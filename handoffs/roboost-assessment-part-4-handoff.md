# Handoff: Part 4 - High-Volume Message Triage

## Submission status

Complete within the selected submission boundary. The Option C pipeline classified every eligible
customer-authored turn, preserved the required output fields, and recorded provider usage below the
USD 1 task limit. No human quality evaluation is planned or claimed.

## Canonical artifacts

- [Part README and runnable commands](../parts/part-4-message-triage/README.md)
- [Final classifications](../parts/part-4-message-triage/outputs/classifications.jsonl)
- [Approach document](../parts/part-4-message-triage/docs/approach.md)
- [Cost ledger](../parts/part-4-message-triage/outputs/cost-ledger.jsonl)
- [Evaluation decision record](../parts/part-4-message-triage/docs/evaluation.md)

## Final run evidence

- Source corpus: 2,204 conversations and 10,000 total turns.
- Eligible triage set: 5,551 customer-authored turns; 4,449 brand turns are context only.
- Decision flow: narrow high-precision rule gate, then batched structured output from
  `gemini-3.5-flash-lite` for unresolved messages.
- Configuration hash: `aacd6cb395fc4762708497418f6bd7adfd177b67d75ea5a36a340f398167ffa2`.
- Provider usage: 574,833 input tokens and 157,498 billed output tokens over 154 completed
  requests.
- Measured completed-request cost: USD 0.566264. Conservative committed cost: USD 0.574427.
- Output: exactly 5,551 validated rows in source order.

## Quality boundary

The repository retains tested sampling and scoring utilities, but no human review queues, gold
labels, accuracy, macro-F1, per-label recall, or calibrated-confidence claims are included. The
`confidence_band` field is an uncalibrated operational placeholder, not a probability.

Verification: `uv run pytest`, `uv run ruff check src tests`, `uv run triage inspect`, and
`uv run triage forecast`. References: [shared vocabulary](../CONTEXT.md#message-triage),
[assessment brief](../AI_Engineer_Task.docx.pdf), and ADRs
[0001](../adrs/0001-separate-intent-from-urgency.md) through
[0004](../adrs/0004-freeze-before-held-out-evaluation.md).
