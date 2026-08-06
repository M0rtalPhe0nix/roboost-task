from message_triage.models import Intent, TriageLabel, derive_triage_label
from message_triage.rules import rule_gate


def test_urgent_label_overrides_primary_intent():
    assert derive_triage_label(Intent.REFUND_REQUEST, True) is TriageLabel.URGENT_ESCALATION


def test_ordinary_anger_is_not_urgent():
    assert rule_gate("This is terrible and I will never order from you again!") is None


def test_allergen_question_is_not_urgent_without_harm():
    assert rule_gate("بنتي عندها حساسية من اللبن، هل عندكم خيارات خالية من الألبان؟") is None


def test_hospital_visit_is_urgent_complaint():
    decision = rule_gate("روحنا المستشفى بسبب الطلب امبارح")
    assert decision is not None
    assert decision.intent is Intent.COMPLAINT
    assert decision.is_urgent is True


def test_explicit_legal_refund_threat_preserves_intent():
    decision = rule_gate("Refund me today or I will take legal action")
    assert decision is not None
    assert decision.intent is Intent.REFUND_REQUEST
    assert decision.is_urgent is True


def test_high_precision_solicitation_is_spam():
    decision = rule_gate("We sell SEO services and guaranteed followers for your account")
    assert decision is not None
    assert decision.intent is Intent.SPAM
    assert decision.is_urgent is False
