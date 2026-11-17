# Perso

A Persian-first Telegram marketplace monitor. The live app is healthcare-first and uses the shared healthcare catalog, buyer-scoped marketplace APIs, source assignments, and role-aware account settings. The explicit `?mode=demo` route remains a separate synthetic preview; the normal route never falls back to sample fixtures.

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

Open http://localhost:3000. Sign in using `BOOTSTRAP_ADMIN_USERNAME` and `BOOTSTRAP_ADMIN_PASSWORD` from your private `.env`. The demo is explicitly synthetic: the mock Telegram gateway and healthcare seed fixture are labeled as sample data in the workspace. Never use the demo initialization override with valuable or production volumes. The preview at `?mode=demo` uses independent browser fixtures and never acts as an API failure fallback.

## Real account

Generate `.env` without `--demo` and fill `TELEGRAM_APP_ID`, `TELEGRAM_APP_HASH`, and `TELEGRAM_PHONE_NUMBER` from your own Telegram application. Retain the generated random session key.

```sh
python3 scripts/setup-env.py
docker compose up -d postgres mongodb redis migrate backend-api frontend
docker compose run --rm -it telegram-gateway login
docker compose up -d telegram-gateway message-worker
```

Enter the sign-in code and optional 2FA password in the terminal. Stop the gateway before repeating login; the session has an exclusive file lock. The gateway owns the only connected session; API and worker processes do not create sessions. Add an authorized Telegram source in the live app. Initial history is bounded by `TELEGRAM_BACKFILL_LIMIT` (100 by default, maximum 1000). Recovery scans preserve their separate history cursor when a gap exceeds that bound; check gateway logs and raise the bound intentionally.

The frontend binds to loopback. Put an HTTPS reverse proxy in front of it for remote use; do not expose the gateway or databases. Browser access uses individual password accounts and revocable sessions. `API_TOKEN` is restricted to aggregate monitoring; it cannot authenticate a user. See [account installation and upgrade](persob/docs/identity.md).

## Workflow

1. **Sign in and configure the account.** Use an individual password session, then set language, location, display, and buying preferences.
2. **Choose interests.** Select catalog products and define the filters that determine which offers can match.
3. **Register an accessible source.** Resolve and save a Telegram source; peer type and access are determined by the account-owning gateway.
4. **Collect and preserve messages.** The collector stores raw messages and source revisions in MongoDB so replay and recovery remain possible.
5. **Dispatch reliable work.** Immutable revisions move through Redis, while reconciliation finds messages that were not dispatched successfully.
6. **Extract, match, and persist results.** Workers produce per-item offers and deduplicated matches/history in PostgreSQL. Prices without a clear item association remain unknown.
7. **Review the authorized marketplace.** React loads persisted interests, source status, offers, rankings, and comparisons; ranking happens before pagination and comparison prices use integer Toman.
8. **Run supervised outreach.** A matching seller can produce a review draft. `OUTREACH_ENABLED=false` by default; approval, seller consent, and durable outbox delivery tracking are required before a message is sent.

A successful Telegram send means API acceptance, not a read receipt. Existing source revisions may require re-extraction to recover items collapsed by the old schema. Marketplace reads and matches are scoped to each buyer's current source assignments; administrators manage shared ingestion, and revoking an assignment blocks subsequent buyer reads.

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

The optional Caddy edge obtains and renews HTTPS certificates. Verify the real certificate and authenticated UI before use; configuration validation does not prove public reachability. Keep the `.env` file mode 0600. To rotate monitoring access, replace only `API_TOKEN` and recreate `backend-api`; verify the old machine credential fails on `/api/v1/operations/status`. Change/reset an account password or deactivate it to revoke browser sessions. Do not replace the Telegram session encryption key during either operation.

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
