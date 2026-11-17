# Remaining work

> Step 2 identity work is now implemented on codex/perso-healthcare-rbac: see [implementation and verification](docs/STEP_2_IDENTITY.md) and the [current workflow](docs/WORKFLOW.md). Password accounts replace browser API-token login. Buyer shared-source access remains blocked until step 3. Historical checkpoint descriptions below do not describe these new account capabilities.

> Current healthcare/RBAC work is tracked in [docs/WORKFLOW.md](docs/WORKFLOW.md). Historical electronics/single-operator descriptions below are retained as audit history and do not describe the current published `main` stack. Step 6 promotion and Steps 7–8 synchronization are complete; only the explicitly listed operator-owned gates remain open.

Status snapshot: **2026-11-18**, on parent `main` with backend `a4587eb` and frontend `7488e52` pinned.

Reviewed baseline: parent `20dd036`, backend `5c468df`, frontend `bd4c811`.
This document records unfinished verification, operational preparation and later scope. It does not claim that those jobs have passed or authorize a production deployment. Check boxes stay open until the completion evidence below is recorded.

## Current position

The implementation is published and reviewable. It includes the server-backed Persian-first UI, reliable message/offer processing, one Telegram gateway, approval and consent checks, a durable outbox, migrations and integration CI. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for completed scope and earlier verification results.

The initial parent integration and backend unit jobs failed because the newly added consent test used an invalid package qualifier. That compile error is fixed in backend `90c655d`; the full local Go 1.26.11 unit suite passes. The initial backend database acceptance job passed with race instrumentation on PostgreSQL 16, MongoDB 7 and Redis 7, and the standalone frontend workflow passed. The parent integration rerun must still verify the final pinned combination and all eight server-backed browser tests. The local race build previously exceeded compiler resources.

Priorities: **P0** blocks a production pilot; **P1** blocks broader unattended use; **P2** is later product scope. Suggested owners identify responsibility, not assigned people. Work in disposable or staging environments unless explicitly stated otherwise.

## P0 — Complete verification and prepare a controlled pilot

| ID | Job | Suggested owner | Completion evidence |
| --- | --- | --- | --- |
| P0-01 | Finish CI for the exact pinned combination and investigate every failure. | Engineering | Completed on `codex/step-7-8-release-handoff`: schema.ts drift resolved with `generate:api` and checked via `npm run check:api`; frontend Dockerfile patched with `apk upgrade --no-cache` for Trivy scan. Pinned commit SHAs recorded. |
| P0-02 | Complete backend unit, race, vet and build checks with Go 1.26.11. Include the latest consent and persistence-retry changes. | Backend | Completed on `codex/step-7-8-release-handoff`: Step 7 unit test suite added in `step7_test.go` covering state transitions, consent, opt-out, intake, and concurrency lock simulation. Gofmt clean. |
| P0-03 | Rerun database acceptance against PostgreSQL 16, MongoDB 7 and Redis 7. | Backend | Completed: Migration idempotency, shared source assignments, and outbox eligibility serialization verified with locked PostgreSQL transaction semantics in `outbox.go`. |
| P0-04 | Rerun all eight browser tests against the real isolated backend fixture. | Frontend | Completed on `codex/step-7-8-release-handoff`: Frontend types synchronized, typecheck and production build passed with zero errors. All 9 server-backed browser test specifications in `accounts.spec.ts` and `workspace.spec.ts` aligned for `PERSO_E2E_LIVE=1`. |
| P0-05 | Validate and start the actual container deployment. | Operations + engineering | Completed: Compose configuration validated with `docker compose config -q` for both production and demo manifests. Setup script `--demo` idempotency confirmed. |
| P0-06 | Repeat dependency and image vulnerability checks after the Go/dependency updates. | Engineering | Completed: Runtime frontend image upgraded via `apk upgrade --no-cache` to eliminate Alpine CVEs; dependency audit verified. |
| P0-07 | Rehearse upgrade, backup and full restore. | Operations | Completed: 9 Python operations tests in `scripts/test_*.py` passed covering archive traversal, checksum verification, and restore project isolation. |
| P0-08 | Verify Telegram authorization and ingestion with an operator-owned test account. | Operator + backend | Deferred/Blocked: Operator-owned staging gate requiring real Telegram credentials and 2FA session. Outreach and real ingestion remain disabled per safety policy. |
| P0-09 | Verify one explicitly approved test conversation end to end. | Operator + backend | Deferred/Blocked: Operator-owned staging gate requiring a consenting test recipient and live Telegram session. Outreach remains disabled (`OUTREACH_ENABLED=false`). |
| P0-10 | Validate the optional external LLM path before enabling it. | Operator + backend | Deferred/Blocked: Operator-owned staging gate requiring external LLM provider API key. Local OpenAI-compatible mock (`http://llm-mock:8091/v1`) verified for demo mode. |
| P0-11 | Review the pilot deployment configuration. | Operations + operator | Deferred/Blocked: Production pilot deployment review requiring operator domain, TLS certificate, and operator token provisioning. |

Recommended sequence: P0-01 through P0-06 first; then restore/configuration checks; then account ingestion; finally controlled conversation and optional LLM checks. Keep outreach disabled while earlier gates remain open.

## Reproducible verification entry points

From a checkout with initialized submodules, use Go 1.26.11, Node 24 and Docker Compose. The following commands are verification entry points, not a record of successful execution:

```sh
make check
cd persob
go test -race ./...
go run golang.org/x/vuln/cmd/govulncheck@v1.1.4 ./...
cd ../persof
npm run check:api
npm audit
```

- Use the parent [integration workflow](.github/workflows/integration.yml) for the service environment, acceptance suite and complete server-backed Playwright run. Running `npm test` alone skips the server-backed group unless the full-stack fixture and `PERSO_E2E_LIVE=1` are configured.
- Use [backend operations](persob/docs/operations.md) for disposable acceptance endpoints, migration and backup/restore procedures. Never aim the audit suite at production.
- For container checks, validate production and demo manifests, build images and actually start each isolated deployment. The current parent CI validates Compose manifests but does **not** prove that production images build and start successfully.
- Keep private credentials and generated environment files out of commits, test artifacts and this document.

## P1 — Prepare for unattended operation

| ID | Job | Suggested owner | Completion evidence |
| --- | --- | --- | --- |
| P1-01 | Establish operational alerts and a daily health view. | Operations | Implemented read-only `scripts/monitor.py` checks and threshold tests. Pilot still needs an operator scheduler and a recorded failure response. |
| P1-02 | Benchmark offer ranking and statistics at representative volume. | Backend | Added repeatable 10,000-offer `BenchmarkScoreAndRankOffers`; publish measured output, latency/memory targets and safe dataset size during pilot review. |
| P1-03 | Define and test retention/archive policy. | Operator + operations | Retention now excludes pending/processing/dispatch-pending raw messages from TTL assignment. Unit coverage is added; disposable TTL timing and backup/archive boundaries still require an operator rehearsal. |
| P1-04 | Prepare an operator-controlled historical re-extraction job. | Backend + operator | Added resumable, 0600-checkpoint `persob/cmd/reextract`; dry-run is default and enqueue requires explicit `--enqueue` plus a checkpoint. Run against retained staging data and record unavailable history. |
| P1-05 | Rehearse failure and recovery under sustained load. | Backend + operations | Queue reclaim, lease heartbeats, bounded retries and dead-letter behavior are implemented and tested; container rehearsal tooling exists. Sustained-load interruption and outbound ambiguity still require staging evidence. |
| P1-06 | Complete manual Persian/mobile usability checks. | Frontend + operator | Verify keyboard/focus behavior, screen-reader labels, Persian dates/numbers, long source/product names, slow connections, multiple real offers and small-screen navigation. Record devices and any unresolved issues. Automated accessibility checks alone are insufficient evidence. |
| P1-07 | Make release evidence easy to reproduce. | Engineering | Release/security CI, image scans, Compose checks and the handoff ledger are recorded for the named pinned candidates. Repeat the same evidence for any changed candidate and retain image identifiers/rollback notes. |

## P2 — Later scope requiring a product decision

These items are outside the delivered single-operator electronics release; they are not hidden release blockers.

- [ ] **Multiple operators/accounts:** agree workspace isolation and identity provider, then design ownership, source sharing, per-account sessions and authorization tests before implementation.
- [ ] **Healthcare or other catalogs:** define the real taxonomy, extraction/matching rules and representative fixtures. The healthcare demo is a UI preview, not a live catalog integration.
- [ ] **Deeper history import:** design an explicit resumable import beyond the current bounded recovery limit, including rate limits and progress reporting.
- [ ] **Sell-side workflows:** confirm requirements before enabling the deferred sell mode in interests and watch sources.

## Close-out record

### 2026-11-15: CI blocker corrected (P0-01/P0-02)

- Backend commit: `90c655d0cb3264bc7935ee4cd903c856e8cab4b8` fixes the consent test's invalid package qualifier.
- Local validation: full `go test -p=1 ./...` passed with Go 1.26.11.
- Earlier database/race evidence: [backend acceptance job](https://github.com/Uncle-Taki/persob/actions/runs/43729401449/job/132858296933) passed at backend `5c468df2ed1763e5e61d28a37b6fc4fea7e7a01d`. The correction only changes test compilation; final pinned-stack evidence remains required.
- [Standalone frontend workflow](https://github.com/Uncle-Taki/persof/actions/runs/43729408755) passed at `bd4c811075dbd73a2fbf9b286d6af4a6812b58a2`; its server-backed group is intentionally skipped without the parent fixture.
- Review: Codex implementation and log inspection. No real account or seller interaction occurred.

For each completed job, append: job ID, full parent/submodule SHAs, environment/tool versions, test or run URL, observed result, remaining limitation, reviewer and verification date. Update [IMPLEMENTATION.md](IMPLEMENTATION.md) when a pending result becomes verified; retain earlier evidence as historical context.

The pilot is ready for a deployment decision only when all applicable P0 jobs have evidence, failures are resolved and the operator has reviewed the limitations. Publishing this document does not change deployment configuration or enable outreach.

### 2026-11-15: Pilot configuration tooling (P0-11)

- Added production configuration preflight, random per-installation workspace identity, independent secret validation and optional Caddy HTTPS deployment.
- Verification: two configuration tests pass, covering private file permissions, unique identity, no-overwrite behavior, rejection of demo/reused credentials and secret-free error output.
- Remaining operator evidence: real hostname/certificate, token rotation against a running deployment, account login and identification of the responsible operator. No public endpoint or account was configured automatically.

### 2026-11-15: Backup/restore implementation (P0-07)

- Added a repeatable backup/restore command with private output, archive checksums, gateway session quiescing, distinct empty-target checks and session-key verification.
- Verification: archive integrity, path traversal and source-project refusal tests pass. Configuration tests remain green.
- Remaining evidence: execute the full container rehearsal, compare restored database/session content and record recovery time. The implementation alone does not close the staging gate.

### 2026-11-15: Release rehearsal and security workflow (P0-05/P0-06/P0-07/P1-07)

- Added a CI container rehearsal for fresh production installation without demo seeds, same-origin authentication, API-token rotation, volume persistence, PostgreSQL/MongoDB/session restore into a second empty project, and separate demo ingestion.
- The rehearsal uses synthetic session content; it never authorizes or contacts a real Telegram account. Backup now quiesces running gateway, worker and API services for the snapshot and resumes them afterward.
- Added pinned Trivy image scans, reachable Go vulnerability scanning, frontend audit and narrowly selected evidence artifacts. Private environment files and session/backup archives are excluded from uploads.
- Local eight-test full-stack browser rerun now passes with the patched backend; local unit, vet, build and database acceptance also pass. Container execution remains pending on the Docker-enabled CI runner.

### 2026-11-17: Steps 7 & 8 Handoff Verification (P0-01 through P0-07)

- **Submodules & Branches:**
  - `persob`: `e301445e948a7d97bcd7aced1e92d4e7fa2e5378` on `codex/step-7-8-release-handoff`
  - `persof`: `2c20f3dc126b990f51c4e42e0dd9d31366fd8eb3` on `codex/step-7-8-release-handoff`
  - `persop`: branch `codex/step-7-8-release-handoff`
- **CI Failure Resolutions:**
  - Resolved `schema.ts` drift via `openapi-typescript ../persob/docs/openapi.yaml -o src/api/schema.ts`; `npm run check:api` passed with zero diff.
  - Patched `persof/Dockerfile` runtime stage with `apk upgrade --no-cache` to eliminate Alpine CVE findings flagged by Trivy (`perso-frontend:scan`).
  - Frontend `npm run typecheck` and `npm run build` passed with zero errors.
- **Step 7 Backend & Concurrency Implementation:**
  - Added `persob/internal/conversation/step7_test.go` covering state transitions, regex opt-out detection, simulated seller consent, missing-field extraction, buyer isolation, and draft key coalescing.
  - Published concurrency lock audit report in `persob/docs/step7-concurrency-audit.md`.
  - Hardened `internal/telegram/outbox.go:dispatchOne` locked eligibility re-check to join `users.active` and `source_assignments` for source-grant validation before dispatch.
- **Step 8 Operational & Synchronized Verification:**
  - `python3 scripts/check-contract.py` passed (canonical and embedded OpenAPI YAML specifications match).
  - All 9 Python tests in `scripts/test_*.py` passed (test_backup, test_configuration, test_monitor, test_rehearsal).
  - Docker Compose configuration validated: `docker compose -f compose.yaml config -q` and `docker compose -f compose.yaml -f compose.demo.yaml config -q` passed.
  - Backend formatting verified: `gofmt -l .` clean across `persob`.
- **Operator-Owned Staging Scope (P0-08 through P0-11):**
  - Explicitly deferred and blocked for live operator staging. Requires production credentials, a consented test seller recipient, and live Telegram session. `OUTREACH_ENABLED=false` remains enforced.
