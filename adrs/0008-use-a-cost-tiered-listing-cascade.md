# Use a cost-tiered listing cascade

Listing intelligence uses deterministic rules first, compact text and vision models to narrow category and risk candidates, and an LLM only for ambiguous decisions and standardized-description generation. Standardized-description generation may use an allow-listed Tone Profile that affects wording only, never validated facts, category, or moderation. This reserves costly generative inference for work where it adds value while keeping high-volume and safety-critical decisions inspectable.
