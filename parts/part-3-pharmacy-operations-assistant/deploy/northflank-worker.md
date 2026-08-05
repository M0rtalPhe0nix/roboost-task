# Northflank Telegram worker handoff

The public assessment bot runs as a single Northflank deployment service using Telegram
long polling. It has no inbound HTTP port. Keep exactly one replica: concurrent pollers
using the same bot token compete for updates, and sessions are currently process-local.

The deployed bot is [@pharmacy_operations_bot](https://t.me/pharmacy_operations_bot).
`TELEGRAM_PUBLIC_ACCESS=true` permits any Telegram user to start a private chat; group
chats remain blocked. This is a temporary assessment setting, not production access
control.

## Image contract

The Docker image contains the app, locked production dependencies, and the ignored local
workbook at `data/operations_data_anonymized.xlsx`. During the build, the workbook is
validated and converted to `data/operations.runtime.csv.gz`; the worker reads this
compact typed dataset to avoid loading Excel with openpyxl inside the 256 MB runtime.
Build from this Part 3 directory; a fresh Git clone does not contain the workbook and
therefore cannot build the image without the authorized data file.

```bash
docker build --platform linux/amd64 \
  -t ghcr.io/<github-user>/roboost-pharmacy-operations-assistant:<tag> .
docker push ghcr.io/<github-user>/roboost-pharmacy-operations-assistant:<tag>
```

Prefer deploying an immutable image digest after the push.

## Service configuration

Configure a Northflank **deployment service** with:

- one continuously running instance;
- no public port;
- the image's default command (the Telegram worker);
- registry credentials with pull-only access to the private GHCR image;
- a secret group containing `GOOGLE_API_KEY` and `TELEGRAM_BOT_TOKEN`;
- `TELEGRAM_PUBLIC_ACCESS=true` only for the short-lived assessment demo; and
- the default session limits in `.env.example` unless load testing supports a change.

For private use, set `TELEGRAM_PUBLIC_ACCESS=false` and configure comma-separated numeric
IDs in `TELEGRAM_ALLOWED_USER_IDS`.

## Release check

After changing code or data:

1. Run Ruff and the deterministic test suite from the README.
2. Build and push a new uniquely tagged image.
3. Update the service to the new digest without changing its secrets.
4. Confirm one container is running and logs show Telegram long polling started.
5. Send `/start`, one supported analytics question, and one unsupported safety question.
6. Confirm a group message is rejected before sharing the bot.

Do not paste unfiltered connector logs into tickets or chat: HTTP request URLs may expose
the Telegram bot token. Never add credentials to the image, repository, or deployment
documentation.

## Current assessment release

On 2026-08-06, Northflank was updated to the Linux/amd64 image digest
`sha256:ce22d2afabe87cde90c7ba3b5bb6c6682736cc200a20c365158051120a106dc4`.
The control plane reported the deployment as `COMPLETED`, with one new container in
`TASK_RUNNING`; containers from earlier releases were `TASK_KILLED` as expected after
replacement. The same image completed the representative analytics smoke test under a
hard 256 MiB Docker memory limit before deployment. A live Telegram conversation check
is still required after each release because the local smoke test does not call Gemini
or Telegram.

## Shutdown and production boundary

Disable or remove the public service after assessment review and rotate exposed demo
credentials. Before production, use an identity allowlist or SSO, rate limits, durable
sessions if required, audit logging, monitoring, evaluation gates, incident response,
and the other controls in the [engineering handoff](../docs/engineering-handoff.md).
