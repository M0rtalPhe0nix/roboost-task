from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from .corpus import iter_customer_messages
from .models import Intent, derive_triage_label

EVALUATION_SEED = 20260806
REVIEW_STATUSES = {"reviewed", "adjudicated"}

QUOTAS = {
    "calibration": {
        "urgent escalation": 3,
        "spam": 20,
        "refund request": 24,
        "compliment": 36,
        "complaint": 40,
        "order inquiry": 77,
    },
    "heldout": {
        "urgent escalation": 8,
        "spam": 80,
        "refund request": 96,
        "compliment": 144,
        "complaint": 160,
        "order inquiry": 312,
    },
}

REVIEW_HEADERS = [
    "evaluation_id",
    "split",
    "message_id",
    "conversation_index",
    "seed_id",
    "turn_index",
    "platform",
    "language",
    "available_history",
    "current_message",
    "gold_intent",
    "gold_is_urgent",
    "reviewer_status",
    "reviewer_notes",
]

MANIFEST_HEADERS = [
    "evaluation_id",
    "split",
    "message_id",
    "predicted_intent",
    "predicted_is_urgent",
    "predicted_triage_label",
    "decision_source",
    "confidence_band",
    "sampling_stratum",
    "population_count",
    "sample_count",
    "sampling_weight",
    "configuration_hash",
]


def prepare_evaluation(
    conversations: list[dict[str, Any]],
    classifications_path: Path,
    state_path: Path,
    output_dir: Path,
    *,
    seed: int = EVALUATION_SEED,
) -> dict[str, Any]:
    artifact_paths = [
        output_dir / "calibration-review.csv",
        output_dir / "heldout-review.csv",
        output_dir / "evaluation-manifest.csv",
        output_dir / "evaluation-metadata.json",
    ]
    existing = [str(path) for path in artifact_paths if path.exists()]
    if existing:
        raise ValueError(
            "refusing to overwrite evaluation artifacts; use a new output directory: "
            + ", ".join(existing)
        )
    classifications = _read_jsonl(classifications_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "completed":
        raise ValueError("classification run must be completed before sampling evaluation rows")

    messages = {message.message_id: message for message in iter_customer_messages(conversations)}
    if set(messages) != {row["message_id"] for row in classifications}:
        raise ValueError("classification ids do not match eligible corpus ids")

    enriched = []
    for prediction in classifications:
        message = messages[prediction["message_id"]]
        split = _conversation_split(message.conversation_index, seed)
        enriched.append(
            {
                **prediction,
                "split": split,
                "platform": message.platform,
                "language": _language(message.text),
                "available_history": "\n".join(
                    f"[{turn.author}] {turn.text}" for turn in message.history
                ),
                "current_message": message.text,
            }
        )

    selected, population_counts = _select(enriched, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    review_paths = {}
    for split in ("calibration", "heldout"):
        split_rows = [row for row in selected if row["split"] == split]
        split_rows.sort(key=lambda row: _stable_key(seed, split, row["message_id"]))
        review_rows = []
        prefix = "CAL" if split == "calibration" else "TEST"
        for index, row in enumerate(split_rows, start=1):
            evaluation_id = f"{prefix}-{index:04d}"
            label = row["triage_label"]
            sample_count = QUOTAS[split][label]
            population_count = population_counts[(split, label)]
            review_rows.append(
                {
                    "evaluation_id": evaluation_id,
                    "split": split,
                    "message_id": row["message_id"],
                    "conversation_index": row["conversation_index"],
                    "seed_id": row["seed_id"],
                    "turn_index": row["turn_index"],
                    "platform": row["platform"],
                    "language": row["language"],
                    "available_history": _excel_safe(row["available_history"]),
                    "current_message": _excel_safe(row["current_message"]),
                    "gold_intent": "",
                    "gold_is_urgent": "",
                    "reviewer_status": "",
                    "reviewer_notes": "",
                }
            )
            manifest_rows.append(
                {
                    "evaluation_id": evaluation_id,
                    "split": split,
                    "message_id": row["message_id"],
                    "predicted_intent": row["intent"],
                    "predicted_is_urgent": str(row["is_urgent"]).lower(),
                    "predicted_triage_label": label,
                    "decision_source": row["decision_source"],
                    "confidence_band": row["confidence_band"],
                    "sampling_stratum": label,
                    "population_count": population_count,
                    "sample_count": sample_count,
                    "sampling_weight": f"{population_count / sample_count:.8f}",
                    "configuration_hash": state["configuration_hash"],
                }
            )
        path = output_dir / f"{split}-review.csv"
        _write_csv(path, REVIEW_HEADERS, review_rows)
        review_paths[split] = str(path)

    manifest_path = output_dir / "evaluation-manifest.csv"
    _write_csv(manifest_path, MANIFEST_HEADERS, manifest_rows)
    metadata = {
        "seed": seed,
        "configuration_hash": state["configuration_hash"],
        "selection_basis": "predicted triage label with conversation-disjoint hash split",
        "calibration_rows": sum(row["split"] == "calibration" for row in selected),
        "heldout_rows": sum(row["split"] == "heldout" for row in selected),
        "total_rows": len(selected),
        "quotas": QUOTAS,
        "review_files": review_paths,
        "manifest_file": str(manifest_path),
    }
    metadata_path = output_dir / "evaluation-metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def score_evaluation(
    review_path: Path,
    manifest_path: Path,
    output_path: Path,
    *,
    split: str,
) -> dict[str, Any]:
    if split not in QUOTAS:
        raise ValueError(f"unknown evaluation split: {split}")
    reviews = _read_csv(review_path)
    manifest_rows = [row for row in _read_csv(manifest_path) if row["split"] == split]
    review_ids = [row["evaluation_id"] for row in reviews]
    manifest_ids = [row["evaluation_id"] for row in manifest_rows]
    if len(set(review_ids)) != len(review_ids):
        raise ValueError("review file contains duplicate evaluation ids")
    if len(set(manifest_ids)) != len(manifest_ids):
        raise ValueError("manifest contains duplicate evaluation ids")
    manifest = {row["evaluation_id"]: row for row in manifest_rows}
    expected_rows = sum(QUOTAS[split].values())
    if len(reviews) != expected_rows or len(manifest) != expected_rows:
        raise ValueError(
            f"{split} requires {expected_rows} review and manifest rows; "
            f"found {len(reviews)} and {len(manifest)}"
        )
    if set(review_ids) != set(manifest_ids):
        raise ValueError("review and manifest evaluation ids do not match")
    if any(row.get("split", split) != split for row in reviews):
        raise ValueError(f"review file contains rows outside the {split} split")
    actual_strata = Counter(row["sampling_stratum"] for row in manifest_rows)
    if actual_strata != Counter(QUOTAS[split]):
        raise ValueError(f"manifest sampling strata do not match the frozen {split} quotas")

    incomplete = []
    scored = []
    for review in reviews:
        evaluation_id = review["evaluation_id"]
        prediction = manifest.get(evaluation_id)
        if prediction is None or prediction["message_id"] != review["message_id"]:
            raise ValueError(f"review/manifest mismatch for {evaluation_id}")
        try:
            gold_intent = Intent(review["gold_intent"].strip())
            gold_urgent = _parse_bool(review["gold_is_urgent"])
        except ValueError:
            incomplete.append(evaluation_id)
            continue
        if review["reviewer_status"].strip().lower() not in REVIEW_STATUSES:
            incomplete.append(evaluation_id)
            continue
        predicted_urgent = _parse_bool(prediction["predicted_is_urgent"])
        scored.append(
            {
                **review,
                **prediction,
                "gold_intent": gold_intent.value,
                "gold_is_urgent": gold_urgent,
                "gold_triage_label": derive_triage_label(gold_intent, gold_urgent).value,
                "predicted_is_urgent": predicted_urgent,
                "sampling_weight": float(prediction["sampling_weight"]),
            }
        )
    if incomplete:
        raise ValueError(
            f"{len(incomplete)} rows are missing valid gold labels/reviewer status; "
            f"first ids: {incomplete[:10]}"
        )

    triage_labels = [
        "refund request",
        "complaint",
        "order inquiry",
        "compliment",
        "spam",
        "urgent escalation",
    ]
    intent_labels = [intent.value for intent in Intent]
    triage = _classification_metrics(
        scored, "gold_triage_label", "predicted_triage_label", triage_labels
    )
    intent = _classification_metrics(scored, "gold_intent", "predicted_intent", intent_labels)
    urgent = _binary_metrics(scored, "gold_is_urgent", "predicted_is_urgent")
    weighted_triage = _classification_metrics(
        scored,
        "gold_triage_label",
        "predicted_triage_label",
        triage_labels,
        weight_key="sampling_weight",
    )
    weighted_intent = _classification_metrics(
        scored,
        "gold_intent",
        "predicted_intent",
        intent_labels,
        weight_key="sampling_weight",
    )
    weighted_urgent = _binary_metrics(
        scored,
        "gold_is_urgent",
        "predicted_is_urgent",
        weight_key="sampling_weight",
    )
    report = {
        "split": split,
        "rows": len(scored),
        "configuration_hash": next(iter(manifest.values()))["configuration_hash"],
        "triage": triage,
        "triage_population_weighted": weighted_triage,
        "intent": intent,
        "intent_population_weighted": weighted_intent,
        "urgency": urgent,
        "urgency_population_weighted": weighted_urgent,
        "weighted_triage_accuracy": weighted_triage["accuracy"],
        "errors": sum(
            row["gold_triage_label"] != row["predicted_triage_label"] for row in scored
        ),
    }
    error_path = output_path.with_name(f"{output_path.stem}-errors.csv")
    error_rows = [
        {
            "evaluation_id": row["evaluation_id"],
            "message_id": row["message_id"],
            "gold_intent": row["gold_intent"],
            "predicted_intent": row["predicted_intent"],
            "gold_is_urgent": str(row["gold_is_urgent"]).lower(),
            "predicted_is_urgent": str(row["predicted_is_urgent"]).lower(),
            "gold_triage_label": row["gold_triage_label"],
            "predicted_triage_label": row["predicted_triage_label"],
            "reviewer_notes": row["reviewer_notes"],
        }
        for row in scored
        if row["gold_triage_label"] != row["predicted_triage_label"]
    ]
    _write_csv(
        error_path,
        [
            "evaluation_id",
            "message_id",
            "gold_intent",
            "predicted_intent",
            "gold_is_urgent",
            "predicted_is_urgent",
            "gold_triage_label",
            "predicted_triage_label",
            "reviewer_notes",
        ],
        error_rows,
    )
    report["error_file"] = str(error_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _select(
    rows: list[dict[str, Any]], seed: int
) -> tuple[list[dict[str, Any]], Counter[tuple[str, str]]]:
    population_counts = Counter((row["split"], row["triage_label"]) for row in rows)
    selected = []
    for split, label_quotas in QUOTAS.items():
        for label, quota in label_quotas.items():
            candidates = [
                row for row in rows if row["split"] == split and row["triage_label"] == label
            ]
            candidates.sort(key=lambda row: _stable_key(seed, split, label, row["message_id"]))
            if len(candidates) < quota:
                raise ValueError(
                    f"insufficient {split}/{label} candidates: "
                    f"need {quota}, found {len(candidates)}"
                )
            selected.extend(candidates[:quota])
    if len({row["message_id"] for row in selected}) != 1_000:
        raise ValueError("evaluation sample must contain 1,000 unique message ids")
    calibration_conversations = {
        row["conversation_index"] for row in selected if row["split"] == "calibration"
    }
    heldout_conversations = {
        row["conversation_index"] for row in selected if row["split"] == "heldout"
    }
    if calibration_conversations & heldout_conversations:
        raise ValueError("conversation leakage detected across evaluation splits")
    return selected, population_counts


def _conversation_split(conversation_index: int, seed: int) -> str:
    if conversation_index == 150:
        return "calibration"
    if conversation_index in {94, 102, 151, 152, 555}:
        return "heldout"
    value = int(hashlib.sha256(f"{seed}:{conversation_index}".encode()).hexdigest()[:8], 16)
    return "calibration" if value % 100 < 20 else "heldout"


def _stable_key(*parts: Any) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def _language(text: str) -> str:
    arabic = len(re.findall(r"[\u0600-\u06FF]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if arabic and latin:
        return "mixed"
    if arabic:
        return "arabic"
    if latin:
        return "english"
    return "other"


def _classification_metrics(
    rows: Sequence[dict[str, Any]],
    gold_key: str,
    predicted_key: str,
    labels: Sequence[str],
    *,
    weight_key: str | None = None,
) -> dict[str, Any]:
    def count(predicate: Any) -> float:
        return sum(
            (float(row[weight_key]) if weight_key else 1.0)
            for row in rows
            if predicate(row)
        )

    per_label = {}
    for label in labels:
        true_positive = count(
            lambda row, label=label: row[gold_key] == label and row[predicted_key] == label
        )
        false_positive = count(
            lambda row, label=label: row[gold_key] != label and row[predicted_key] == label
        )
        false_negative = count(
            lambda row, label=label: row[gold_key] == label and row[predicted_key] != label
        )
        precision = _safe_div(true_positive, true_positive + false_positive)
        recall = _safe_div(true_positive, true_positive + false_negative)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": _safe_div(2 * precision * recall, precision + recall),
            "support": count(lambda row, label=label: row[gold_key] == label),
        }
    total_weight = count(lambda row: True)
    return {
        "accuracy": _safe_div(
            count(lambda row: row[gold_key] == row[predicted_key]), total_weight
        ),
        "macro_f1": _safe_div(sum(item["f1"] for item in per_label.values()), len(labels)),
        "per_label": per_label,
        "confusion_matrix": {
            gold: {
                predicted: count(
                    lambda row, gold=gold, predicted=predicted: row[gold_key] == gold
                    and row[predicted_key] == predicted
                )
                for predicted in labels
            }
            for gold in labels
        },
    }


def _binary_metrics(
    rows: Sequence[dict[str, Any]],
    gold_key: str,
    predicted_key: str,
    *,
    weight_key: str | None = None,
) -> dict[str, Any]:
    def count(predicate: Any) -> float:
        return sum(
            (float(row[weight_key]) if weight_key else 1.0)
            for row in rows
            if predicate(row)
        )

    true_positive = count(lambda row: row[gold_key] is True and row[predicted_key] is True)
    false_positive = count(lambda row: row[gold_key] is False and row[predicted_key] is True)
    false_negative = count(lambda row: row[gold_key] is True and row[predicted_key] is False)
    precision = _safe_div(true_positive, true_positive + false_positive)
    recall = _safe_div(true_positive, true_positive + false_negative)
    return {
        "precision": precision,
        "recall": recall,
        "f1": _safe_div(2 * precision * recall, precision + recall),
        "support": count(lambda row: row[gold_key] is True),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"expected true or false, got {value!r}")


def _excel_safe(value: str) -> str:
    if value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, headers: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
