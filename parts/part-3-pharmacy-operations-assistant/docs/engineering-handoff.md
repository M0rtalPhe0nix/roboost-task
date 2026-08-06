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
connector still uses an in-memory session service. A `before_model_callback` limits each
Gemini request to the latest 10 human-visible messages by default while preserving tool
call/response contents inside that window. The Telegram session service physically
discards older events, evicts sessions idle for one hour, and retains at most 25 active
sessions. Connector metadata follows the same bounds, and a global semaphore processes
one Telegram message at a time. `CHAT_HISTORY_MESSAGES`, `SESSION_IDLE_TTL_SECONDS`,
`MAX_ACTIVE_SESSIONS`, and `MAX_CONCURRENT_MESSAGES` configure these limits.

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
3. **Access control** - put the API behind SSO or a non-public Telegram bot with a
   Telegram-ID allowlist. Add rate limits, short retention, secret management, and
   environment-specific service accounts. Never expose ADK Web publicly.
4. **Observability** - log request ID, authenticated actor, model/prompt/policy versions,
   tool arguments, aggregate result hash, latency, token use, refusal reason, and errors.
   Do not log raw workbook rows or secrets. Monitor data freshness, tool failures,
   unsupported-question rate, cost, and response latency.
5. **Privacy and security** - complete a threat model and privacy review. Preserve the
   aggregate-only tool boundary, enforce result-size limits, scan dependencies, and test
   that prompt content cannot change policy or access source rows.
6. **Human validation and rollout** - begin in shadow mode with an analyst, then a small
   COO/operations pilot. Require users to validate consequential findings. Expand only
   after numerical and refusal-error reviews meet agreed thresholds.
7. **Reliability** - use a persistent session service only if conversation history is
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

## Memory evidence for the assessment worker

On 2026-08-06, a local macOS peak-RSS diagnostic over all 64,619 rows measured 253.7 MiB
when loading the source workbook directly and 186.5 MiB when loading the prepared runtime
dataset. The retained analytics frame decreased from 28.8 MiB to 2.4 MiB. These figures
show the direction and local headroom; they are not a Linux-container guarantee. Re-run
the representative analytics load under the deployment image's 256 MiB memory limit
after dependency, Python, workbook, or schema changes.

The corresponding Linux/amd64 image check, run under a hard 256 MiB Docker cgroup limit,
constructed the bounded Telegram connector and completed the representative watch-out
analysis with a 195.1 MiB cgroup peak and 175.0 MiB current usage. This is a deployment
smoke test rather than an end-to-end model-call load test; retain the one-message
concurrency limit and monitor the live worker for OOM restarts.

## Deployment position

The assessment bot runs as one Northflank deployment service because Telegram long
polling needs a continuously running worker. The ignored workbook is validated and
converted into a compact typed dataset during the image build; the worker reads that
dataset instead of parsing Excel at runtime. The source workbook remains inside the
private image and is never committed to Git. This simplifies the demo but means data
changes require an image rebuild, and anyone with image access can extract the data.
Public Telegram access is limited to assessment review and must be disabled afterward.
Availability and bounded in-memory sessions must not be described as production-grade. See the
[Northflank worker handoff](../deploy/northflank-worker.md) for the exact boundary.

The 2026-08-06 assessment release is pinned by digest and its Northflank rollout evidence
is recorded in that worker handoff. The platform check does not replace the documented
post-release Telegram conversation checks.
