from __future__ import annotations

import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path

from .budget import CostLedger
from .models import (
    Classification,
    ConfidenceBand,
    CustomerMessage,
    DecisionSource,
    Intent,
    ModelDecision,
    TriageLabel,
    derive_triage_label,
)
from .prompt import build_prompt
from .provider import ProviderResponseError, TriageProvider
from .rules import rule_gate


def classify_messages(
    messages: Sequence[CustomerMessage],
    provider: TriageProvider,
    ledger: CostLedger,
    *,
    batch_size: int = 50,
    max_output_tokens: int = 2048,
    checkpoint_path: Path | None = None,
) -> list[Classification]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if max_output_tokens < 1:
        raise ValueError("max_output_tokens must be positive")

    results = _load_checkpoint(checkpoint_path) if checkpoint_path else {}
    message_by_id = {message.message_id: message for message in messages}
    _validate_checkpoint(results, message_by_id)
    fallback: list[CustomerMessage] = []
    for message in messages:
        if message.message_id in results:
            continue
        decision = rule_gate(message.text)
        if decision is None:
            fallback.append(message)
            continue
        classification = _classification(
            message,
            ModelDecision(message.message_id, decision.intent, decision.is_urgent),
            DecisionSource.RULE_GATE,
            ConfidenceBand.HIGH,
        )
        results[message.message_id] = classification
        if checkpoint_path:
            _append_checkpoint(checkpoint_path, [classification])

    pending_batches = list(_batches(fallback, batch_size))
    while pending_batches:
        batch = pending_batches.pop(0)
        prompt = build_prompt(batch)
        reservation = ledger.reserve(prompt, max_output_tokens, item_count=len(batch))
        try:
            response = provider.classify(prompt, max_output_tokens=max_output_tokens)
        except ProviderResponseError as exc:
            ledger.complete(
                reservation,
                exc.usage,
                response_id=exc.response_id,
                model_version=exc.model_version,
            )
            if exc.retryable and len(batch) > 1:
                midpoint = len(batch) // 2
                pending_batches[0:0] = [batch[:midpoint], batch[midpoint:]]
                continue
            raise RuntimeError(str(exc)) from exc
        ledger.complete(
            reservation,
            response.usage,
            response_id=response.response_id,
            model_version=response.model_version,
        )
        by_id, missing_messages, anomalies = _validate_batch(batch, response.decisions)
        for anomaly, affected_ids in anomalies.items():
            ledger.record_anomaly(
                reservation.request_id,
                anomaly=anomaly,
                expected_count=len(batch),
                returned_count=len(response.decisions),
                affected_ids=affected_ids,
            )
        completed_batch = []
        for message in batch:
            if message.message_id not in by_id:
                continue
            classification = _classification(
                message,
                by_id[message.message_id],
                DecisionSource.MODEL_FALLBACK,
                ConfidenceBand.MEDIUM,
            )
            results[message.message_id] = classification
            completed_batch.append(classification)
        if checkpoint_path:
            _append_checkpoint(checkpoint_path, completed_batch)
        if missing_messages:
            if len(missing_messages) == len(batch):
                if len(batch) == 1:
                    raise RuntimeError(
                        f"provider omitted the only requested id: {batch[0].message_id}"
                    )
                midpoint = len(batch) // 2
                pending_batches[0:0] = [batch[:midpoint], batch[midpoint:]]
            else:
                pending_batches.insert(0, missing_messages)

    if len(results) != len(messages):
        raise RuntimeError("classification output count does not match input count")
    return [results[message.message_id] for message in messages]


def write_jsonl(classifications: Iterable[Classification], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for classification in classifications:
            stream.write(
                json.dumps(classification.as_dict(), ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
        stream.flush()
        os.fsync(stream.fileno())


def _classification(
    message: CustomerMessage,
    decision: ModelDecision,
    source: DecisionSource,
    confidence: ConfidenceBand,
) -> Classification:
    return Classification(
        message_id=message.message_id,
        conversation_index=message.conversation_index,
        seed_id=message.seed_id,
        turn_index=message.turn_index,
        intent=decision.intent,
        is_urgent=decision.is_urgent,
        triage_label=derive_triage_label(decision.intent, decision.is_urgent),
        decision_source=source,
        confidence_band=confidence,
    )


def _validate_batch(
    messages: Sequence[CustomerMessage], decisions: Sequence[ModelDecision]
) -> tuple[dict[str, ModelDecision], list[CustomerMessage], dict[str, list[str]]]:
    expected = {message.message_id for message in messages}
    by_id: dict[str, ModelDecision] = {}
    duplicate_ids: set[str] = set()
    unknown_ids: set[str] = set()
    for decision in decisions:
        if decision.message_id not in expected:
            unknown_ids.add(decision.message_id)
            continue
        if decision.message_id in by_id:
            duplicate_ids.add(decision.message_id)
            by_id.pop(decision.message_id, None)
            continue
        if decision.message_id not in duplicate_ids:
            by_id[decision.message_id] = decision
    missing_messages = [message for message in messages if message.message_id not in by_id]
    anomalies = {}
    if unknown_ids:
        anomalies["unknown_ids_discarded"] = sorted(unknown_ids)
    if duplicate_ids:
        anomalies["duplicate_ids_retried"] = sorted(duplicate_ids)
    if missing_messages:
        anomalies["missing_ids_retried"] = [message.message_id for message in missing_messages]
    return by_id, missing_messages, anomalies


def _batches(items: Sequence[CustomerMessage], size: int) -> Iterable[Sequence[CustomerMessage]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _load_checkpoint(path: Path) -> dict[str, Classification]:
    if not path.exists():
        return {}
    results = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                if set(item) != {
                    "message_id",
                    "conversation_index",
                    "seed_id",
                    "turn_index",
                    "intent",
                    "is_urgent",
                    "triage_label",
                    "decision_source",
                    "confidence_band",
                }:
                    raise ValueError("checkpoint row has an invalid shape")
                if not isinstance(item["is_urgent"], bool):
                    raise TypeError("checkpoint is_urgent must be boolean")
                classification = Classification(
                    message_id=item["message_id"],
                    conversation_index=item["conversation_index"],
                    seed_id=item["seed_id"],
                    turn_index=item["turn_index"],
                    intent=Intent(item["intent"]),
                    is_urgent=item["is_urgent"],
                    triage_label=TriageLabel(item["triage_label"]),
                    decision_source=DecisionSource(item["decision_source"]),
                    confidence_band=ConfidenceBand(item["confidence_band"]),
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid checkpoint row on line {line_number}") from exc
            if classification.message_id in results:
                raise ValueError(f"duplicate checkpoint id {classification.message_id}")
            results[classification.message_id] = classification
    return results


def _validate_checkpoint(
    results: dict[str, Classification], messages: dict[str, CustomerMessage]
) -> None:
    unknown = sorted(set(results) - set(messages))
    if unknown:
        raise ValueError(f"checkpoint contains unknown message ids: {unknown[:5]}")
    for message_id, result in results.items():
        source = messages[message_id]
        if (
            result.conversation_index,
            result.seed_id,
            result.turn_index,
        ) != (source.conversation_index, source.seed_id, source.turn_index):
            raise ValueError(f"checkpoint source metadata mismatch for {message_id}")
        if result.triage_label is not derive_triage_label(result.intent, result.is_urgent):
            raise ValueError(f"checkpoint derived label mismatch for {message_id}")


def _append_checkpoint(path: Path, classifications: Sequence[Classification]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        for classification in classifications:
            stream.write(
                json.dumps(classification.as_dict(), ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
        stream.flush()
        os.fsync(stream.fileno())
