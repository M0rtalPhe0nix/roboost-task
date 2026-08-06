import json

import pytest

from message_triage.budget import CostLedger, Pricing, TokenUsage
from message_triage.models import CustomerMessage, Intent, ModelDecision, TriageLabel
from message_triage.pipeline import classify_messages
from message_triage.provider import ProviderResponse, ProviderResponseError


def message(index: int, text: str) -> CustomerMessage:
    return CustomerMessage(
        conversation_index=index,
        seed_id=index,
        turn_index=0,
        platform="instagram",
        text=text,
        gap_minutes=0,
        history=(),
    )


class FakeProvider:
    def __init__(self, urgent: bool = False, duplicate: bool = False) -> None:
        self.urgent = urgent
        self.duplicate = duplicate
        self.prompts = []

    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse:
        self.prompts.append(prompt)
        records = json.loads(prompt.split("MESSAGES_JSON:\n", 1)[1])
        decisions = [
            ModelDecision(record["id"], Intent.ORDER_INQUIRY, self.urgent) for record in records
        ]
        if self.duplicate:
            decisions[-1] = decisions[0]
        return ProviderResponse(
            tuple(decisions),
            TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            response_id="fake-response",
            model_version="fake-model-v1",
        )


class TruncatedProvider:
    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse:
        raise ProviderResponseError(
            "truncated",
            TokenUsage(input_tokens=100, output_tokens=max_output_tokens),
            response_id="truncated-response",
            model_version="fake-model-v1",
        )


class SplitThenSucceedProvider(FakeProvider):
    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse:
        records = json.loads(prompt.split("MESSAGES_JSON:\n", 1)[1])
        self.prompts.append(prompt)
        if len(records) > 25:
            raise ProviderResponseError(
                "truncated",
                TokenUsage(input_tokens=100, output_tokens=max_output_tokens),
                retryable=True,
            )
        decisions = tuple(
            ModelDecision(record["id"], Intent.ORDER_INQUIRY, False) for record in records
        )
        return ProviderResponse(
            decisions,
            TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        )


class PartialThenSucceedProvider(FakeProvider):
    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse:
        records = json.loads(prompt.split("MESSAGES_JSON:\n", 1)[1])
        self.prompts.append(prompt)
        returned = records[5:] if len(records) == 50 else records
        decisions = tuple(
            ModelDecision(record["id"], Intent.ORDER_INQUIRY, False) for record in returned
        )
        return ProviderResponse(
            decisions,
            TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        )


class UnknownThenSucceedProvider(FakeProvider):
    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse:
        records = json.loads(prompt.split("MESSAGES_JSON:\n", 1)[1])
        self.prompts.append(prompt)
        returned = records[1:] if len(records) > 1 else records
        decisions = [
            ModelDecision(record["id"], Intent.ORDER_INQUIRY, False) for record in returned
        ]
        if len(records) > 1:
            decisions.append(ModelDecision("not-in-this-batch", Intent.SPAM, False))
        return ProviderResponse(
            tuple(decisions),
            TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        )


def test_pipeline_combines_rule_gate_and_model_fallback_in_source_order(tmp_path):
    messages = [
        message(0, "We sell SEO services and guaranteed followers"),
        message(1, "Where is my order?"),
    ]
    provider = FakeProvider()
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())

    results = classify_messages(messages, provider, ledger, batch_size=10)

    assert [result.message_id for result in results] == [item.message_id for item in messages]
    assert results[0].intent is Intent.SPAM
    assert results[0].decision_source == "rule_gate"
    assert results[1].intent is Intent.ORDER_INQUIRY
    assert results[1].decision_source == "model_fallback"
    assert ledger.actual_usd() > 0


def test_model_urgency_derives_urgent_escalation_label(tmp_path):
    provider = FakeProvider(urgent=True)
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())

    result = classify_messages([message(0, "ambiguous")], provider, ledger)[0]

    assert result.intent is Intent.ORDER_INQUIRY
    assert result.is_urgent is True
    assert result.triage_label is TriageLabel.URGENT_ESCALATION


def test_duplicate_provider_ids_are_discarded_and_retried(tmp_path):
    provider = FakeProvider(duplicate=True)
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())

    results = classify_messages(
        [message(0, "first"), message(1, "second")], provider, ledger, batch_size=10
    )

    assert len(results) == 2
    assert len(provider.prompts) == 3
    assert ledger.actual_usd() > 0
    assert ledger.committed_usd() > 0
    assert any(event["event"] == "response_anomaly" for event in ledger.events())


def test_checkpoint_resume_does_not_repeat_paid_requests(tmp_path):
    items = [message(0, "first"), message(1, "second")]
    checkpoint = tmp_path / "classifications.jsonl"
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())
    first_provider = FakeProvider()
    first_results = classify_messages(
        items, first_provider, ledger, batch_size=1, checkpoint_path=checkpoint
    )
    first_cost = ledger.actual_usd()

    resumed_provider = FakeProvider()
    resumed_results = classify_messages(
        items, resumed_provider, ledger, batch_size=1, checkpoint_path=checkpoint
    )

    assert resumed_results == first_results
    assert resumed_provider.prompts == []
    assert ledger.actual_usd() == first_cost


def test_truncated_response_usage_is_recorded_before_failure(tmp_path):
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())

    with pytest.raises(RuntimeError, match="truncated"):
        classify_messages(
            [message(0, "ambiguous")],
            TruncatedProvider(),
            ledger,
            max_output_tokens=100,
        )

    assert ledger.actual_usd() > 0
    assert [event["event"] for event in ledger.events()] == ["reserved", "completed"]


def test_max_tokens_batch_is_charged_split_and_retried(tmp_path):
    items = [message(index, f"message {index}") for index in range(50)]
    provider = SplitThenSucceedProvider()
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())

    results = classify_messages(items, provider, ledger, batch_size=50)

    assert len(results) == 50
    assert len(provider.prompts) == 3
    assert [event["event"] for event in ledger.events()] == [
        "reserved",
        "completed",
        "reserved",
        "completed",
        "reserved",
        "completed",
    ]


def test_partial_response_checkpoints_valid_items_and_retries_only_missing(tmp_path):
    items = [message(index, f"message {index}") for index in range(50)]
    provider = PartialThenSucceedProvider()
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())
    checkpoint = tmp_path / "checkpoint.jsonl"

    results = classify_messages(
        items, provider, ledger, batch_size=50, checkpoint_path=checkpoint
    )

    assert len(results) == 50
    assert len(provider.prompts) == 2
    first_records = json.loads(provider.prompts[0].split("MESSAGES_JSON:\n", 1)[1])
    retry_records = json.loads(provider.prompts[1].split("MESSAGES_JSON:\n", 1)[1])
    assert len(first_records) == 50
    assert [record["id"] for record in retry_records] == [item.message_id for item in items[:5]]
    assert sum(1 for _ in checkpoint.open(encoding="utf-8")) == 50


def test_unknown_ids_are_discarded_and_only_missing_requested_ids_are_retried(tmp_path):
    items = [message(index, f"message {index}") for index in range(5)]
    provider = UnknownThenSucceedProvider()
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing())

    results = classify_messages(items, provider, ledger, batch_size=5)

    assert len(results) == 5
    assert len(provider.prompts) == 2
    assert all(result.message_id != "not-in-this-batch" for result in results)
    anomalies = [event for event in ledger.events() if event["event"] == "response_anomaly"]
    assert {event["anomaly"] for event in anomalies} == {
        "unknown_ids_discarded",
        "missing_ids_retried",
    }
