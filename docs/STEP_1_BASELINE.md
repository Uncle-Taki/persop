# Step 1 baseline and verification

Reviewed: 2026-11-15, Asia/Tehran. Scope: branch setup and documentation only. No application behavior, migration, API schema, runtime configuration, seed, or submodule content changes.

## Exact starting point

| Repository | Branch base commit | Git tree |
| --- | --- | --- |
| persop | e17d5eb512b05570084edfd60b443e3a1a5d8a8a | bdfe99c21da254692e8e0c7d0e389ddca1520374 |
| persob | 33aac438d760d0d293e907cf8892775bbaeca222 | 76af22b59c86657fa175daf372bbed01af7d57fd |
| persof | 9cb867d5cffbd529aaff12ea6485a28da693bc21 | 50b05b1f9d46fb65d04df70b87b80182bb1b9ec6 |

GitHub main refs, Git commit metadata and recursive trees were read again. A fresh recursive checkout confirms the parent's persob/persof gitlinks equal the commits above. No AGENTS.md exists in the three tracked trees; no applicable ancestor AGENTS.md was found in the checkout environment. The proposed branch codex/perso-healthcare-rbac was absent in all three remote branch inventories before this work. Local feature branches start at these exact commits.

Submodules have no new content commits in step 1. Publishing their feature branches at the verified base prepares subsequent work; the parent continues to pin the same compatible code. Existing branches/main and existing migration files are preserved.

## Fresh local checks

| Check | Observed result | Notes |
| --- | --- | --- |
| Recursive Git checkout and git submodule status | Passed | Exact base/pins above; initial working trees clean |
| python3 scripts/check-contract.py | Passed | Canonical and embedded backend OpenAPI bytes match |
| python3 -m unittest discover -s scripts -p 'test_*.py' | Passed: 7 tests | Existing configuration/backup/monitor tests; no container execution |
| npm ci --ignore-scripts --no-audit --no-fund | Passed: 100 packages | Existing lockfile unchanged; lifecycle scripts deliberately not invoked |
| npm run check:api | Passed | Generated schema unchanged from baseline |
| npm run typecheck | Passed | TypeScript noEmit |
| npm run build | Passed | Production build; ignored dist output only |
| Full local Go unit/race/vet/build | Not run | No usable Go language toolchain; /usr/bin/go is not the Go compiler (go version returns Unknown option); no gofmt available |
| Local container/DB/browser integration | Not run | Docker unavailable; no local disposable full stack. Verified exact-baseline CI evidence below instead |

Environment: Git 2.52.0, Node v24.22.1, npm 11.9.0, Python 3.12.14. Npm emits an existing environment http-proxy configuration warning; install, generated contract, typecheck and build still exit 0. No package/lockfile update was made. These are baseline checks, not evidence that future roles/healthcare/mock features already work.

## CI evidence for exact baseline commits

The following existing runs were retrieved and their jobs inspected during step 1. They were not newly triggered by these local checks.

| Exact baseline | Evidence | Observed conclusion |
| --- | --- | --- |
| Parent e17d5eb | [Pinned stack integration 43755090757](https://github.com/Uncle-Taki/persop/actions/runs/43755090757) | Success. Job 132937316225 passed backend race/vet/build, disposable DB acceptance, API contract, frontend generated types/typecheck/build, deployment manifest validation and server-backed browser tests. The log explicitly reports 8 passed (7.7s). |
| Parent e17d5eb | [Release/security 43755090769](https://github.com/Uncle-Taki/persop/actions/runs/43755090769) | Failure overall. Dependencies job 132937316479 passed Python tests, reachable Go vulnerability scan and frontend dependency audit. Containers job 132937316745 passed install/demo/persistence/token-rotation/restore rehearsal and image builds, then failed both runtime-image scan steps. |
| Backend 33aac43 | [Backend checks 43754573524](https://github.com/Uncle-Taki/persob/actions/runs/43754573524) | Failure overall. Acceptance job 132935738826 passed. Unit job 132935739001 passed formatting, then queue tests failed to connect to Redis at 127.0.0.1:56389; subsequent vet/build/contract steps were skipped. |
| Frontend 9cb867d | [Frontend checks 43754791608](https://github.com/Uncle-Taki/persof/actions/runs/43754791608) | Success. Install/typecheck/build/standalone Playwright passed. Its server-backed group is conditional and this standalone run must not be represented as all eight full-stack checks. |

These results supersede older claims that the exact parent baseline still awaits its first eight-test browser rerun or first container rehearsal. They do not close real Telegram or seller verification, runtime-image findings, future migration checks, or the new healthcare implementation.

## Pre-existing issues and future check requirements

| ID | Baseline issue | Evidence / interpretation | Follow-up |
| --- | --- | --- | --- |
| BASE-01 | Standalone backend unit workflow lacks the Redis fixture used by queue tests | .github/workflows/check.yml unit job declares no services; its log reports Redis connection refusal. Parent integration provides the service and passes at the same backend revision. This is a test-environment failure, not a new role/healthcare regression. | Provision the declared disposable dependency when running the full backend suite; do not skip queue coverage or label the standalone run green. Keep the failure visible until corrected in an authorized implementation slice. |
| BASE-02 | Both runtime-image scans fail | Release run/step outcomes and container-job logs confirm scanner exits 1. Detailed finding JSON is in the workflow's container-release-evidence artifact; individual findings have not been assessed in step 1. | Review exact findings and rebuild/rescan before a production release. Do not invent a CVE list or suppress scanner failures to obtain a passing badge. |
| BASE-03 | Existing UI/contract shape mismatch on non-default offer sorting | client.ts expects ScoredOffer[] for every sort; handlers/offer.go can return plain Offer[] without with_scores. | Resolve alongside healthcare offer contracts in step 4/6 and exercise every UI sort. No behavior change in this documentation checkpoint. |
| BASE-04 | Single configured owner is embedded in auth, worker filtering and analytics assumptions | middleware, worker processor, offer/source repositories and conversation manager reviewed | Implement actual ownership/grants and endpoint/job authorization in steps 2/3, before multiple buyers access the app. Role labels alone are insufficient. |

## Step 1 completion checks

- [x] Re-read the attached workflow and actual main refs/pins.
- [x] Check applicable repository/ancestor instructions and branch-name availability.
- [x] Create local feature branches in the parent and both submodules.
- [x] Record fresh local checks separately from existing CI evidence and pre-existing failures.
- [x] Map all 11 prototype screens, controls, endpoint gaps, ownership decisions and all 131 properties across seven exported prototype interfaces in [CONTRACT_MAP.md](CONTRACT_MAP.md).
- [x] Add the canonical [WORKFLOW.md](WORKFLOW.md) before feature implementation and link historical status documents to the new plan/evidence.
- [x] Publish/verify remote feature refs and the documentation checkpoint; see the workflow push ledger and final commit/branch links. Parent a4ec4d8f23404f8bddb4f3d56f13dcbc1567f8ae and both baseline submodule feature refs were subsequently verified; step 2 publication is separate.

The next application step is step 2: accounts, sessions, exact roles, personal settings and a minimal role-aware account UI. No step 2 work is included here.
