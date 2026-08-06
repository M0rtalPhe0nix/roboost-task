from decimal import Decimal

import pytest

from message_triage.budget import (
    BudgetExceeded,
    CostLedger,
    Pricing,
    TokenUsage,
    conservative_token_estimate,
)


def test_pricing_includes_thought_tokens_in_billed_output():
    pricing = Pricing()
    usage = TokenUsage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        candidate_tokens=900_000,
        thought_tokens=100_000,
    )
    assert pricing.cost(usage.input_tokens, usage.output_tokens) == Decimal("2.800000")


def test_pre_request_guard_blocks_worst_case_over_cap(tmp_path):
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing(), Decimal("0.000100"))
    with pytest.raises(BudgetExceeded, match="above"):
        ledger.reserve("small", 1_000, item_count=1)
    assert not (tmp_path / "ledger.jsonl").exists()


def test_outstanding_reservation_remains_committed_after_restart(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = CostLedger(path, Pricing(), Decimal("0.80"))
    reservation = ledger.reserve("hello", 1_000, item_count=2)

    restarted = CostLedger(path, Pricing(), Decimal("0.80"))

    assert restarted.committed_usd() == reservation.reserved_usd
    assert restarted.actual_usd() == Decimal("0")


def test_completion_replaces_reservation_with_measured_usage(tmp_path):
    ledger = CostLedger(tmp_path / "ledger.jsonl", Pricing(), Decimal("0.80"))
    reservation = ledger.reserve("hello", 1_000, item_count=1)

    actual = ledger.complete(reservation, TokenUsage(input_tokens=5, output_tokens=5))

    assert ledger.committed_usd() == actual
    assert ledger.actual_usd() == actual
    assert actual < reservation.reserved_usd


def test_estimator_reserves_half_the_utf8_byte_count():
    text = "hello مرحبا"
    byte_count = len(text.encode("utf-8"))
    assert conservative_token_estimate(text) == (byte_count + 1) // 2


def test_cost_rounds_up_and_rejects_negative_usage():
    pricing = Pricing()
    assert pricing.cost(1, 0) == Decimal("0.000001")
    with pytest.raises(ValueError, match="negative"):
        pricing.cost(-1, 0)
