# Handoff: Part 4 - High-Volume Message Triage

## Next-session objective

Build and run the Option C customer-message triage pipeline, submit classifications and runnable code, and prepare its short explanatory document.

## Read first

- Shared vocabulary: `/Users/mohamedomara/Documents/roboost-task/CONTEXT.md` (Message Triage section)
- Decisions: `/Users/mohamedomara/Documents/roboost-task/docs/adr/0001-separate-intent-from-urgency.md` through `0004-freeze-before-held-out-evaluation.md`
- Data: `/Users/mohamedomara/Documents/roboost-task/AI Engineer Assessment/Messages Dataset/dm_message_corpus_10k.json`
- Brief: `/Users/mohamedomara/Documents/roboost-task/AI_Engineer_Task.pdf` (Part 4, Option C)

## Settled scope

- Classify only inbound customer-authored turns. Brand turns are prior-conversation context only. The supplied file contains 2,204 conversations and 5,551 customer turns, despite the brief calling it 10,000 messages.
- Use only earlier turns in the conversation for a message; never future turns.
- Preserve `intent` (refund request, complaint, order inquiry, compliment, spam) and independent `is_urgent`, then derive one required `triage_label`; urgent escalation takes precedence.
- Urgent means explicit legal/regulatory/social-media escalation or credible safety, health, or personal-data harm. Ordinary anger or churn intent is not urgent.
- Use a high-precision deterministic Rule Gate for obvious spam/urgent cases and a batched Gemini Flash-Lite structured-output Model Fallback for ambiguity.
- The ordinary full-corpus run must stop at USD 0.80, leaving USD 0.20 unused below the task cap. Do not spend blindly on retries.
- Audit reasons are debug/calibration-only behind a switch and disabled for the final full run. Final confidence is low/medium/high as a calibrated operational band, never raw LLM self-confidence.
- Build a manually reviewed, stratified 1,000-message evaluation set: 200 calibration, 800 held-out. Freeze rules/prompt/model/batching before reporting held-out results.
- Final output should preserve `seed_id` and original turn index, intent, urgent flag, triage label, decision source, and confidence band. Debug fields are optional/off for final run.

## Open work

- Securely locate/configure the issued Gemini API key via ignored environment settings; never write it to handoff/docs/repo.
- Inspect the corpus for language, label prevalence, and rules candidates. Create annotation guidance before human labeling.
- Implement usage metering and an enforceable pre-request spend guard; run small calibration batches before the one final full run.
- Define confidence calibration from the 200 labels and evaluate all required classifications on the frozen 800.
- Produce a transparent final README: count mismatch, decision hierarchy, cost ledger, model/version/prompt hashes, quality results, and limitations.

## Suggested skills

- `domain-modeling` for label-definition changes.
- `tdd` if building tests for rule routing and schema validation.
- `spreadsheets:Spreadsheets` if the human-labeling/evaluation worksheet is created.
- `openai-docs` is not relevant; use official Gemini documentation/pricing only when current API behavior needs verification.
