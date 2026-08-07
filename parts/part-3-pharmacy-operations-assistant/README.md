# Part 3 - Pharmacy Operations Assistant

A working Google Agent Development Kit (ADK) assistant for the COO of a 132-branch
pharmacy group. Gemini converts a plain-language question into one allow-listed tool
call; deterministic pandas code performs every calculation over the read-only workbook
and returns aggregate evidence for the model to explain.

The assessment brief says "restaurant" and "120 branches," but the supplied workbook is
the authoritative source: 64,619 pharmacy delivery orders across 132 branches.

## Try the prototype

| Interface | Best for | How to open it |
| --- | --- | --- |
| Telegram | Fast assessor or COO review | Open [@pharmacy_operations_bot](https://t.me/pharmacy_operations_bot) or scan the QR code in the [COO guide](docs/coo-handoff.md#option-1-telegram-recommended). |
| ADK Web | Local development and transparent tool inspection | Run `python scripts/run_adk_web.py`; the launcher prepares the project and opens the UI. |

Telegram accepts private chats only. The public assessment bot is temporary and must
not receive confidential, patient, prescription, or employee information. ADK Web is a
local reviewer/development interface and must not be exposed publicly.

Try one of these questions:

- `Which comparable branches got slower last month?`
- `Show me zones with the highest rate of deliveries over 90 minutes.`
- `Did dispatch lag or pickup lag increase for the worst branch?`
- `What should I look into from the latest complete month?`

## What it can answer

- Month-over-month changes in median delivery duration, dispatch lag, or pickup lag for
  branches that meet the comparison floor.
- Aggregated long-delivery patterns by branch, zone, order hour, or pseudonymous rider.
- Operational watch-outs covering timing, ratings, comment signals, comparison
  suppression, and timestamp-quality warnings.
- Dataset scope, metric definitions, sample counts, time windows, and Evidence Strength.

It declines medication/patient safety, inventory, staffing, demand, cost/profit, and
definitive-cause questions and names the missing source. It never accepts SQL or returns
source rows, customer IDs, or order IDs.

## Architecture

```text
ADK Web or private Telegram chat
    -> Google ADK Agent (Gemini: intent and explanation)
       -> latest 10 visible chat messages included in model context
       -> analyze_operations (one allow-listed tool)
          -> OperationsRepository (read-only deterministic pandas calculations)
             -> local workbook or compact worker dataset
       <- aggregate observations, counts, evidence labels, and warnings
```

## Run ADK Web locally

Prerequisites: Python 3.11-3.14, a Gemini API key, and internet access for first-time setup.
The supplied anonymized workbook is included at `data/operations_data_anonymized.xlsx`
so the assessment prototype runs from a fresh clone.

```bash
python scripts/run_adk_web.py
```

On first run, the launcher securely prompts for the Gemini API key if `.env` is absent,
installs [uv](https://docs.astral.sh/uv/) for the current user if needed, installs the
locked dependencies, starts ADK Web on loopback, and opens <http://localhost:8000> in
the default browser. Select `app` and start a new chat. Press **Ctrl+C** in the launcher
terminal to stop the server.

The launcher preserves an existing `.env` without prompting or overwriting it. Use
`python scripts/run_adk_web.py --no-browser` for a headless launch or `--port PORT` to
choose another loopback port. To keep the workbook elsewhere, set
`OPERATIONS_DATA_PATH` in `.env`.

Gemini receives at most the latest 10 human-visible user/assistant messages on each
model call. Tool-call records inside that window are preserved but do not count toward
the limit. Configure the window with `CHAT_HISTORY_MESSAGES` (1-50).

The Telegram worker also physically trims older ADK events, evicts idle sessions after
one hour, keeps at most 25 active sessions, and processes one message at a time by
default. Configure these safeguards with `SESSION_IDLE_TTL_SECONDS`,
`MAX_ACTIVE_SESSIONS`, and `MAX_CONCURRENT_MESSAGES`.

## Run with Docker Compose

```bash
cp .env.example .env
# Add GOOGLE_API_KEY to .env.
docker compose up --build
```

Compose mounts the workbook read-only and serves ADK Web at <http://localhost:8000>.
Override its host path with
`OPERATIONS_DATA_FILE=/absolute/path/to/operations_data_anonymized.xlsx`.

## Run Telegram locally

Set `TELEGRAM_BOT_TOKEN` in `.env`. For a short-lived public demo, also set
`TELEGRAM_PUBLIC_ACCESS=true`. For private use, leave public access false and set
`TELEGRAM_ALLOWED_USER_IDS` to comma-separated numeric Telegram user IDs.

```bash
uv run python -m app.telegram_bot
```

The container uses this Telegram worker as its default process. The assessment instance
is hosted on Northflank; see the [deployment handoff](deploy/northflank-worker.md).

## Verification

```bash
uv run ruff check .
uv run pytest --cov=app --cov-report=term-missing
```

These checks are deterministic and make no Gemini calls. The checked-in conversational
eval set documents routing, tool arguments, multi-turn drill-downs, causal restraint, the
90-minute non-SLA guardrail, privacy, and unsupported questions, but no live model-scored
evaluation is claimed for the final submission.

## Reliability policy

- `delivery_duration_minutes = DeliveryTime - CreatedDate`
- `dispatch_lag_minutes = AddedToTripTime - CreatedDate`
- `pickup_lag_minutes = PickingUpTime - AddedToTripTime`
- Negative or missing intervals are excluded from that metric and reduce completeness.
- Branch comparisons require 50 valid observations, 14 active days, and 90% metric
  completeness in both months. In May-June 2026, 22 branches pass this floor.
- Evidence Strength is high at 100+ valid observations, 20+ active days, and 95%+
  completeness; medium at the comparison floor; otherwise low.
- A long delivery is over 90 minutes. This analysis threshold is near the source 75th
  percentile; it is not a contractual SLA.
- Arabic/English late-delivery keywords are reported as customer signals, never as
  proven causes.

All thresholds are versioned environment settings rather than model choices.

## Repository layout

```text
app/                     ADK agent, policy, deterministic analytics, Telegram transport
data/                    included anonymized assessment workbook
deploy/                  Northflank worker handoff
docs/                    COO and engineering guides, plus the Telegram QR asset
scripts/                 local launcher and worker-dataset preparation
tests/                   deterministic contract, analytics, eval-set, and bot tests
.env.example             safe configuration template
compose.yaml             local ADK Web handoff
Dockerfile               Telegram worker image
pyproject.toml, uv.lock  dependencies and reproducible lockfile
```

## Known limitations

- Relative `last month` means the latest complete workbook month, not the current
  calendar month; July 2026 is partial.
- Invalid timestamp intervals are excluded metric by metric and reduce completeness.
- Keyword comment signals are not full multilingual semantic classification.
- The workbook has no approved SLA, branch metadata, inventory, staffing, medication,
  promotions, cost, weather, traffic, or incident data.
- Public Telegram access can consume model quota. Sessions are in memory; production
  still requires the controls in the engineering guide.
- Conversation continuity is limited to the latest 10 visible messages by default;
  earlier messages are not sent to Gemini.
- The worker image converts the workbook into a compact typed dataset at build time to
  avoid openpyxl's runtime memory spike. Data changes therefore require an image rebuild.

## Handoffs and decisions

- [COO usage guide](docs/coo-handoff.md)
- [Engineering production-readiness guide](docs/engineering-handoff.md)
- [Northflank deployment handoff](deploy/northflank-worker.md)
- [Pharmacy domain ADR](../../adrs/0013-treat-part-3-as-a-pharmacy-domain.md)
- [Evidence Strength ADR](../../adrs/0014-show-evidence-strength-for-operational-calculations.md)
- [Measured contributors vs. customer signals ADR](../../adrs/0015-separate-measured-contributors-from-review-signals.md)
- [Northflank assessment deployment ADR](../../adrs/0017-use-northflank-for-the-public-demo.md)
