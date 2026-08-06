from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_UP, Decimal
from pathlib import Path
from typing import Any

MICRO_USD = Decimal("0.000001")


class BudgetExceeded(RuntimeError):
    """A request cannot safely fit beneath the configured spend cap."""


@dataclass(frozen=True)
class Pricing:
    model: str = "gemini-3.5-flash-lite"
    input_usd_per_million: Decimal = Decimal("0.30")
    output_usd_per_million: Decimal = Decimal("2.50")

    def cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts cannot be negative")
        value = (
            Decimal(input_tokens) * self.input_usd_per_million
            + Decimal(output_tokens) * self.output_usd_per_million
        ) / Decimal(1_000_000)
        return value.quantize(MICRO_USD, rounding=ROUND_UP)


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    candidate_tokens: int = 0
    thought_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class Reservation:
    request_id: str
    reserved_usd: Decimal
    estimated_input_tokens: int
    max_output_tokens: int


def conservative_token_estimate(text: str) -> int:
    """Over-estimate mixed Arabic/English prompt tokens without another API request."""
    # Gemini documents about four characters per token. UTF-8 bytes / 2 deliberately
    # reserves more for Arabic and code-switched text without making another API call.
    byte_count = len(text.encode("utf-8"))
    return max(1, (byte_count + 1) // 2)


class CostLedger:
    """Append-only JSONL ledger with crash-safe outstanding reservations."""

    def __init__(self, path: Path, pricing: Pricing, cap_usd: Decimal = Decimal("0.80")) -> None:
        if cap_usd <= 0 or cap_usd > Decimal("1.00"):
            raise ValueError("cap_usd must be greater than zero and no more than USD 1.00")
        self.path = path
        self.pricing = pricing
        self.cap_usd = cap_usd

    def reserve(self, prompt: str, max_output_tokens: int, *, item_count: int) -> Reservation:
        estimated_input = conservative_token_estimate(prompt)
        reserved = self.pricing.cost(estimated_input, max_output_tokens)
        committed = self.committed_usd()
        if committed + reserved > self.cap_usd:
            raise BudgetExceeded(
                f"request would raise committed spend to USD {committed + reserved:.6f}, "
                f"above the USD {self.cap_usd:.2f} cap"
            )
        reservation = Reservation(str(uuid.uuid4()), reserved, estimated_input, max_output_tokens)
        self._append(
            {
                "event": "reserved",
                "request_id": reservation.request_id,
                "timestamp": _now(),
                "model": self.pricing.model,
                "item_count": item_count,
                "estimated_input_tokens": estimated_input,
                "max_output_tokens": max_output_tokens,
                "reserved_usd": _money(reserved),
            }
        )
        return reservation

    def complete(
        self,
        reservation: Reservation,
        usage: TokenUsage,
        *,
        response_id: str | None = None,
        model_version: str | None = None,
    ) -> Decimal:
        actual = self.pricing.cost(usage.input_tokens, usage.output_tokens)
        if actual > reservation.reserved_usd:
            raise BudgetExceeded(
                "provider usage exceeded the request reservation; "
                "ledger left conservatively reserved"
            )
        self._append(
            {
                "event": "completed",
                "request_id": reservation.request_id,
                "timestamp": _now(),
                "model": self.pricing.model,
                "model_version": model_version,
                "response_id": response_id,
                "usage": asdict(usage),
                "actual_usd": _money(actual),
            }
        )
        return actual

    def committed_usd(self) -> Decimal:
        reservations: dict[str, Decimal] = {}
        completions: dict[str, Decimal] = {}
        for event in self.events():
            request_id = event.get("request_id")
            if event.get("event") == "reserved":
                reservations[request_id] = Decimal(event["reserved_usd"])
            elif event.get("event") == "completed":
                completions[request_id] = Decimal(event["actual_usd"])
        return sum(
            (completions.get(key, reserved) for key, reserved in reservations.items()), Decimal("0")
        )

    def actual_usd(self) -> Decimal:
        return sum(
            (
                Decimal(event["actual_usd"])
                for event in self.events()
                if event.get("event") == "completed"
            ),
            Decimal("0"),
        )

    def record_anomaly(
        self,
        request_id: str,
        *,
        anomaly: str,
        expected_count: int,
        returned_count: int,
        affected_ids: list[str],
    ) -> None:
        self._append(
            {
                "event": "response_anomaly",
                "request_id": request_id,
                "timestamp": _now(),
                "anomaly": anomaly,
                "expected_count": expected_count,
                "returned_count": returned_count,
                "affected_ids": affected_ids,
            }
        )

    def events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events = []
        with self.path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f"invalid cost ledger JSON on line {line_number}"
                        ) from exc
        return events

    def _append(self, event: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _money(value: Decimal) -> str:
    return f"{value:.6f}"
