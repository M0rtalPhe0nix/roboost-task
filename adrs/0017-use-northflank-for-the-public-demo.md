# Use Northflank for the public demo

The Pharmacy Operations Assistant assessment preview runs as one Northflank deployment worker
using Telegram long polling and a private immutable container image. Northflank replaced the
earlier Koyeb proposal because the Telegram adapter needs a continuously running worker rather than
a public web endpoint that can scale to zero. The deployment remains temporary and assessment-only;
Docker Compose and the local launcher are the canonical handoff paths, and production still
requires private access control, durable operational controls, monitoring, and incident response.
