# Handoff: Part 3 - Pharmacy Operations Assistant

## Next-session objective

Build and document the working Pharmacy Operations Assistant prototype, plus the COO and engineering handoff documents.

## Read first

- Shared vocabulary: `./roboost-task/CONTEXT.md` (Pharmacy Operations section)
- Decisions: `./roboost-task/docs/adr/0013-treat-part-3-as-a-pharmacy-domain.md` through `0016-use-koyeb-only-for-the-public-demo.md`
- Data: `./roboost-task/AI Engineer Assessment/Operations Dataset/operations_data_anonymized.xlsx`
- Brief: `./roboost-task/AI_Engineer_Task.pdf` (Part 3)

## Settled scope

- The data is authoritative: build a pharmacy assistant, not a restaurant assistant. The data dictionary identifies 64,619 delivery orders and 132 branches; brief references to restaurant and 120 branches are treated as stale/incorrect.
- Stack preference: FastAPI + React + Docker + uv + pnpm.
- The LLM interprets a COO question into an allow-listed, read-only query plan. All numbers and rankings are deterministically computed from the workbook. Answers include filters/definitions and evidence-strength context; do not expose raw query logic by default.
- Evidence Strength is high/medium/low and considers observation count, time coverage, and completeness. Display underlying counts and suppress inadequate branch comparisons.
- An assistant must decline unsupported questions (medication safety, inventory, staffing, definitive causation, etc.) and name the missing source.
- For “why” questions, show measured timing contributors (dispatch/pickup/delivery) separately from customer-reported comment signals; neither is described as a proven root cause.
- Primary COO interface: Telegram bot. React is internal/admin debugging only. Use a Telegram-ID allowlist and keep the bot non-public for an internal operations use case.
- Koyeb is the optional public demo deployment. Docker Compose is the canonical handoff; do not rely on Koyeb free-tier availability or storage.

## Data facts already verified

- One spreadsheet data sheet plus a data dictionary.
- Fields include order/customer pseudonymous IDs, optional Arabic-English comments, rating, branch, delivery zone, rider, amount, created/shift/delivery/assigned/pickup timestamps.
- Deterministic derived metrics: end-to-end delivery duration, dispatch lag, pickup lag.
- Branch coverage is materially uneven; at least BR-131 and BR-132 begin late in the observed window, while other branch IDs have sparse records. Comparability safeguards are necessary.

## Deployment research

- Telegram Bot API: https://core.telegram.org/bots
- Koyeb free instance: one 512 MB / 0.1 vCPU service, no persistent volume, scales to zero after one idle hour: https://www.koyeb.com/docs/reference/instances
- Do not claim permanent free availability. Render sleeps after 15 minutes; Cloud Run needs a billing account and charges beyond free quotas.

## Open work

- Profile workbook dates, distributions, data quality, and define exact minimum-comparability thresholds from data.
- Decide query-plan schema, allowed metric catalog, and natural-language routing/fallback behavior.
- Build FastAPI analysis layer, Telegram adapter, React admin/debug UI, Docker Compose, Koyeb manifest/deployment notes, tests, and two short handoff documents.
- Ensure no Gemini API key or bot token enters the repository.

## Suggested skills

- `spreadsheets:Spreadsheets` for workbook inspection and any output workbook.
- `domain-modeling` for pharmacy terminology.
- `browser:control-in-app-browser` for local UI QA if needed.
- `sites:sites-building` only if `.openai/hosting.json` exists (otherwise do not use).
