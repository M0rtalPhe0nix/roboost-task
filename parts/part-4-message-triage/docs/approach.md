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

## Evaluation plan

Create a manually reviewed, stratified set of 1,000 customer messages. Use 200 only for calibration,
including rule and prompt changes, and keep 800 sealed for a single frozen evaluation. Report intent
macro-F1, per-label precision/recall/F1, urgent precision/recall, urgent-escalation routing quality,
rule-gate coverage and accuracy, schema failure rate, total provider tokens, and actual USD cost.

The full run produced 5,551 classifications at USD 0.566264 measured cost and USD 0.574427
conservative committed cost. The deterministic 200/800 review queues are prepared, but human gold
labels are not complete. Quality results must not be inferred from model predictions or reported
until the scorer accepts a completed review file.
