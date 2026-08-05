# Engineering handoff - responsible production readiness

## Current prototype boundary

Google ADK supplies the conversational runtime. The agent has one tool,
`analyze_operations`, which accepts only enumerated analyses, metrics, periods, and
dimensions. It cannot execute SQL or retrieve source rows. All calculations run in a
read-only pandas repository; Gemini receives only aggregated outputs.

The local ADK web UI is a reviewer/development surface. The container default runs the
official ADK Telegram connector with long polling. A mandatory gate accepts only private
chats before a message reaches ADK. It supports an explicit public assessment mode or a
numeric Telegram-ID allowlist. The assessment deployment enables public mode; the
connector still uses an in-memory session service.

## Data and metric contract

The loader requires the 13 documented workbook columns, unique order IDs, and valid
created timestamps. It derives delivery duration, dispatch lag, and pickup lag exactly
as stated in the source dictionary. Negative intervals become missing for that metric.

Evidence Strength combines valid observation count, active-day coverage, and metric
completeness. Branch comparisons require the floor in both periods; suppressed branches
are counted in the response. Relative periods are anchored to the maximum source
timestamp and ignore the partial current data month.

## Required production gates

1. **Data contract and lineage** - replace the workbook with a versioned, read-only
   warehouse view; validate schema, freshness, timezone, uniqueness, timestamp ordering,
   and row-count reconciliation on every load.
2. **Business definitions** - have Operations approve the delivery SLA/threshold,
   business-day timezone, minimum comparison floor, rating semantics, and branch-opening
   treatment. Version changes and back-test them.
3. **Evaluation** - maintain a reviewed question set covering supported routing,
   unsupported declines, Arabic/English phrasing, numerical fidelity, suppression,
   prompt injection, and adversarial requests. Gate releases on tool-choice and answer
   faithfulness, not only prose similarity.
4. **Access control** - put the API behind SSO or a non-public Telegram bot with a
   Telegram-ID allowlist. Add rate limits, short retention, secret management, and
   environment-specific service accounts. Never expose ADK Web publicly.
5. **Observability** - log request ID, authenticated actor, model/prompt/policy versions,
   tool arguments, aggregate result hash, latency, token use, refusal reason, and errors.
   Do not log raw workbook rows or secrets. Monitor data freshness, tool failures,
   unsupported-question rate, cost, and response latency.
6. **Privacy and security** - complete a threat model and privacy review. Preserve the
   aggregate-only tool boundary, enforce result-size limits, scan dependencies, and test
   that prompt content cannot change policy or access source rows.
7. **Human validation and rollout** - begin in shadow mode with an analyst, then a small
   COO/operations pilot. Require users to validate consequential findings. Expand only
   after numerical and refusal-error reviews meet agreed thresholds.
8. **Reliability** - use a persistent session service only if conversation history is
   required; define timeouts, retries, circuit breaking, model fallback behavior, backup,
   incident response, and rollback. The analytics layer should remain usable without an
   LLM for investigation and regression testing.

## Test coverage in this repository

The offline suite checks metric derivation, exclusion of negative intervals,
month-over-month comparison floors, sparse-branch suppression, separation of measured
and customer-reported signals, aggregate privacy, tool allow-listing, and the ADK prompt
contract. It makes no Gemini calls.

Before production, add warehouse integration tests, authenticated end-to-end tests,
load tests, multilingual behavioral evaluations, and a frozen regression set with
manually verified answers.

## Deployment position

The assessment bot runs as one Northflank deployment service because Telegram long
polling needs a continuously running worker. The ignored workbook is baked into an image
built from the local project directory; it is never committed to Git. This simplifies
the demo but means data changes require an image rebuild, and anyone with image access
can extract the workbook. Public Telegram access is limited to assessment review and
must be disabled afterward. Availability and in-memory sessions must not be described
as production-grade. See the
[Northflank worker handoff](../deploy/northflank-worker.md) for the exact boundary.
