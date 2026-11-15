# Step 2 — password accounts, roles and customization

Branch: codex/perso-healthcare-rbac in persop, persob and persof.
Scope: accounts/sessions/roles/profile/preferences/minimal account UI. Source assignments, healthcare catalog/extraction, the mock HTTP LLM and the prototype promotion remain later steps. No deployment or real seller communication is included.

## Resulting behavior

- Personal username/password login replaces the shared browser token. Sessions are opaque, PostgreSQL-backed, hashed at rest, expire after 12 hours and use HttpOnly/SameSite=Strict cookies. Production requires Secure cookies/HTTPS. Authenticated mutations require a session-derived CSRF token; JSON login rejects cross-origin browser requests.
- Exactly super_admin, admin and buyer are valid persistent roles. Admins manage buyer accounts; only super admins grant elevated roles. Last-active-super-admin protection is transactional and concurrency-tested.
- Profile, language, preferred city/area, default offer sorting and number display are persisted per user. Language/sort/number display apply to the current UI; location is stored for the later buying filters.
- Settings includes profile/preferences/password forms and role-aware account creation/editing/deactivation/password reset. Password and role/status changes revoke affected sessions. Logout revokes the current session. Every request checks current account status and role.
- Buyer shared-marketplace endpoints fail closed until step 3 establishes source grants and buyer-scoped offers/statistics/conversations. Buyers can use their account, preferences, shared catalog and personal interests now. This avoids exposing the old single-operator data to newly created buyers.
- API_TOKEN is confined to aggregate GET /api/v1/operations/status. It cannot establish an account session or read/change marketplace/user data. Monitoring uses that route plus /ready. Password reset/deactivation now revokes browser access; rotating the monitoring token does not.
- New migration 004 preserves identities/history, converts legacy user/operator/unknown roles to inactive buyer, retains inactive admin identities, adds session/preferences/rate-limit storage and a case-insensitive username constraint. An explicitly configured OPERATOR_USER_ID can bootstrap the first super admin. Existing credentials are never overwritten by restart/bootstrap.

The deployment generator now produces private bootstrap credentials, production cookie settings and the unchanged independent service secrets. Parent CI/rehearsal use password accounts/cookies and test monitoring-token confinement and password/session revocation. Standalone backend CI now provisions PostgreSQL and Redis for its real fixture tests (resolving the missing-fixture configuration identified in BASE-01).

## Synchronized contract and operations

Canonical OpenAPI, its embedded copy and generated frontend types are updated together. The frontend keeps CSRF in memory and resumes via cookies; it removes the previous session-storage API token. It requests with_scores explicitly for every offer sort so the existing scored response contract is consistent for this client. The broader offer/healthcare response redesign remains step 4/6.

Account installation/upgrade, bootstrap and endpoint details are in [backend identity operations](../persob/docs/identity.md). Existing private .env installations must add explicit bootstrap credentials before enabling account access, preserving OPERATOR_USER_ID and the Telegram session key. New installations use scripts/setup-env.py. Back up before applying the new migration; do not edit migrations 001–003.

## Observed verification before publication

Local environment: Go 1.26.11, Node 24.22.1, Python 3.12.14, PostgreSQL 17.11, Redis 8.0.2, MongoDB 7.0.26, Chromium headless shell 156.0.8078.79. Temporary services are isolated to the verification invocation and synthetic data. CI remains the PostgreSQL 16/Redis 7 reference environment; local native runs do not claim to be Docker image execution.

| Check | Observed outcome |
| --- | --- |
| Full backend unit suite with disposable PostgreSQL/Redis | Passed across all packages |
| Identity HTTP/PostgreSQL tests with race detection | 4 tests passed: lifecycle, security boundary, concurrent super-admin protection, populated legacy migration/idempotency |
| go vet and backend executable build | Passed |
| Database acceptance, internal/audit and internal/telegram | Passed with disposable PostgreSQL/Redis/MongoDB |
| Full backend race suite | Passed across all packages on a separate empty disposable database |
| Canonical/embedded OpenAPI consistency | Passed |
| Generated frontend types | Regenerated from canonical OpenAPI; typecheck passed |
| Frontend production build | Passed |
| Full-stack Playwright | 10 passed (17.0s): account create/customize/reload/authorization/logout, last-super-admin UI, existing live workspace, error/no-fixture-fallback, mobile RTL/LTR, automated WCAG AA |
| Python configuration/backup/monitor/rehearsal checks | 8 passed (including new credential-aware readiness regression) |
| Modified configuration/workflow YAML parse and whitespace | Passed |

Earlier browser attempts did not execute app checks because the browser download was truncated and the full Chromium binary required unavailable Unix sockets. Debian headless shell ran successfully. One subsequent account test used an exact label locator for a nested select; switching to its actual combobox accessibility role resolved the test and the full ten-test run passed. Earlier compile attempts overlapped source changes; completed checks, not those incomplete attempts, are the evidence to use. A first full race rerun reused the browser-seeded database: existing negative repository tests dropped their isolated tables and then resolved the public application tables through search_path, so their expected missing-table errors did not occur. The final race run uses a separate empty disposable database, matching CI sequencing; no assertions were removed or suppressed.

## Remaining limits

- Step 3 must replace administrator/single-owner marketplace assumptions with explicit source grants and buyer-specific matching/aggregation/inquiry visibility. This checkpoint deliberately denies buyer shared-marketplace reads.
- The live catalog remains electronics until step 4 and the healthcare prototype remains separate until step 6. No HTTP mock LLM implementation is claimed here.
- Account administration currently lists a bounded 200 accounts. Email delivery, public signup, social login and MFA are not part of this slice. Login is limited per username and socket peer; a shared reverse proxy concentrates that peer limit as documented.
- The container install/rotation/restore rehearsal was updated for sessions but requires Docker-enabled CI execution. Existing runtime-image scan findings from BASE-02 remain release work; this identity change does not claim to resolve them.
- No main branch was intentionally changed, no production service was deployed, and no real Telegram seller messages were sent.

The [workflow ledger](WORKFLOW.md) records candidate/published revisions and is updated before every individual publication. Its final parent commit is reported after the remote confirms it; a document cannot embed its own final commit SHA.

## Published submodule candidates

- Backend: [299a942f66dec0ac17e4ef5a8dd8a12ce46356d8](https://github.com/Uncle-Taki/persob/commit/299a942f66dec0ac17e4ef5a8dd8a12ce46356d8), remote branch confirmed.
- Frontend: [d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242](https://github.com/Uncle-Taki/persof/commit/d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242), remote branch confirmed.
- Parent commit: reported after the final documentation/configuration tree and these exact pins are published.

CI follow-up: backend and frontend initial feature runs passed. The first parent integration run exposed ambient deployment settings leaking into config tests; the backend follow-up clears all newly added variables and explicitly tests insecure production cookies. The first container rehearsal exposed a readiness-only wait before checking token rotation; the parent follow-up requires the new monitoring credential to reach the operation route before proceeding. These failures and their exact runs remain recorded in the workflow ledger. Dependency checks passed; runtime-image scanner findings remain open.
