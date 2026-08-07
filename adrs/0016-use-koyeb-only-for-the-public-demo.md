# Use Koyeb only for the public demo

**Status: Superseded by [ADR 0017](0017-use-northflank-for-the-public-demo.md).**

The Pharmacy Operations Assistant may be deployed to Koyeb's free web-service tier for reviewer access, while Docker Compose remains the canonical handoff. Koyeb's free instance has constrained compute, can scale to zero, and cannot attach persistent storage, so the submission must not rely on it for correctness or availability.
