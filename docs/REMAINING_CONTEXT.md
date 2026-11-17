# Perso remaining-work context

Updated: 2026-11-17, Asia/Tehran

This is the compact handoff for the next implementation or review session. It is grounded in the current checked-out branch and source tree; historical workflow entries may describe earlier candidates and must not override the current pins below.

## Current checkout

- Parent repository: branch `codex/step-7-8-release-handoff`, commit `7785809`.
- Backend submodule: `persob/main`, commit `bd0093578aa6ddb7beba5bcdf0588e55d4a57af8`.
- Frontend submodule: `persof/main`, commit `db56d41bc164c752f0c3c2871ad397776996d0e0`.
- Parent gitlinks point to backend `bd00935` and frontend `db56d41`.
- The backend worktree has an uncommitted two-line test-fixture edit in `internal/conversation/step7_test.go` (`بله حتماً` and `بپرسید`). The parent reports the backend gitlink as dirty because of that edit. Preserve it and decide explicitly whether to commit or revert it before the next publication.

## What is implemented

### Step 6 — healthcare live workspace

The live entrypoint is `persof/src/App.tsx` → `persof/src/live/LiveApp.tsx`. It uses the typed API client for session, products, interests, sources, offers, statistics, gateway status, users, and conversations. The Step 6 child change is in the current frontend ancestry at `c261d3e`; the current `db56d41` adds the later contract and runtime-image corrections.

Backend healthcare identity and session contract changes are present in the current backend ancestry. Demo fixtures are healthcare-oriented and the OpenAI-compatible mock is wired through Compose.

Review limitation: `persof/src/DemoApp.tsx` and prototype page files still contain synthetic sample content. They are not the default `App.tsx` path, but the next reviewer must verify that no normal live flow silently falls back to them. Product, offer, source-detail, and conversation UI should be checked against the backend response shapes and role matrix, not just visual labels.

### Step 7 — supervised buyer conversations

Backend entry points:

- `persob/internal/conversation/manager.go`
- `persob/internal/conversation/state_machine.go`
- `persob/internal/api/handlers/conversation.go`
- `persob/internal/telegram/outbox.go`
- `persob/internal/conversation/step7_test.go`

Implemented behavior includes buyer-owned drafts, administrator approval recorded separately from the buyer owner, current buyer/source-grant/interest eligibility checks, seller opt-out detection, simulated consent, missing-field intake, deduplication keys, pause/close actions, and locked outbox revalidation against account deactivation and source revocation.

Frontend entry points:

- `persof/src/api/client.ts` conversation methods
- `persof/src/live/LiveApp.tsx` conversation list/detail/actions
- `persof/src/api/schema.ts` conversation contracts

The backend hard-blocks outreach when `OUTREACH_ENABLED=false`; demo-auth and unconfigured Telegram mock mode fail closed before outbound delivery.

### Step 8 — synchronized handoff

Current evidence recorded in `docs/WORKFLOW.md`, `IMPLEMENTATION.md`, and `REMAINING_WORK.md` includes:

- canonical/embedded OpenAPI synchronization;
- frontend API schema generation and drift check;
- frontend typecheck and production build;
- backend formatting, race/vet/build and audit evidence on the published candidate;
- nine Python operations tests;
- Compose manifest validation;
- runtime-image and dependency remediation commits.

Treat CI claims as evidence for the named commit only. Re-run checks when the dirty test fixture or any source changes are included in a new candidate.

## Remaining gates

These are the actual remaining gates for a controlled pilot. They require operator-owned staging resources and must stay outside automatic demo execution:

1. **P0-08 — Telegram authorization and ingestion:** an operator-owned test account, phone/2FA session creation, source resolution, and one synthetic/approved ingestion run.
2. **P0-09 — approved conversation:** one explicitly consented test recipient through approval → consent → missing-field intake → persisted update. Keep real outreach disabled until the operator authorizes this staging run.
3. **P0-10 — external LLM path:** validate the optional provider with an operator-supplied key, bounded timeout/retry behavior, malformed output handling, and no credential exposure. The local HTTP mock already covers demo mode.
4. **P0-11 — pilot configuration review:** operator domain/TLS, bootstrap secrets, secure cookies, monitoring token rotation, backup destination, restore procedure, and rollback notes.
5. **P1-06 — manual Persian/mobile review:** keyboard focus, screen-reader labels, Persian dates/numbers, long names, slow connections, responsive navigation, and real offer density on a small-screen device.
6. **P1-01/P1-02/P1-03/P1-04/P1-05/P1-07:** unattended-operation alerts, ranking benchmarks, retention policy, resumable historical re-extraction, failure/recovery rehearsal, and reproducible image/security evidence.

## Next review sequence

1. Reconcile the top-level status and stale historical wording in `docs/WORKFLOW.md`; retain history but mark the current Step 6/7/8 status from the pins above.
2. Resolve the dirty `step7_test.go` edit deliberately and run `gofmt -l .` plus the focused conversation tests.
3. Run the exact pinned-stack checks from a clean disposable environment: backend unit/race/vet/build, audit acceptance, frontend `npm run check:api`, typecheck, build, and server-backed Playwright with `PERSO_E2E_LIVE=1`.
4. Validate demo boot with `docker compose -p perso-demo -f compose.yaml -f compose.demo.yaml up -d --build`; use an alternate `FRONTEND_PORT` only when the host's port 3000 is occupied.
5. Keep `OUTREACH_ENABLED=false`, avoid real credentials, and report every skipped or blocked operator gate separately.

## Do not infer

- A passing frontend Playwright command with skipped live tests is not server-backed buyer/conversation evidence.
- Pure unit tests for consent and locking are not proof of a real Telegram delivery.
- Compose configuration validation is not proof that a production deployment or real external LLM works.
- A synthetic demo conversation does not authorize contacting a real seller.
