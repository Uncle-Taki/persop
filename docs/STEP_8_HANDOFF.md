# Step 8 integration handoff

Step 8 integrates and verifies the implemented Steps 1–5. It does not complete Step 6 (promote all healthcare prototype screens) or Step 7 (buyer request/approval/consent conversation flow). Production deployment and real Telegram outreach are separate actions.

## Revisions and evidence

Starting parent: `5008b0c332ee1eb6567a978966e73b7ec25d9dbb`; backend: `5c8c7ca3463d0918b88e16e6a4009b6644ba2783`; frontend: `8c8a0bc3c3fcded46a52feaeff80f04aaf69330f`. Work is published on `codex/perso-step-8`; final child pins and CI results are recorded after verification.

Local: exact Go 1.26.11; Node 24.22.1. Frontend API generation, typecheck and production build passed; Python checks and canonical/embedded API check passed. Provider/config/extraction race checks passed. Browser startup is restricted by the local Unix-socket policy. GitHub CI must validate the exact pinned stack, database acceptance, all live browser tests and the Docker rehearsal. Image scan findings are release gates, never disabled to manufacture a pass.

## Isolated healthcare demo

Use a fresh directory and a new Compose project/volumes. Generate private credentials with `python3 scripts/setup-env.py --demo`, then `make demo`. Keep `.env` private. Existing files are preserved; a previous demo file needs an independent random `LLM_MOCK_TOKEN` (64 hex characters). Sign in using its bootstrap username/password. There is no public signup or fixed default password. Create admin/buyer accounts in Settings; assign the synthetic source in Sources to buyers explicitly.

The demo runs canonical migrations first, then a one-shot `demo-seed` service. It loads a synthetic healthcare catalog/source, grants that source permission to the internal mock, and injects a synthetic saline offer. The worker calls `/v1/chat/completions` at the internal `llm-mock` service with its private token. Provider evidence is recorded in MongoDB `llm_extractions`. No real Telegram credentials, external LLM key or seller messages are required. Outreach is forced off for demo gateway/worker. The fixture selector is rejected outside development/test mock mode.

The release rehearsal requires the healthcare offer, a successful persisted HTTP-provider extraction, no outbound messages, restart persistence, session/password and monitoring-token revocation, and isolated PostgreSQL/Mongo/encrypted-session restore. An offer produced solely by deterministic fallback cannot pass the mock check. The original and restored Telegram sessions are never run together.

## Upgrade and recovery

Back up the existing deployment using `scripts/backup.py` as described in the README. Preserve OPERATOR_USER_ID and TELEGRAM_SESSION_STORAGE_KEY. Do not add demo overrides or seed files to production. Build the pinned images, run `docker compose run --rm backend-api migrate`, then recreate the application services. Migrations 001–006 are immutable and verified by checksum. Duplicate legacy normalized peers stop migration 005; resolve them explicitly with history preserved. No source access is granted to new buyers automatically.

Source assignment replaces an administrator's complete selection using the current version; stale writes return 409. Removing/re-adding a source does not restore its former grants. Browser sessions are revoked by password/role/status changes. API_TOKEN authenticates aggregate monitoring only. New provider configuration does not authorize external processing: both LLM_ENABLED and exact-source external permission are required. Keep external providers and outreach disabled for the initial verification.

For rollback, use an isolated restore with the matching code/images and encryption key; there are no destructive down-migrations. Do not run older application code against an upgraded schema as a substitute for a tested restore. Retain private archives off-host with encryption and verify checksums/counts before switching environments.

## Remaining product boundaries

The default UI is the existing server-backed mint workspace; the full healthcare prototype remains explicit at `?mode=demo`. The session catalog label is still electronics even though healthcare catalog fields/CRUD are implemented. Healthcare unit/specification/expiry compatibility needs additional product work; this handoff does not certify clinical product equivalence. The new buyer inquiry workflow remains Step 7. Existing supervised operator outreach stays disabled during verification. Public hosting, real Telegram authorization/reconnect and production provider checks require a separate operator-controlled pilot.
