# AI Engineer Assessment

The bounded work required to submit a professional AI-engineering assessment. It combines written product reasoning with reproducible build artifacts.

## Delivery

**Assessment Submission**:
The complete set of assessment deliverables, targeted for completion within one month from the start of this session.
_Avoid_: Assignment, exam

**Offer-Focused Submission**:
An Assessment Submission designed to maximize the likelihood of receiving an offer through defensible judgment, reproducibility, and clear communication.
_Avoid_: Learning project, feature showcase

## Message Triage

**Customer Message**:
An inbound message authored by a customer in the supplied message corpus. Brand-authored messages provide context but are not triage candidates.
_Avoid_: Conversation, brand reply

**Intent**:
The customer's primary need: refund request, complaint, order inquiry, compliment, or spam.
_Avoid_: Triage label, queue

**Urgency**:
An independent signal that immediate operational escalation is required: explicit legal, regulatory, or social-media escalation threats, or credible safety, health, or personal-data harm. Ordinary anger and churn intent are not Urgency.
_Avoid_: Intent, severity

**Triage Label**:
The single routing outcome required by the assessment. It is derived from Intent and Urgency; an urgent Customer Message is routed as urgent escalation.
_Avoid_: Intent, category

**Available Conversation History**:
The messages in a conversation that occurred before the Customer Message being triaged. It may be used as context; later turns may not.
_Avoid_: Full conversation, future context

**Rule Gate**:
The deterministic first stage that assigns only high-precision triage outcomes or risk signals before model inference.
_Avoid_: Fallback, model classifier

**Model Fallback**:
The batched, structured-output model stage used only when the Rule Gate cannot safely make a decision.
_Avoid_: Rule gate, retry

**Evaluation Set**:
A manually reviewed, stratified set of 1,000 Customer Messages used to measure triage quality. It is partitioned into 200 calibration messages and 800 held-out test messages.
_Avoid_: Production output, training data

**Option C Execution Budget**:
The maximum permitted Gemini API spend for the normal full-corpus triage run: USD 0.80. The remaining USD 0.20 of the assessment limit is an unused safety margin.
_Avoid_: Assessment-wide key budget, target spend

**Audit Reason**:
A short explanation of a triage outcome used only during debugging and calibration. It is controlled by an explicit switch and excluded from the final full-corpus run.
_Avoid_: Final classification, source evidence

**Confidence Band**:
An operational low, medium, or high confidence label derived from the decision path and calibrated accuracy, rather than a model's unverified self-rating.
_Avoid_: Probability, model self-confidence

## Listing Intelligence

**Regional Marketplace**:
An Arabic-English marketplace in which listings can be Arabic, English, or code-switched across the two languages.
_Avoid_: Single-language marketplace, translation exception

**High-Risk Listing**:
A listing with meaningful but insufficient evidence of a prohibited item. It is held unpublished for human review, not rejected because of review-capacity pressure.
_Avoid_: Confirmed violation, approved listing

**Confirmed Violation**:
A listing with unambiguous evidence that it breaches marketplace prohibition policy. It may be automatically rejected.
_Avoid_: High-risk listing, suspicious listing

**Review Allocation**:
The distribution of the marketplace's 5% human-review capacity: 80% for risk-prioritized ambiguous listings, 15% for uncertainty or novelty, and 5% for stratified audit. Emergency safety signals may preempt the queue.
_Avoid_: Random sample, first-in-first-out queue

**Category Ontology**:
The governed semantic layer around the fixed category tree, containing category relationships and Arabic-English aliases. It may identify category gaps but cannot autonomously add production categories.
_Avoid_: Self-modifying taxonomy, ungoverned category list

**Category Gap**:
An explicit abstention outcome for a listing that has no adequate category in the approved Category Ontology. It is queued for taxonomy-owner review.
_Avoid_: Forced category, new production category

**Validated Field**:
A structured listing fact that has passed schema, allow-list, and evidence-link validation. Only Validated Fields may be used by the deterministic policy engine to select a publication action.
_Avoid_: Raw listing content, unverified extraction

**Injection Signal**:
An indication that untrusted listing text, OCR, or image content attempts to alter system behavior. It is a content-integrity signal, not evidence that an item is prohibited.
_Avoid_: Confirmed violation, policy decision

**Tone Profile**:
An allow-listed presentation setting for standardized descriptions, such as neutral, concise, premium, or friendly. It may change wording but cannot change Validated Fields, category, or moderation.
_Avoid_: Free-form instruction, product fact

## Review Benchmarking

**Focal Brand**:
The brand for which an AI Summary is generated as the client. The other brands in the comparison are its competitors.
_Avoid_: Market-wide owner, universal client

**Focal-Brand View**:
One AI Summary that treats exactly one comparison brand as the Focal Brand. The assessment will produce one view each for Lumen Coffee, Solara Coffee, and Vera Coffee.
_Avoid_: Combined verdict, all-brand summary

**Observation**:
An evidence-bound statement describing a pattern in public review data. It does not assert an unobserved cause or promised business outcome.
_Avoid_: Causal conclusion, recommendation

**Suggested Action Plan**:
A proposed response to an Observation that is clearly distinguished from the evidence and framed for validation, not as a guaranteed outcome.
_Avoid_: Observation, direct causal claim

**Business Context Profile**:
Versioned, client-provided operational information used to make Suggested Action Plans feasible, including controllable levers, role ownership, constraints, channels, and active initiatives. It is separate from public review evidence.
_Avoid_: Inferred operating model, review data

**Review-Only Mode**:
The AI Summary behavior when no Business Context Profile is available. It may produce an Observation and a generic, testable response, but identifies the context needed before assigning operational ownership or promising feasibility.
_Avoid_: Context-aware action plan, operational recommendation

**Core F&B Model**:
The category-agnostic review and operations vocabulary shared by all food-and-beverage clients, including product quality, service, speed, value, cleanliness, channel, and location.
_Avoid_: Category playbook, client context

**Category Playbook**:
A governed configuration that specializes the Core F&B Model for a category through aspects, evidence mappings, and possible action levers.
_Avoid_: Client context profile, universal taxonomy

## Pharmacy Operations

**Pharmacy Operations Assistant**:
The Part 3 prototype for a 132-branch pharmacy group. It answers operational questions from supplied pharmacy orders, deliveries, and review data for a non-technical COO.
_Avoid_: Restaurant operations assistant

**Evidence Strength**:
A high, medium, or low label for an operational calculation derived from observation count, time coverage, and data completeness. Material outputs display their underlying counts; rankings below the minimum comparison floor are suppressed.
_Avoid_: Count-only reliability, model confidence

**Unsupported Question**:
A COO question that cannot be answered from the supplied orders, delivery, rating, and comment data. The assistant declines it and identifies the additional source required instead of inferring an answer.
_Avoid_: Best-effort answer, plausible guess

**Measured Contributor**:
A deterministically calculated operational factor, such as dispatch lag, pickup lag, or delivery duration, associated with an observed performance change.
_Avoid_: Proven cause, review signal

**Customer-Reported Signal**:
A pattern in customer comments that provides supporting experience evidence but does not establish operational causation.
_Avoid_: Measured contributor, proven cause

**Koyeb Demo Deployment**:
The optional public preview of the Pharmacy Operations Assistant, deployed as one Koyeb free web service. It is not the canonical runtime because the free instance can scale to zero and has no persistent volume.
_Avoid_: Production deployment, canonical handoff

**Listing Cascade**:
The cost-tiered processing path for listings: deterministic rules, compact text and vision candidate selection, then LLM handling only for ambiguity and controlled description generation.
_Avoid_: LLM-only pipeline, one-model solution
