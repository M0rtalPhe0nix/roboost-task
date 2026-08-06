# Message triage annotation guide

Version: draft v1, for calibration-set review. This guide must be frozen with the classifier before
held-out evaluation.

## Unit and context boundary

Annotate one inbound customer-authored turn. Use preceding turns in the same conversation only when
needed to interpret the current turn. Do not use a later customer turn, brand reply, generated
`ai_reply`, username, or customer name as evidence.

Record one primary intent and one independent urgency flag. Derive the final routing label from
those two fields; do not annotate `urgent escalation` as an intent.

## Primary intent

- `refund request`: the customer's main ask is returning money, reversing a charge, or receiving a
  refund. A request for replacement or generic compensation without asking for money is a complaint.
- `complaint`: dissatisfaction, a defect, wrong/missing item, poor service, or unresolved bad
  experience when refund is not the main ask.
- `order inquiry`: tracking, delivery time, ordering help, availability, menu, allergen information,
  branch, opening time, price, or another factual question about an order or purchase.
- `compliment`: praise, appreciation, or thanks is the main communicative purpose. A short "thanks"
  after resolution is a compliment even if earlier turns contain a complaint.
- `spam`: scam, irrelevant bulk content, or unsolicited commercial solicitation that is not a
  genuine customer-service request. A plausible partnership, franchise, career, or media inquiry is
  not automatically spam; use the closest operational intent and flag it for ontology review.

When multiple intents occur, label the customer's principal requested action. Prefer `refund
request` when an explicit refund ask accompanies a complaint. Use available history to interpret a
short follow-up such as "where is it?" or "yes, refund it."

## Urgency

Set `is_urgent=true` only for at least one of these conditions in the current message, interpreted
with available history:

- Explicit threat or stated action involving police, courts, a lawyer, a regulator, consumer
  protection, or another authority.
- Explicit threat to publish/escalate the incident on social media or to the press.
- Credible safety or health harm that has occurred or is occurring, such as poisoning, an allergic
  reaction, choking, hospitalization, or dangerous contamination.
- Credible exposure or misuse of personal, payment, or account data.

Do not mark urgent solely for anger, profanity, capital letters, the word "urgent," a long delay,
cold food, a churn threat, a demand for a manager, or a general allergen/ingredient question without
harm or imminent unsafe exposure.

## Derived label

If `is_urgent=true`, set `triage_label=urgent escalation`. Otherwise, copy the primary intent into
`triage_label`. This precedence is deterministic.

## Review and disagreement

Annotators should record an intent, urgency flag, and short evidence span. Uncertain items receive a
second review. Resolve disagreements against this guide; if the guide cannot resolve an item, record
the ambiguity and update the guide using calibration examples only. Do not change definitions after
opening the held-out labels.
