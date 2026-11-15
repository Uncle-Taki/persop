# Remaining work

> Step 2 identity work is now implemented on codex/perso-healthcare-rbac: see [implementation and verification](docs/STEP_2_IDENTITY.md) and the [current workflow](docs/WORKFLOW.md). Password accounts replace browser API-token login. Buyer shared-source access remains blocked until step 3. Historical checkpoint descriptions below do not describe these new account capabilities.

> Current healthcare/RBAC work is tracked in [docs/WORKFLOW.md](docs/WORKFLOW.md), with the [contract map](docs/CONTRACT_MAP.md) and [verified step 1 baseline](docs/STEP_1_BASELINE.md). The electronics/single-operator scope and older pending-test statements below describe the historical checkpoint. Exact-baseline parent integration now passed eight browser tests and the container rehearsal; standalone backend fixture and runtime-image scan failures remain documented. Healthcare, roles, and mock HTTP LLM are planned and are not implemented by this documentation change.

Status snapshot: **2026-11-15**, after publishing `codex/perso-improvements-wip`.

Reviewed baseline: parent `20dd036`, backend `5c468df`, frontend `bd4c811`.
This document records unfinished verification, operational preparation and later scope. It does not claim that those jobs have passed or authorize a production deployment. Check boxes stay open until the completion evidence below is recorded.

## Current position

The implementation is published and reviewable. It includes the server-backed Persian-first UI, reliable message/offer processing, one Telegram gateway, approval and consent checks, a durable outbox, migrations and integration CI. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for completed scope and earlier verification results.

The initial parent integration and backend unit jobs failed because the newly added consent test used an invalid package qualifier. That compile error is fixed in backend `90c655d`; the full local Go 1.26.11 unit suite passes. The initial backend database acceptance job passed with race instrumentation on PostgreSQL 16, MongoDB 7 and Redis 7, and the standalone frontend workflow passed. The parent integration rerun must still verify the final pinned combination and all eight server-backed browser tests. The local race build previously exceeded compiler resources.

Priorities: **P0** blocks a production pilot; **P1** blocks broader unattended use; **P2** is later product scope. Suggested owners identify responsibility, not assigned people. Work in disposable or staging environments unless explicitly stated otherwise.

## P0 — Complete verification and prepare a controlled pilot

| ID | Job | Suggested owner | Completion evidence |
| --- | --- | --- | --- |
| P0-01 | Finish CI for the exact pinned combination and investigate every failure. | Engineering | Link successful parent integration and backend/frontend checks to full commit SHAs. Record test counts and skips; an unfinished run is not a pass. |
| P0-02 | Complete backend unit, race, vet and build checks with Go 1.26.11. Include the latest consent and persistence-retry changes. | Backend | All commands pass on a runner with enough memory. Record runner/toolchain and logs. Resolve compiler/resource failures without dropping race coverage. |
| P0-03 | Rerun database acceptance against PostgreSQL 16, MongoDB 7 and Redis 7. | Backend | Migration upgrade/preservation, concurrent migrations, item/revision deduplication, queue recovery, price normalization, ranking, ownership and persisted intake tests all pass. Earlier local PostgreSQL 18 fixtures do not replace this run. |
| P0-04 | Rerun all eight browser tests against the real isolated backend fixture. | Frontend | All eight pass with `PERSO_E2E_LIVE=1`; interest navigation works with the count badge. Retain report/trace and verify persistence, invalid credentials, API failure, mobile RTL/LTR and accessibility checks. |
| P0-05 | Validate and start the actual container deployment. | Operations + engineering | Compose validation and both application image builds pass. Fresh production configuration has no demo data; the separate demo works. Verify migrations, health checks, API proxy, database authentication, session permissions and volume persistence after restart. |
| P0-06 | Repeat dependency and image vulnerability checks after the Go/dependency updates. | Engineering | Save `govulncheck`, frontend audit and built-image scan results for the exact revisions/images. Resolve release-blocking findings or document a specific reviewed disposition. Earlier scans are not proof that this revision is clear. |
| P0-07 | Rehearse upgrade, backup and full restore. | Operations | Restore PostgreSQL, MongoDB and encrypted session files into an isolated deployment; validate migration ledger, row counts, offers and authenticated reads. Keep the restored session stopped while the original is active. Record recovery time and the rollback procedure. |
| P0-08 | Verify Telegram authorization and ingestion with an operator-owned test account. | Operator + backend | Phone code/2FA, session restart/exclusive ownership, source resolution, groups/channels/forums, edits/deletes, linked discussion mapping, bounded backfill and reconnect recovery work. Exercise FloodWait handling and document recovery when a gap exceeds the configured bound. |
| P0-09 | Verify one explicitly approved test conversation end to end. | Operator + backend | With a consenting test recipient, confirm approval, consent, typed answers, opt-out, terminal state, quiet hours, revoked interest, retries and visible delivery failures. Distinguish API acceptance from read receipts. Keep general outreach disabled until this controlled check is complete. |
| P0-10 | Validate the optional external LLM path before enabling it. | Operator + backend | Verify both global and per-source permission, input limit, shared rate limit, provider errors, deterministic fallback and prompt-injection resistance with permitted test data. Model output cannot approve outreach or grant consent. If unused, keep disabled and record this gate as not applicable to the pilot. |
| P0-11 | Review the pilot deployment configuration. | Operations + operator | Configure HTTPS, unique operator identity, random tokens, session encryption key and restricted internal services. Rehearse token rotation and check that errors/logs do not expose credentials. Record who can approve outreach and operate recovery. |

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
| P1-01 | Establish operational alerts and a daily health view. | Operations | Alert on queue pending age/count, dead letters, Redis disk use, worker heartbeats, gateway authorization, outbox failures and backup age. Exercise a failure and record the response. |
| P1-02 | Benchmark offer ranking and statistics at representative volume. | Backend | Agree latency/memory targets, publish measurements and determine the safe dataset size. If needed, replace full-population API ranking with a maintained scoring projection while preserving ranking-before-pagination. |
| P1-03 | Define and test retention/archive policy. | Operator + operations | Decide raw/history/backup retention and Redis archival boundaries. Verify enabled TTL cleanup on disposable data and prevent trimming unprocessed work. Retention currently defaults to keeping data. |
| P1-04 | Prepare an operator-controlled historical re-extraction job. | Backend + operator | Dry-run retained raw messages, estimate workload and prove resumability/idempotency before recovering items collapsed by the legacy schema. Report unavailable raw history explicitly. |
| P1-05 | Rehearse failure and recovery under sustained load. | Backend + operations | Interrupt workers, gateway and dependencies during processing. Verify recovery without lost raw records, duplicate PostgreSQL effects or silently acknowledged persistence errors; document ambiguous outbound-delivery handling. |
| P1-06 | Complete manual Persian/mobile usability checks. | Frontend + operator | Verify keyboard/focus behavior, screen-reader labels, Persian dates/numbers, long source/product names, slow connections, multiple real offers and small-screen navigation. Record devices and any unresolved issues. Automated accessibility checks alone are insufficient evidence. |
| P1-07 | Make release evidence easy to reproduce. | Engineering | Add repeatable image build/scan checks and retain test reports, image identifiers and rollback notes. Ensure a green standalone frontend check cannot be mistaken for complete full-stack coverage. |

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

### 2026-11-15: Read-only operational monitoring (P1-01)

- Added aggregate JSON monitoring for API/gateway readiness, worker heartbeats, pending queue age/count, dead letters, Redis disk use, outbox failures/age and backup age.
- Alert evaluation tests cover unhealthy queue/backup snapshots and healthy operation. Monitoring returns nonzero on collection failures and never includes secret values or message bodies in its result.
- Remaining operator work: choose thresholds/recipients, connect the command to the deployment scheduler and exercise the installed alert route. No external messages or schedules were created.
