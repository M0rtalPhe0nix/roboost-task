# High-volume message triage approach

## Objective

Classify every eligible inbound customer turn in the supplied one-day corpus into the assessment's
six routing labels while keeping paid Gemini usage below USD 1. The ordinary execution budget is
stricter: USD 0.80, with USD 0.20 intentionally unused.

## Design

The pipeline separates the customer's primary intent from urgency. This preserves business context
for urgent refund and complaint cases while producing one unambiguous routing label. Urgency wins
only when deriving the final label.

The deterministic first stage is intentionally small. It completes only high-precision spam or
urgent cases. Everything else is sent in compact batches to stable Gemini 3.5 Flash-Lite with a JSON
Schema. The prompt includes only earlier turns for context, treats message content as untrusted data,
and asks for no rationale. Application validation requires every requested ID exactly once and
rejects unknown IDs, duplicate IDs, missing items, bad enums, and wrong field types.

## Budget enforcement

Every model request is reserved in an append-only ledger before it is sent. The reservation prices
a deliberately pessimistic input-token ceiling plus the configured maximum output. Outstanding
reservations remain committed across restarts. Successful responses replace the reservation with
provider-reported prompt and billed output usage, where billed output includes both candidate and
thinking tokens. No blind retries are implemented.

The model name and rates are code configuration, not prose-only assumptions. As of 2026-08-06,
Gemini's official pricing lists `gemini-3.5-flash-lite` at USD 0.30 per million input tokens and USD
2.50 per million output tokens for standard paid requests. Pricing must be rechecked before the
final paid run.

## Evaluation boundary

The repository retains a tested design for a manually reviewed, stratified set of 1,000 customer
messages: 200 for calibration and 800 for a conversation-disjoint held-out evaluation. That human
evaluation will not be performed for the final submission.

The full run produced 5,551 classifications at USD 0.566264 measured cost and USD 0.574427
conservative committed cost. No review queues, gold labels, calibrated confidence bands, or quality
metrics are submitted. Quality must not be inferred from model predictions.
