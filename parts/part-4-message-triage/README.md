# Part 4 - High-Volume Message Triage

Working-pipeline workspace for Part 4, Option C: classify a full day of customer messages into refund request, complaint, order inquiry, compliment, spam, or urgent escalation within the assessment's USD 1 API budget.

The supplied corpus contains 2,204 conversations and 5,551 customer-authored turns, rather than the brief's rounded 10,000-message description. The final submission must disclose and use the actual eligible-turn count.

## Required submission

This workspace will contain runnable code, the full classification output, and a short approach document. The final README must report:

- Exact input and eligible-message counts, including the treatment of brand-authored turns.
- Decision hierarchy, model/provider version, prompt and configuration hashes, and frozen evaluation setup.
- Cost ledger, enforced spend guard, and final API usage.
- Evaluation methodology and quality results from the held-out set.
- Output schema, run instructions, limitations, and how to reproduce the final run safely.

## Decision boundary

Classify only inbound customer-authored turns. Earlier conversation turns may be used as context; later turns must never be used. Persist the primary intent and an independent urgent flag, then derive the required single `triage_label`; urgent escalation takes precedence.

Urgency is limited to explicit legal, regulatory, or social-media escalation threats and credible safety, health, or personal-data harm. Ordinary anger and churn intent do not meet that bar.

Use a high-precision deterministic Rule Gate for clear urgent and spam cases, then a batched Gemini Flash-Lite structured-output fallback only for ambiguity. The ordinary full-corpus run has a hard USD 0.80 maximum, retaining USD 0.20 safety margin below the assessment cap. Debug audit reasons are calibration-only and must be disabled in final output; confidence bands are calibrated operational labels, not model self-ratings.

## Intended workspace layout

```text
part-4-message-triage/
├── README.md
├── src/          # Corpus parsing, rules, model fallback, cost guard, export
├── docs/         # Annotation guide, approach document, evaluation record
├── tests/        # Routing, schema, leakage, and budget-guard tests
└── outputs/      # Final classifications and submission-safe evidence
```

## Evaluation boundary

Create a manually reviewed, stratified 1,000-message evaluation set: 200 calibration messages and 800 held-out messages. Improve rules, prompts, thresholds, batching, and model choice using calibration only, then freeze them before running the held-out evaluation. Final output preserves the source `seed_id`, original turn index, intent, urgent flag, triage label, decision source, and confidence band.

## References

- [Part 4 handoff](../../handoffs/roboost-assessment-part-4-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.pdf)
- [Message Triage vocabulary](../../CONTEXT.md#message-triage)
- Related ADRs: [`0001`](../../docs/adr/0001-separate-intent-from-urgency.md), [`0002`](../../docs/adr/0002-use-only-available-conversation-history.md), [`0003`](../../docs/adr/0003-use-a-rule-gate-with-model-fallback.md), [`0004`](../../docs/adr/0004-freeze-before-held-out-evaluation.md)

