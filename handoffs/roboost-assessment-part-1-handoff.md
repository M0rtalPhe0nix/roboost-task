# Handoff: Part 1 - Product Listing Intelligence

## Next-session objective

Produce the written response for Case Study 2: E-Commerce Marketplace - Product Listing Intelligence. Make it implementation-ready and explicitly answer all five assessment questions.

## Read first

- Shared vocabulary: `/Users/mohamedomara/Documents/roboost-task/CONTEXT.md` (Listing Intelligence section)
- Decisions: `/Users/mohamedomara/Documents/roboost-task/docs/adr/0005-hold-ambiguous-high-risk-listings.md` through `0009-roll-out-injection-detection-in-monitor-mode.md`
- Brief: `/Users/mohamedomara/Documents/roboost-task/AI_Engineer_Task.pdf` (Part 1, Case Study 2)

## Settled scope

- The marketplace is Arabic-English regional; code-switching is normal.
- Prioritize an offer-focused, professional submission due within one month.
- Use a cost-tiered cascade: deterministic rules, compact text/vision candidate selection, then LLMs only for ambiguity and standardized description generation.
- Confirmed policy violations can be auto-rejected. Ambiguous high-risk listings are held unpublished, including when human review is at capacity; capacity pressure is not evidence of a violation.
- Allocate the 5% review capacity 80% expected-harm risk queue, 15% uncertainty/novelty, 5% stratified audit; safety emergencies preempt the queue.
- Use a governed category ontology with Arabic-English aliases. It can return an explicit category-gap outcome but cannot autonomously create production categories.
- Seller text, photos, and OCR are untrusted. Publication decisions require validated, evidence-linked fields and deterministic policy code, not raw content or unconstrained LLM extraction.
- Injection detection starts monitor-and-flag only. Do not treat a detection as proof of prohibited content; measure bilingual false positives before it can hold listings.
- Description tone is an allow-listed profile (for example neutral, concise, premium, friendly). It may alter wording only, never facts, category, or moderation.

## Key guardrail research

- OWASP LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP prevention cheat sheet: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- Google Model Armor overview: https://docs.cloud.google.com/model-armor/overview?hl=en

## Open work

- Turn decisions into a concise narrative/pipeline diagram and quantified threshold policy.
- State explicit assumptions on prohibited-item policy authority and model/provider availability.
- Add metrics for safety recall, false holds/rejects, categorization quality, cost/listing, review yield, category-gap/drift rate, and description factuality.
- Avoid claiming injection prevention is perfect; present defense in depth and adversarial testing.

## Suggested skills

- `domain-modeling` for any new language or durable decision.
- `pdf:pdf` to cite/check the brief.
- `excalidraw` only if an editable pipeline diagram materially improves the written deliverable.
