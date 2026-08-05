# COO guide - Pharmacy Operations Assistant

Use the assistant through Telegram for the quickest review or through ADK Web when a
technical operator is running the prototype locally. Both interfaces use the same
analytics and the same pharmacy workbook.

## Option 1: Telegram (recommended)

1. Scan the QR code below with your phone camera, or open
   [@pharmacy_operations_bot](https://t.me/pharmacy_operations_bot).
2. Choose **Start** in Telegram.
3. Send a question in the private chat. The bot does not operate in group chats.

<img src="assets/telegram-bot-qr.png" alt="QR code for the Pharmacy Operations Telegram bot" width="320">

The assessment bot is a temporary public demo: anyone who discovers its username can
message it. Do not send confidential, patient, prescription, customer, or employee
information. The supplied workbook is already connected; you do not need to upload it.

## Option 2: ADK Web on a computer

Ask a technical operator to start the local prototype from the Part 3 directory:

```bash
python scripts/run_adk_web.py
```

On first run, the launcher asks privately for the Gemini API key, creates the local
`.env`, installs uv if needed, installs the locked dependencies, starts ADK Web, and
opens the browser automatically. It does not replace an existing `.env`.

Then:

1. In the page opened at <http://localhost:8000>, select `app` from the agent list.
2. Start a new session and type a question in the message box.
3. Stop the prototype with **Ctrl+C** in the terminal when finished.

ADK Web is a local assessment and debugging interface. It must not be published to the
internet or treated as a production dashboard.

## Questions worth asking

- "Which comparable branches got slower last month?"
- "Show me zones with the highest rate of deliveries over 90 minutes."
- "Did dispatch lag or pickup lag increase for the worst branch?"
- "What should I look into from the latest complete month?"

Ask one concrete question at a time. Follow-up questions can narrow the result within
the same chat session.

## How to read an answer

Before acting, check the displayed period, metric definition, valid observation count,
active days, completeness, and Evidence Strength. A suppressed branch did not meet the
minimum comparison floor; it should not be interpreted as normal performance.

Numbers and rankings are calculated from the workbook, not invented by the language
model. Invalid timestamp sequences are excluded from the affected metric. Customer
comments appear separately as customer-reported signals.

The assistant cannot prove why an outcome happened. A longer dispatch or pickup lag is
a measured contributor, not proof of root cause. The 90-minute threshold is an analysis
convention, not a company SLA.

Do not use the assistant for medication or patient safety, clinical advice, inventory,
staffing, demand, cost/profit, or compliance decisions. Validate consequential findings
with branch managers and the responsible data owners.
