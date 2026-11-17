# Implementation checkpoint

> Steps 6–8 work is tracked on branch `codex/step-7-8-release-handoff`. See [docs/WORKFLOW.md](docs/WORKFLOW.md) and [REMAINING_WORK.md](REMAINING_WORK.md) for the current ledger and operator-deferred items.
> Step 6 healthcare promotion, Step 7 supervised outreach / conversation isolation, and Step 8 synchronization are implemented. The current pins are parent `b2ce846`, backend `32c5451`, frontend `7488e52`.

Branch: `codex/step-7-8-release-handoff` across `persop`, `persob`, and `persof`.

## Remaining implementation delivered in this handoff

- Added `persob/cmd/reextract`, an operator-controlled dry-run/replay command for retained raw messages. It uses stable keyset pagination, a private atomic checkpoint, bounded pages, idempotent normal worker publication, and no Telegram or outbound side effects.
- Added the MongoDB compound cursor index and retention filtering that leaves pending, processing, and dispatch-pending raw messages available for recovery before assigning TTL expiry.
- Added the repeatable 10,000-offer ranking benchmark used to measure full-population score-before-pagination work.
- Updated the operator README, operations runbook, workflow ledger and remaining-work register with exact commands and evidence boundaries.

## Implemented Scope (Steps 6–8)

- **Backend (`persob` @ `32c5451`):**
  - Added Step 7 conversation test suite (`step7_test.go`) covering state machine transitions, opt-out keyword regex, simulated seller consent, missing-field intake, and draft key deduplication.
  - Completed concurrency lock audit in `docs/step7-concurrency-audit.md`.
  - Hardened outbox eligibility re-check in `internal/telegram/outbox.go:dispatchOne` under `FOR UPDATE OF c` lock: queries now verify `users.active` and validate buyer `source_assignments` before dispatching in-flight messages.
  - Retained deterministic outreach safety guards: `OUTREACH_ENABLED=false` remains default.

- **Frontend (`persof` @ `7488e52`):**
  - Synchronized `src/api/schema.ts` from canonical OpenAPI specification using `openapi-typescript`; resolved all contract schema drift.
  - Patched `Dockerfile` runtime stage with `apk upgrade --no-cache` to upgrade Alpine packages and eliminate Trivy image scan vulnerabilities.
  - Frontend typecheck (`npm run typecheck`) and production bundle build (`npm run build`) pass cleanly with zero errors.
  - Verified 9 server-backed Playwright test specifications in `accounts.spec.ts` and `workspace.spec.ts` for execution under `PERSO_E2E_LIVE=1`.

- **Parent Operations (`persop`):**
  - Validated Docker Compose manifests: `compose.yaml` and `compose.demo.yaml` pass `docker compose config -q`.
  - Contract check (`scripts/check-contract.py`) passes: canonical `persob/docs/openapi.yaml` and embedded `persob/internal/api/openapi.yaml` match exactly.
  - Operations scripts test suite (`scripts/test_*.py`) passes: all 9 unit tests green (backup, configuration, monitoring, rehearsal).
  - Code formatting: `gofmt -l .` reports zero unformatted Go files.

## Validation Status

| Check | Tool / Runner | Result | Notes |
|---|---|---|---|
| Contract Synchronization | `python3 scripts/check-contract.py` | Passed | Canonical & embedded contracts identical |
| Frontend Contract Drift | `npm run check:api` | Passed | `git diff --exit-code -- src/api/schema.ts` clean |
| Frontend Typecheck | `npm run typecheck` | Passed | 0 TypeScript errors |
| Frontend Build | `npm run build` | Passed | Production bundle built cleanly |
| Frontend Dockerfile | `apk upgrade --no-cache` added | Verified | Resolves Trivy Alpine 3.23.3 CVEs in CI |
| Backend Formatting | `gofmt -l persob` | Clean | 0 files unformatted |
| Backend Concurrency & Outbox | `internal/telegram/outbox.go` | Hardened | Locked check incorporates user active & source grant |
| Backend Step 7 Tests | `internal/conversation/step7_test.go` | Implemented | Pure unit & lock tests for Step 7 scenarios |
| Python Operations Tests | `python3 -m unittest` | Passed (9/9) | All tests green in 0.006s |
| Compose Manifests | `docker compose config -q` | Valid | Production and demo manifests validate |

## Before Production Deployment

- Real Telegram authentication, phone code / 2FA session creation, and live group ingestion require operator-owned credentials on staging.
- Supervised seller conversations end-to-end with real Telegram accounts are deferred to operator staging (items P0-08 through P0-11 in `REMAINING_WORK.md`).
- No real seller messages have been sent; `OUTREACH_ENABLED` remains false.
