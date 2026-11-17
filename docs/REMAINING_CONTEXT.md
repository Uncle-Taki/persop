# Perso remaining-work context

Updated: 2026-11-18, Asia/Tehran

This is the compact handoff for the next implementation or review session. It is grounded in the current checked-out branch and source tree; historical workflow entries may describe earlier candidates and must not override the current pins below.

## Current checkout

- Parent repository: branch `codex/step-7-8-release-handoff` at the commit containing this handoff.
- Backend submodule: `persob/main`, commit `32c54516ca3ad14f6d0dd3302a9004b87e21bab5`.
- Frontend submodule: `persof/main`, commit `7488e528a57c592a611196528f4b152b3946d6d9`.
- Parent gitlinks point to backend `32c5451` and frontend `7488e52`.
- Parent, backend, and frontend worktrees are clean.

## What is implemented

### Step 6 — healthcare live workspace

The live entrypoint is `persof/src/App.tsx` → `persof/src/live/LiveApp.tsx`. It uses the typed API client for session, products, interests, sources, offers, statistics, gateway status, users, and conversations. The Step 6 child change is in the current frontend ancestry at `c261d3e`; the current `7488e52` adds contract, runtime-image, and live-browser selector corrections.

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
- release/security rehearsal CI passing, including Trivy scans and dependency audits;
- healthcare mock mode scoped to the live browser integration step;
- aligned live browser tab selectors and consent/config fixture corrections.

Treat CI claims as evidence for the named commit only. Re-run checks when the dirty test fixture or any source changes are included in a new candidate.

## Remaining gates

These are the actual remaining gates for a controlled pilot. They require operator-owned staging resources and must stay outside automatic demo execution:

1. **P0-08 — Telegram authorization and ingestion:** an operator-owned test account, phone/2FA session creation, source resolution, and one synthetic/approved ingestion run.
2. **P0-09 — approved conversation:** one explicitly consented test recipient through approval → consent → missing-field intake → persisted update. Keep real outreach disabled until the operator authorizes this staging run.
3. **P0-10 — external LLM path:** validate the optional provider with an operator-supplied key, bounded timeout/retry behavior, malformed output handling, and no credential exposure. The local HTTP mock already covers demo mode.
4. **P0-11 — pilot configuration review:** operator domain/TLS, bootstrap secrets, secure cookies, monitoring token rotation, backup destination, restore procedure, and rollback notes.
5. **P1-06 — manual Persian/mobile review:** keyboard focus, screen-reader labels, Persian dates/numbers, long names, slow connections, responsive navigation, and real offer density on a small-screen device.
6. **P1-01/P1-02/P1-03/P1-04/P1-05/P1-07:** repository tooling is implemented for monitoring, ranking measurement, safe retention assignment, resumable historical replay, queue recovery and release evidence. Operator scheduler setup, measured pilot targets, disposable TTL timing, retained-history replay, sustained-load interruption and repeatable staging evidence remain open.

## Next review sequence

1. Reconcile the top-level status and stale historical wording in `docs/WORKFLOW.md`; the current pins and CI ledger now supersede older Step 6/7/8 checkpoint prose.
2. Re-run the exact pinned-stack checks if source changes are made: backend unit/race/vet/build and audit acceptance, frontend `npm run check:api`, typecheck, build, and server-backed Playwright with `PERSO_E2E_LIVE=1`.
3. Validate demo boot with `docker compose -p perso-demo -f compose.yaml -f compose.demo.yaml up -d --build`; use an alternate `FRONTEND_PORT` only when the host's port 3000 is occupied.
4. Keep `OUTREACH_ENABLED=false`, avoid real credentials, and report every skipped or blocked operator gate separately.

## Current implementation pass

The repository-owned follow-up tooling is now implemented in the current worktree:

- `persob/cmd/reextract` provides a dry-run by default and an explicit checkpointed Redis replay path for retained raw messages.
- MongoDB retention assignment excludes pending, processing, and dispatch-pending raw messages; the cursor index supports bounded keyset scans.
- `persob/internal/analytics/benchmark_test.go` provides a repeatable 10,000-offer ranking benchmark.
- The README, operations runbook, workflow ledger and remaining-work register now distinguish implemented tooling from staging evidence still required.

Verification from an isolated copy with Go 1.26.8 and a writable temporary build cache: `go test -run '^$' ./...` passed; targeted tests for `cmd/reextract`, MongoDB retention and analytics passed; the ranking benchmark measured 21.27 ms/op and 20.25 MB/op for 10,000 offers on the local 12th Gen Intel(R) Core(TM) i5-12500H. Canonical Go 1.26.11 execution remains blocked by the local read-only toolchain cache, so this is compile/test evidence from the temporary copy rather than the canonical checkout.

## Do not infer

- A passing frontend Playwright command with skipped live tests is not server-backed buyer/conversation evidence.
- Pure unit tests for consent and locking are not proof of a real Telegram delivery.
- Compose configuration validation is not proof that a production deployment or real external LLM works.
- A synthetic demo conversation does not authorize contacting a real seller.
