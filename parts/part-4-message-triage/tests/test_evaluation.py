import csv
import json

import pytest

from message_triage import evaluation


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evaluation_rows():
    reviews = [
        {
            "evaluation_id": "CAL-0001",
            "message_id": "c1:s1:t0",
            "gold_intent": "complaint",
            "gold_is_urgent": "false",
            "reviewer_status": "reviewed",
            "reviewer_notes": "",
        },
        {
            "evaluation_id": "CAL-0002",
            "message_id": "c2:s2:t0",
            "gold_intent": "complaint",
            "gold_is_urgent": "true",
            "reviewer_status": "adjudicated",
            "reviewer_notes": "legal escalation",
        },
    ]
    manifest = [
        {
            "evaluation_id": "CAL-0001",
            "split": "calibration",
            "message_id": "c1:s1:t0",
            "predicted_intent": "complaint",
            "predicted_is_urgent": "false",
            "predicted_triage_label": "complaint",
            "sampling_stratum": "complaint",
            "sampling_weight": "5",
            "configuration_hash": "frozen-config",
        },
        {
            "evaluation_id": "CAL-0002",
            "split": "calibration",
            "message_id": "c2:s2:t0",
            "predicted_intent": "order inquiry",
            "predicted_is_urgent": "false",
            "predicted_triage_label": "order inquiry",
            "sampling_stratum": "urgent escalation",
            "sampling_weight": "2",
            "configuration_hash": "frozen-config",
        },
    ]
    return reviews, manifest


def test_score_reports_routing_and_urgency_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(
        evaluation,
        "QUOTAS",
        {"calibration": {"complaint": 1, "urgent escalation": 1}},
    )
    reviews, manifest = evaluation_rows()
    review_path = tmp_path / "review.csv"
    manifest_path = tmp_path / "manifest.csv"
    output_path = tmp_path / "report.json"
    write_csv(review_path, reviews)
    write_csv(manifest_path, manifest)

    report = evaluation.score_evaluation(
        review_path, manifest_path, output_path, split="calibration"
    )

    assert report["triage"]["accuracy"] == 0.5
    assert report["intent"]["accuracy"] == 0.5
    assert report["urgency"]["support"] == 1
    assert report["urgency"]["recall"] == 0.0
    assert report["weighted_triage_accuracy"] == pytest.approx(5 / 7)
    assert report["triage_population_weighted"]["accuracy"] == pytest.approx(5 / 7)
    assert report["intent_population_weighted"]["accuracy"] == pytest.approx(5 / 7)
    assert report["errors"] == 1
    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted["error_file"].endswith("report-errors.csv")


def test_score_rejects_unreviewed_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(
        evaluation,
        "QUOTAS",
        {"calibration": {"complaint": 1, "urgent escalation": 1}},
    )
    reviews, manifest = evaluation_rows()
    reviews[1]["reviewer_status"] = ""
    review_path = tmp_path / "review.csv"
    manifest_path = tmp_path / "manifest.csv"
    write_csv(review_path, reviews)
    write_csv(manifest_path, manifest)

    with pytest.raises(ValueError, match="1 rows are missing valid gold labels"):
        evaluation.score_evaluation(
            review_path,
            manifest_path,
            tmp_path / "report.json",
            split="calibration",
        )


def test_conversation_split_keeps_forced_urgent_groups_separate():
    assert evaluation._conversation_split(150, evaluation.EVALUATION_SEED) == "calibration"
    assert {
        evaluation._conversation_split(index, evaluation.EVALUATION_SEED)
        for index in (94, 102, 151, 152, 555)
    } == {"heldout"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [("=SUM(A1:A2)", "'=SUM(A1:A2)"), ("ordinary message", "ordinary message")],
)
def test_review_text_is_safe_for_spreadsheets(value, expected):
    assert evaluation._excel_safe(value) == expected


def test_csv_round_trip_strips_excel_compatible_bom(tmp_path):
    path = tmp_path / "review.csv"
    evaluation._write_csv(path, ["evaluation_id"], [{"evaluation_id": "CAL-0001"}])

    assert evaluation._read_csv(path) == [{"evaluation_id": "CAL-0001"}]


def test_prepare_refuses_to_overwrite_review_work(tmp_path):
    output_dir = tmp_path / "evaluation"
    output_dir.mkdir()
    (output_dir / "calibration-review.csv").write_text("human work", encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite evaluation artifacts"):
        evaluation.prepare_evaluation(
            [],
            tmp_path / "classifications.jsonl",
            tmp_path / "state.json",
            output_dir,
        )
