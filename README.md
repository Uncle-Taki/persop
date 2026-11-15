# Perso

A Persian-first Telegram marketplace monitor. The live app uses the electronics catalog; the healthcare sample UI is an isolated preview at `?mode=demo`. This release supports **one operator workspace and one Telegram account**. It does not implement independent customer accounts.

The parent pins compatible revisions of [persob](https://github.com/Uncle-Taki/persob) (Go) and [persof](https://github.com/Uncle-Taki/persof) (React). Clone with:

```sh
git clone --recurse-submodules https://github.com/Uncle-Taki/persop.git
cd persop
```

## Explicit demo

Requires Docker Compose v2.24+ and Python 3. The `perso-demo` project creates separate named volumes.

```sh
python3 scripts/setup-env.py --demo
make demo
```

Open http://localhost:3000. Enter the `API_TOKEN` from your private `.env`. The header says **Mock connection**; prices come only from synthetic messages. Never use the demo initialization override with valuable or production volumes. The preview at `?mode=demo` uses independent browser fixtures and never acts as an API failure fallback.

## Real account

Generate `.env` without `--demo` and fill `TELEGRAM_APP_ID`, `TELEGRAM_APP_HASH`, and `TELEGRAM_PHONE_NUMBER` from your own Telegram application. Retain the generated random session key.

```sh
python3 scripts/setup-env.py
docker compose up -d postgres mongodb redis migrate backend-api frontend
docker compose run --rm -it telegram-gateway login
docker compose up -d telegram-gateway message-worker
```

Enter the sign-in code and optional 2FA password in the terminal. Stop the gateway before repeating login; the session has an exclusive file lock. The gateway owns the only connected session; API and worker processes do not create sessions. Add an authorized Telegram source in the live app. Initial history is bounded by `TELEGRAM_BACKFILL_LIMIT` (100 by default, maximum 1000). Recovery scans preserve their separate history cursor when a gap exceeds that bound; check gateway logs and raise the bound intentionally.

The frontend binds to loopback. Put an HTTPS reverse proxy in front of it for remote use; do not expose the gateway or databases. `API_TOKEN` is an initial single-operator bearer credential, not a multi-user identity provider. Rotate it in `.env` and recreate the API container to revoke browser access.

## Workflow

1. Select catalog products under **Interests**.
2. Resolve and save an accessible Telegram source. Peer type and access are determined by the account-owning gateway.
3. The collector preserves messages in MongoDB, dispatches immutable revisions through Redis, and reconciles undispatched messages.
4. Workers produce per-item offers and deduplicated matches/history in PostgreSQL. Prices without a clear item association remain unknown.
5. React reads server data. Source status and interests survive reload. Offer ranking precedes pagination; comparison prices use integer Toman (Rial remainders truncate toward zero).
6. Matching identifiable sellers with missing fields can produce a review draft. `OUTREACH_ENABLED=false` by default. Enabling it requires the separate approval in the UI; consent is application-owned, and delivery status comes from the durable outbox.

A successful Telegram send means API acceptance, not a read receipt. Existing source revisions may require re-extraction to recover items collapsed by the old schema. Shared/private source isolation beyond the configured operator is not supported by this release.

## Development and checks

Go 1.26 and Node 24 are used. From the parent:

```sh
make check
cd persof && npm run generate:api && npm test
```

Run the backend on port 8080 and `npm run dev` in `persof`; Vite proxies `/api` to the backend. Follow [persob/docs/operations.md](persob/docs/operations.md) for disposable database acceptance tests, migrations, backups, restore, retention and diagnostics. Follow [IMPLEMENTATION.md](IMPLEMENTATION.md) for scope and verification details.

Normal shutdown (`make down`) preserves volumes. Production configuration contains no demo seeds. Database changes are serialized and recorded with checksums in `schema_migrations`; keep previously applied migration files immutable. The parent deployment runs a dedicated migration step, and application startup also verifies migrations for direct CLI use.

The prioritized verification, pilot preparation and later product backlog is tracked in [REMAINING_WORK.md](REMAINING_WORK.md).

## Publishing changes

Commit/test backend and frontend branches first, then update the parent submodule pointers. CI checks the pinned combination. The dated audit under `audit/2026-11-14` is historical evidence; it does not describe the current build's validation status.

## Pilot configuration and HTTPS

New production environment files receive a random workspace UUID and independent private credentials. Existing files are never overwritten. Check configuration before first login:

```sh
python3 scripts/preflight.py --env-file .env
```

Use `--offline` only to check generated credentials before entering real Telegram values. For a public deployment, set `PERSO_DOMAIN=your-hostname.example` in `.env`, point its DNS to the host and open ports 80/443. Then run:

```sh
python3 scripts/preflight.py --public
docker compose -f compose.yaml -f compose.https.yaml up -d --build
```

The optional Caddy edge obtains and renews HTTPS certificates. Verify the real certificate and authenticated UI before use; configuration validation does not prove public reachability. Keep the `.env` file mode 0600. To rotate API access, generate a new independent `API_TOKEN`, replace only that value and recreate `backend-api`; verify the old token fails and the new one works. Do not replace the session encryption key during ordinary API-token rotation.

## Backup and isolated restore

The backup command quiesces and resumes running gateway, worker and API services around the snapshot. It writes private archives and a checksum manifest into a **new** directory. Encrypt the archives before copying them to off-host storage.

```sh
python3 scripts/backup.py backup --project perso --env-file .env --directory backups/release-001
```

Create the `backups` parent directory with mode 0700 first. For a restore rehearsal, prepare a different Compose project and private environment file, keeping the original `TELEGRAM_SESSION_STORAGE_KEY`. Start only its PostgreSQL, MongoDB and Redis services. Then run:

```sh
python3 scripts/backup.py restore --project perso-restore --env-file .env.restore --directory backups/release-001
```

Restore rejects the source project, running application services, nonempty databases/session volume, mismatched encryption keys, corrupt archives and unsafe session paths. A partial failed restore must be discarded before retrying. The restored gateway stays stopped. Validate counts, migration ledger and API reads before deciding whether to use the restored environment. Never run both copies of a real Telegram session.

## Operator health snapshot

Run the read-only health check on the deployment host and let your existing scheduler/monitoring system alert on a nonzero exit status:

```sh
python3 scripts/monitor.py --project perso --env-file .env --url https://your-hostname.example --backup-manifest backups/release-001/manifest.json
```

The JSON reports queue pending count/age, dead letters, worker heartbeats, Redis data-disk use, outbox failures/age, gateway authorization, authenticated API availability and backup age. Default thresholds are initial operating defaults, not measured service-level guarantees; adjust them for the pilot. Exit status 1 means an alert and 2 means inspection failed. Without a backup manifest, backup health remains an alert. Snapshot output contains aggregate health only, not message text or credentials. Arrange daily review and periodic checks through your own scheduler; no external alert recipients or schedules are created automatically.
