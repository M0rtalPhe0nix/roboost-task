# COO handoff - Pharmacy Operations Assistant

This guide is for the COO of the pharmacy group. It explains what was built, how to use
it, what its answers can support, and where human review or additional data is needed.

## What we built

The Pharmacy Operations Assistant is a conversational analysis tool for the supplied
pharmacy delivery workbook: 64,619 orders across 132 branches. You can ask an
operational question in plain English, and the assistant returns an explanation backed
by aggregate calculations from the workbook.

The language model interprets the question and explains the result, but it does not
calculate operational figures itself. An allow-listed analytics tool performs the
calculations using fixed metric definitions, quality checks, and comparison thresholds.
This design keeps the answers grounded in the available data and prevents access to
individual customer or order records.

Use the assistant through Telegram for the quickest review or download the use case to
run ADK Web on a computer. Both interfaces use the same analytics and workbook.

## How to use it

### Option 1: Telegram (recommended)

1. Scan the QR code below with your phone camera, or open
   [@pharmacy_operations_bot](https://t.me/pharmacy_operations_bot).
2. Choose **Start** in Telegram.
3. Send a question in the private chat. The bot does not operate in group chats.

<img src="assets/telegram-bot-qr.png" alt="QR code for the Pharmacy Operations Telegram bot" width="320">

The assessment bot is a temporary public demo: anyone who discovers its username can
message it. Do not send confidential, patient, prescription, customer, or employee
information. The supplied workbook is already connected; you do not need to upload it.

### Option 2: Download and run ADK Web on a computer

You need an internet connection, [Python 3.11-3.14](https://www.python.org/downloads/),
the supplied anonymized pharmacy workbook, and a
[Gemini API key](https://aistudio.google.com/app/apikey).

1. Press **[Download the Pharmacy Operations Assistant use-case folder
   (.zip)](https://download-directory.github.io/?url=https%3A%2F%2Fgithub.com%2FM0rtalPhe0nix%2Froboost-task%2Ftree%2Fmain%2Fparts%2Fpart-3-pharmacy-operations-assistant&filename=pharmacy-operations-assistant)**.
   The download should begin automatically. This link packages the public Part 3
   folder from GitHub; it does not require a GitHub account.
2. Open the Downloads folder and extract `pharmacy-operations-assistant.zip`. Open the
   extracted `pharmacy-operations-assistant` folder. The correct folder contains
   `README.md`, `pyproject.toml`, and the `scripts` and `data` folders.
3. Confirm that the supplied workbook is at
   `data/operations_data_anonymized.xlsx`. The workbook is not included in the public
   download. If the `data` folder is empty, copy the supplied
   `operations_data_anonymized.xlsx` file into it before continuing.
4. Open a terminal in the extracted `pharmacy-operations-assistant` folder:

   - **Windows 11:** Right-click an empty area inside the folder and choose **Open in
     Terminal**. On Windows 10, click the File Explorer address bar, type `powershell`,
     and press **Enter**.
   - **macOS:** Open the Terminal app, type `cd ` including the space, drag the
     extracted folder from Finder into the Terminal window, and press **Return**.

5. Run the launcher in that terminal:

   **Windows:**

   ```powershell
   py scripts\run_adk_web.py
   ```

   If Windows says `py` is not recognized, try:

   ```powershell
   python scripts\run_adk_web.py
   ```

   **macOS:**

   ```bash
   python3 scripts/run_adk_web.py
   ```

6. On the first run, paste the Gemini API key when the terminal asks for it. The input
   is hidden while you type. The launcher then installs the required locked
   dependencies, starts ADK Web, and opens <http://localhost:8000> in the browser.
7. In ADK Web, select `app` from the agent list, start a new session, and type a
   question in the message box.
8. When finished, return to the terminal and press **Ctrl+C** to stop the assistant.

The launcher does not replace an existing `.env` file. ADK Web runs only on this
computer; do not publish it to the internet or treat it as a production dashboard.

### Questions worth asking

- "Which comparable branches got slower last month?"
- "Show me zones with the highest rate of deliveries over 90 minutes."
- "Did dispatch lag or pickup lag increase for the worst branch?"
- "What should I look into from the latest complete month?"

Ask one concrete question at a time. Follow-up questions can narrow the result within
the same chat session. The assistant remembers only the latest 10 visible messages when
answering; start a fresh question with the necessary context if it was discussed earlier.

## What you can rely on it for

You can rely on the assistant to:

- Calculate aggregate operational figures and rankings from the supplied workbook,
  rather than asking the language model to invent or estimate them.
- Compare qualifying branches month over month using median delivery duration,
  dispatch lag, and pickup lag.
- Highlight long-delivery patterns by branch, zone, order hour, or pseudonymous rider.
- Report the period, metric definition, valid observation count, active days,
  completeness, and Evidence Strength needed to judge an answer.
- Exclude invalid timestamp sequences from the affected metric and suppress branch
  comparisons that do not meet the minimum evidence floor.
- Keep customer-comment signals separate from measured timing contributors.

A finding with stronger evidence is a good starting point for operational investigation
and prioritization. Before acting, still confirm consequential findings with the
relevant branch managers and data owners.

## What you should not rely on it for

The assistant cannot prove why an outcome happened. A longer dispatch or pickup lag is
a measured contributor, not proof of root cause. The 90-minute threshold is an analysis
convention, not a company SLA.

Do not use the assistant to:

- Make medication or patient-safety decisions or provide clinical advice.
- Make inventory, staffing, demand, cost, profit, or compliance decisions; the workbook
  does not contain the required source data.
- Treat customer-comment keywords as verified causes.
- Treat a suppressed branch as performing normally; suppression means there was not
  enough reliable data for the comparison.
- Interpret “last month” as the current calendar month. It means the latest complete
  month in the workbook; July 2026 is only partial.
- Request or expose source rows, customer IDs, or order IDs.

Use its results as decision support and an investigation starting point, not as an
autonomous decision or a substitute for operational ownership.
