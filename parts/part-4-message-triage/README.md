# Part 4 - High-Volume Message Triage

Runnable final pipeline for Part 4, Option C: classify a full day of customer messages into
refund request, complaint, order inquiry, compliment, spam, or urgent escalation within the
assessment's USD 1 API budget.

The supplied corpus contains 2,204 conversations and 5,551 customer-authored turns, rather than the brief's rounded 10,000-message description. The final submission must disclose and use the actual eligible-turn count.

## Current implementation status

The corpus parser, leakage-safe message representation, rule gate, Gemini structured-output
adapter, output validation, JSONL exporter, append-only cost ledger, and pre-request budget guard
are implemented. The paid full-corpus run completed for all 5,551 eligible messages. A blinded,
conversation-disjoint evaluation workflow is implemented and tested, but no human annotation or
quality evaluation will be performed for this submission. No accuracy, F1, or calibrated-confidence
claim is made.

Verified corpus profile:

| Measure | Count |
| --- | ---: |
| Conversations | 2,204 |
| All turns | 10,000 |
| Eligible customer turns | 5,551 |
| Brand-authored context turns | 4,449 |

The brief's "10,000 messages" corresponds to all conversation turns. Only the 5,551 inbound
customer turns are triage candidates. `seed_id` repeats in the source, so the implementation uses
`conversation_index + seed_id + turn_index` as its stable message identity while preserving the
source `seed_id` and turn index separately.

## Decision flow

1. Parse the corpus and yield only customer-authored turns. Each record contains only prior turns.
2. Apply a deliberately narrow deterministic gate for clear unsolicited spam, explicit
   legal/regulatory/public escalation threats, and credible harm already experienced.
3. Send unresolved records to stable `gemini-3.5-flash-lite` in batches of 50 with a compact JSON
   parallel-array Schema (`id`, `i`, and `u` on the wire) that is expanded to the documented output
   fields, using
   its default minimal thinking level and no requested audit explanation.
4. Validate exact one-to-one IDs and enums before accepting a batch.
5. Retain the primary `intent` and independent `is_urgent`, then derive the single
   `triage_label`; urgent escalation always takes precedence.

See [the approach document](docs/approach.md) and
[annotation guide](docs/annotation-guide.md) for the current decision contract.

## Cost control

The ordinary run has a hard USD 0.80 cap, leaving USD 0.20 beneath the task limit. Pricing is
versioned in code at the current Gemini 3.5 Flash-Lite standard paid rates: USD 0.30 per million
input tokens and USD 2.50 per million output tokens, including thinking tokens. Recheck the
[official Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) immediately before the
paid run if pricing or model selection changes.

Before every request, the ledger reserves a pessimistic cost using half the UTF-8 byte count as an
input-token estimate and the configured maximum output tokens. A request is refused if actual
completed spend plus outstanding reservations plus the new reservation would exceed the cap.
After a response, provider-reported prompt, candidate, and thinking tokens replace the reservation
with measured cost. Reservations and completions are fsynced to an append-only JSONL ledger, so an
interrupted request remains conservatively committed after restart.

Current no-API forecast using batch size 50 and 2,048 maximum output tokens. If a response still
reaches `MAX_TOKENS`, its billed usage is recorded and that batch alone is retried as two halves.
If Gemini returns valid results for only part of a batch, those exact IDs are checkpointed and only
the missing IDs are retried. Unknown IDs are discarded, duplicate IDs are withheld, and both cases
are written to the cost ledger as response anomalies before affected requested IDs are retried:

| Forecast measure | Value |
| --- | ---: |
| Model-fallback messages | 5,549 |
| Requests | 111 |
| Conservative input-token estimate | 965,268 |
| Reserved maximum output tokens | 227,328 |
| Sum of per-request maximum reservations | USD 0.857953 |
| Hard ordinary-run cap | USD 0.80 |
| Assessment limit | USD 1.00 |

The maximum-reservation sum is not committed at once: requests are sequential, and each reservation
is replaced by provider-reported actual usage before the next request. The USD 0.80 hard guard still
stops before the internal cap. Including the already recorded USD 0.005899 truncated attempt, the
maximum-reservation sum remains below the assessment's USD 1 limit.

### Completed run evidence

| Measure | Value |
| --- | ---: |
| Configuration hash | `aacd6cb395fc4762708497418f6bd7adfd177b67d75ea5a36a340f398167ffa2` |
| Classified customer turns | 5,551 |
| Gemini-completed requests | 154 |
| Provider input tokens | 574,833 |
| Provider billed output tokens | 157,498 |
| Measured completed-request cost | USD 0.566264 |
| Conservative committed cost | USD 0.574427 |
| Assessment limit | USD 1.00 |

The USD 0.574427 committed figure includes one interrupted request's USD 0.008163 reservation,
which remains outstanding by design. It is the safer number for budget compliance and leaves USD
0.425573 below the assessment limit. Gemini occasionally returned missing or unknown IDs; the
pipeline audited those anomalies, discarded unknown IDs, retried only unresolved requested IDs,
and still produced exactly one validated classification for every eligible message.

## API key and setup

Copy `.env.example` to `.env` in this directory, then replace the placeholder:

```dotenv
GEMINI_API_KEY=your-issued-key-here
```

The `.env` file is ignored by Git and loaded only for an explicitly authorized paid run. Never put
the real key in `.env.example`, source code, documentation, or a command committed to shell history.

## Commands

Run from this directory with Python 3.11 or newer:

```bash
uv sync --extra dev --extra gemini
uv run triage inspect
uv run triage forecast
uv run pytest
uv run ruff check src tests
```

The paid command is intentionally inert without both an environment-provided key and the explicit
authorization flag:

```bash
uv run triage run --allow-paid-api
```

For the existing interrupted pre-compaction run only, accept the audited configuration migration
while retaining its outstanding cost reservation:

```bash
uv run triage run --allow-paid-api --resume --accept-config-change
```

The completed run does not need to be called again for evaluation. Never put the key in the
repository. If a future fresh run is explicitly required, use a new output/ledger pair; if that
exact run is interrupted, rerun the same command with `--resume`. The state file rejects changed
input, prompt, model, price, budget, batch, or output settings, and accepted batches are not sent
again. The CLI refuses budgets above USD 1.00, defaults to USD 0.80, and will not call Gemini merely
for inspection, forecasting, or evaluation.

## Output contract

`outputs/classifications.jsonl` contains one row per eligible customer turn in source order:

```json
{
  "message_id": "c0:s0:t2",
  "conversation_index": 0,
  "seed_id": 0,
  "turn_index": 2,
  "intent": "order inquiry",
  "is_urgent": false,
  "triage_label": "order inquiry",
  "decision_source": "model_fallback",
  "confidence_band": "medium"
}
```

Confidence bands are uncalibrated operational placeholders tied to the decision path. They are not
model self-confidence scores or measured probabilities.

## Evaluation decision

The repository includes deterministic sampling and scoring code plus tests for a possible
conversation-disjoint 200-message calibration and 800-message held-out review. That human review
will not be performed for this submission, so:

- `outputs/evaluation/` intentionally contains no review queues or reports;
- no gold labels or label-level quality metrics are submitted;
- confidence bands remain uncalibrated placeholders; and
- the final claims are limited to completeness, schema validity, leakage controls, deterministic
  tests, provider usage, and measured cost.

The unused workflow is documented in [the evaluation record](docs/evaluation.md) so the absence of
quality metrics is explicit rather than implied.

## Decision boundary

Classify only inbound customer-authored turns. Earlier conversation turns may be used as context; later turns must never be used. Persist the primary intent and an independent urgent flag, then derive the required single `triage_label`; urgent escalation takes precedence.

Urgency is limited to explicit legal, regulatory, or social-media escalation threats and credible safety, health, or personal-data harm. Ordinary anger and churn intent do not meet that bar.

Use a high-precision deterministic Rule Gate for clear urgent and spam cases, then a batched Gemini Flash-Lite structured-output fallback only for ambiguity. The ordinary full-corpus run has a hard USD 0.80 maximum, retaining USD 0.20 safety margin below the assessment cap. Debug audit reasons are disabled in final output; confidence bands are uncalibrated operational placeholders, not model self-ratings.

## Workspace layout

```text
part-4-message-triage/
├── README.md
├── src/          # Corpus parsing, rules, model fallback, cost guard, export
├── docs/         # Annotation guide, approach document, evaluation record
├── tests/        # Routing, schema, leakage, and budget-guard tests
└── outputs/      # Final classifications and submission-safe evidence
```

## Quality boundary

No human-labeled evaluation set or accuracy metric is included in the final submission. The output preserves the source `seed_id`, original turn index, intent, urgent flag, triage label, decision source, and uncalibrated confidence band. The repository claims complete processing and deterministic contract coverage, not measured classification quality.

## References

- [Part 4 handoff](../../handoffs/roboost-assessment-part-4-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.docx.pdf)
- [Message Triage vocabulary](../../CONTEXT.md#message-triage)
- Related ADRs: [`0001`](../../adrs/0001-separate-intent-from-urgency.md), [`0002`](../../adrs/0002-use-only-available-conversation-history.md), [`0003`](../../adrs/0003-use-a-rule-gate-with-model-fallback.md), [`0004`](../../adrs/0004-freeze-before-held-out-evaluation.md)
