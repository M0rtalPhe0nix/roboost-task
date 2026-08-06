from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Intent(StrEnum):
    REFUND_REQUEST = "refund request"
    COMPLAINT = "complaint"
    ORDER_INQUIRY = "order inquiry"
    COMPLIMENT = "compliment"
    SPAM = "spam"


class TriageLabel(StrEnum):
    REFUND_REQUEST = "refund request"
    COMPLAINT = "complaint"
    ORDER_INQUIRY = "order inquiry"
    COMPLIMENT = "compliment"
    SPAM = "spam"
    URGENT_ESCALATION = "urgent escalation"


class DecisionSource(StrEnum):
    RULE_GATE = "rule_gate"
    MODEL_FALLBACK = "model_fallback"


class ConfidenceBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ConversationTurn:
    turn_index: int
    author: str
    text: str
    gap_minutes: int


@dataclass(frozen=True)
class CustomerMessage:
    conversation_index: int
    seed_id: int
    turn_index: int
    platform: str
    text: str
    gap_minutes: int
    history: tuple[ConversationTurn, ...]

    @property
    def message_id(self) -> str:
        return f"c{self.conversation_index}:s{self.seed_id}:t{self.turn_index}"


@dataclass(frozen=True)
class ModelDecision:
    message_id: str
    intent: Intent
    is_urgent: bool


@dataclass(frozen=True)
class Classification:
    message_id: str
    conversation_index: int
    seed_id: int
    turn_index: int
    intent: Intent
    is_urgent: bool
    triage_label: TriageLabel
    decision_source: DecisionSource
    confidence_band: ConfidenceBand

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "conversation_index": self.conversation_index,
            "seed_id": self.seed_id,
            "turn_index": self.turn_index,
            "intent": self.intent.value,
            "is_urgent": self.is_urgent,
            "triage_label": self.triage_label.value,
            "decision_source": self.decision_source.value,
            "confidence_band": self.confidence_band.value,
        }


def derive_triage_label(intent: Intent, is_urgent: bool) -> TriageLabel:
    if is_urgent:
        return TriageLabel.URGENT_ESCALATION
    return TriageLabel(intent.value)
