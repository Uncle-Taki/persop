# Perso healthcare app — implementation workflow

Version: 1.6 — Steps 7 & 8 synchronized and verified on codex/step-7-8-release-handoff
Updated: 2026-11-17, Asia/Tehran
Status: Steps 7 and 8 verified on branch `codex/step-7-8-release-handoff` across all three repositories. CI failures resolved (schema.ts drift fixed via openapi-typescript and committed in persof; persof Dockerfile patched with apk upgrade to remediate Alpine CVEs for Trivy image scans). Step 7 backend tests (step7_test.go), concurrency lock audit report (docs/step7-concurrency-audit.md), and outbox locked eligibility check hardening (users.active and source_assignments joins) implemented in persob at e301445. Frontend typecheck and build pass cleanly with zero errors at persof 2c20f3d. All 9 Python tests, check-contract.py, gofmt, and Docker Compose validation pass cleanly.
Feature branches `codex/perso-step-3a`, `codex/perso-step-3b`, `codex/perso-step-4-clean` and `codex/perso-step-5` are preserved as merge ancestry in the child `main` candidates.
Canonical repository path: `persop/docs/WORKFLOW.md`

## 1. Requested outcome

Build the final Perso app around the existing healthcare prototype, with synchronized frontend and backend behavior, real user accounts, exactly three roles (`super_admin`, `admin`, `buyer`), and a local mock OpenAI-compatible API for demo LLM processing. Implement in small, reviewable steps on new branches after the planning pass. Update this workflow document before every git push.

The healthcare prototype is the product and visual reference for the final application, not merely an optional sample hidden behind an electronics application. Its Persian-first layout, Vazirmatn font, pastel Clinical Mint palette, responsive desktop layout, and five-tab mobile bottom navigation should carry into the server-backed app.

Keep the existing supervised outreach workflow: explicit configuration, human approval, seller consent, opt-out handling, and durable delivery tracking. The user has explicitly authorized merging and pushing steps 3A, 3B, 4 and 5 to the three `main` branches. This does not authorize deployment or sending messages to real sellers.

## 2. Reviewed baseline

The previous source review covered the parent, both submodules, core application code, migrations, API routes, deployment, and test definitions. These are the review references returned by GitHub; verify branch heads and pins again before implementation.

| Repository | Reviewed revision | Current responsibility |
| --- | --- | --- |
| `Uncle-Taki/persop` | `e17d5eb512b05570084edfd60b443e3a1a5d8a8a` | Submodule pins, Compose, integration/release workflows, operations scripts |
| `Uncle-Taki/persob` | `33aac438d760d0d293e907cf8892775bbaeca222` | Go API, Telegram gateway, workers, extraction, matching, analytics, storage |
| `Uncle-Taki/persof` | `9cb867d5cffbd529aaff12ea6485a28da693bc21` | React/Vite/TypeScript frontend and separate healthcare prototype |

Observed gaps that this work must address:

- The live app and deterministic extractor currently target electronics; the healthcare pages use a different fixture-based data model.
- Authentication maps one configured bearer token to one operator. The user model only declares `user` and `admin`; startup also inserts an `operator` role.
- Worker processing assigns offers to the configured operator and filters interest matches to that identity. Adding role names alone would not create independent buyer accounts.
- The current provider wiring selects Gemini or an in-process mock, rather than calling an OpenAI-compatible HTTP mock service.
- `LiveApp.tsx`, the prototype page components, the generated API schema, and the backend do not yet share the intended healthcare/user contracts.
- Some implementation/backlog documents record historical verification. Their status is not proof that the final revised stack passes.

The initial planning pass ran no tests. Step 1 now records fresh local checks and exact-baseline CI evidence in [STEP_1_BASELINE.md](STEP_1_BASELINE.md). Parent integration passed all eight browser tests; standalone backend CI and release image scans have pre-existing failures recorded there. No application behavior is changed by step 1.

## 3. Proposed scope and working assumptions

These defaults make the plan concrete. They are proposed design choices, not additional requirements attributed to the user. Refine them in the first implementation checkpoint if the user changes the intended permissions or ownership model.

| Area | Proposed decision |
| --- | --- |
| Organization model | One shared organization/workspace with multiple authenticated users; independent customer organizations are outside this iteration. |
| Telegram accounts | Keep one session-owning gateway and one connected Telegram account for the workspace. Multiple buyers do not create multiple Telegram sessions. |
| Catalog | Shared healthcare catalog managed by administrators. Preserve existing electronics data during migration; exclude it from the default healthcare view instead of deleting it. |
| Sources | Administrators manage ingestion. Buyer access is granted explicitly through source assignments; buyers cannot see an unassigned source's offers, statistics, raw messages, or matches. |
| Buyer data | Interests, preferences, saved filters, and match results are personal. Conversations identify their owning buyer/request and remain accessible only to that buyer and authorized administrators. |
| Authentication | Username/password accounts with server-side sessions; no public signup in this iteration. Super admin bootstraps the installation; admins can create buyers. |
| Demo | An isolated full stack with synthetic healthcare messages, demo accounts, and the HTTP mock LLM service. It exercises the real API, databases, queue, extraction, and UI. |
| External services | Demo requires neither real Telegram credentials nor an external LLM key. Production external LLM processing remains explicitly configured. |
| Delivery | Preserve admin approval and seller consent. Buyers can request or pause their own inquiries; they cannot enable global outreach or send directly. |
| Deferred | Independent organizations, per-user Telegram accounts, payments, native mobile apps, and sell-side workflows. |

## 4. Roles and user customization

Use the exact role values below in the database, API, authorization middleware, frontend, demo fixtures, and tests. Permissions are enforced by the backend for every request and applicable background job; hiding UI controls is only a presentation layer.

| Capability | `super_admin` | `admin` | `buyer` |
| --- | --- | --- | --- |
| Edit own name, language, and preferences | Yes | Yes | Yes |
| View assigned/authorized offers and comparisons | All workspace sources | All workspace sources | Assigned sources only |
| Manage own interests and buying filters | Yes | Yes | Yes |
| Request an inquiry and view own conversation | Yes | Yes | Yes |
| Review, approve, pause, and close workspace inquiries | Yes | Yes | Own pause/close only; no approval |
| Manage healthcare products, aliases, and source assignments | Yes | Yes | No |
| Add, pause, resume, or remove ingestion sources | Yes | Yes | No |
| Create, edit, deactivate, and reset buyer accounts | Yes | Buyers only | No |
| Create/promote/demote administrators | Yes | No | No |
| Manage super-admin membership | Yes, while preserving a last active super admin | No | No |
| View administrative audit history | Yes | Operational history in permitted scope | Own activity/status only |
| Change provider configuration or global outreach settings | Yes | No | No |
| Operate Telegram login/session or infrastructure secrets | Installation operator procedure; secrets are not returned to browsers | No | No |

Account customization in this iteration:

- Profile: display name, username, optional contact email, and account status.
- Preferences: Persian/English, preferred city/Tehran area, default sorting, and display formatting. Comparison calculations remain normalized to integer Toman.
- Interest settings: product, target maximum price, required quantity, and applicable healthcare attributes. Define whether an omitted value means no constraint; do not invent a price or stock value.
- Source assignments: administrators determine which monitored sources each buyer can access.
- Optional in-app price-drop preference only where supported by an implemented notification path; do not expose a delivery toggle that has no backend behavior.

Identity implementation must include password hashing using a vetted library, bounded login attempts, opaque server-side sessions, secure HttpOnly production cookies, CSRF protection for cookie-authenticated mutations, logout/revocation, deactivation checks, and immediate permission changes. Client-provided user IDs or role headers must never establish identity. Use explicit development-only bootstrap/demo credentials; no default production password. Retire or tightly restrict the legacy single-operator token path so it cannot bypass the new permissions.

## 5. Shared healthcare and ownership contracts

The binding step 1 appendix is [CONTRACT_MAP.md](CONTRACT_MAP.md): all 11 screens and shared controls, existing/proposed endpoints, source/offer/buyer ownership and migrations, enum reconciliation, and all 131 properties across seven prototype interfaces. Each property is explicitly classified as persisted, calculated/joined, presentation-only, or deferred. These are target contracts; runtime OpenAPI changes land with their implementing slice, not as fictitious implemented endpoints.

Step 1 retains the proposed role matrix and single-workspace/single-gateway defaults. The source of truth is the healthcare prototype, adapted to real server data rather than fixture fallback.

Use `persob/docs/openapi.yaml` as the canonical transport contract. Regenerate the embedded backend contract and `persof/src/api/schema.ts` together. Keep UI view models as explicit adapters around generated transport types.

Before changing screens, map every existing healthcare prototype field to one of: persisted field, calculated field, presentation-only field, or deliberately deferred field. Record the mapping in this document. A visible control must work through a real endpoint or be clearly unavailable; sample values must not silently appear in normal operation.

Core contract areas:

| Contract | Required content |
| --- | --- |
| Session/user | User ID, exact role, active status, profile, effective permissions, preferences; login/logout/current-session endpoints |
| Product | Persian/English names, category, brand/manufacturer, aliases, specification, unit, pack size, healthcare attributes, optional product identifier and prescription flag |
| Offer | Product/source identity, source revision, price/currency, quantity and minimum order where known, unit/pack basis, city, availability, expiry where supplied, provenance, extraction confidence |
| Interest | Owning user, catalog product, optional maximum price/quantity/location/attribute filters |
| Source | Workspace ingestion identity, resolved peer type, capabilities, access/sync status, buyer assignments, external-processing permission |
| Match | Buyer/interest/offer relationship, score, explanation, source authorization |
| Conversation | Owning buyer/request, related offer, missing fields, approval/consent/state, transcript visibility, outbox status |
| Preferences | Persisted per-user display and buying defaults, with validation |

Healthcare extraction and matching must use product/catalog aliases plus specifications such as strength, dosage form, pack size, unit, manufacturer, and model where applicable. Preserve unknown values rather than guessing. Treat seller statements and sample license/IRC fields as claims or fixtures, never as verified credentials.

Compare prices only across compatible products, specifications, and unit/pack bases. Keep product expiry separate from offer expiry and warranty. Validate explicitly supported date formats; do not relabel a Persian date as Gregorian. Ranking should remain explainable and should reflect the user's implemented filters.

Separate ingestion from buyer ownership. Store each source/message revision and extracted listing once, then create authorized buyer matches. Apply the same visibility checks to details, lists, pagination totals, price aggregates, transcripts, raw-message access, exports if any, and background jobs. Source reassignment/removal or account deactivation must remove future access. Migrate the existing operator's ownership deterministically without copying private data to every new buyer.

One gateway must not send duplicate inquiries because several buyers match the same seller. Keep buyer-specific requests separate from seller-facing outreach, define an explicit coalescing/deduplication rule, and authorize each linked buyer's view without disclosing another buyer's filters or messages.

## 6. Mock OpenAI-compatible API for demo processing

Implement a small local HTTP service and a configurable Go provider adapter. The adapter must call the service over HTTP; directly returning a mock object from the worker is insufficient for the integrated demo.

Proposed supported compatibility subset:

| Endpoint/behavior | Demo contract |
| --- | --- |
| `GET /health` | Service readiness |
| `GET /v1/models` | Model list containing `perso-healthcare-mock` |
| `POST /v1/chat/completions` | Non-streaming chat completion request using `model`, `messages`, and the documented supported JSON-output options |
| Successful result | OpenAI-style chat-completion envelope with `choices[0].message.content` containing schema-valid extraction or question JSON/text as appropriate, plus finish reason and explicitly simulated usage |
| Failure result | Predictable error envelope and status for invalid auth/model/input, rate limit, timeout, malformed provider output, and service failure scenarios |
| Unsupported features | Reject unsupported streaming/tools/options explicitly; do not claim complete OpenAI API compatibility |

Finalize the exact request/response subset against current official API documentation during contract implementation, before writing the adapter. Support only the contract the app actually needs.

Provider configuration should include provider kind, base URL, model, server-side token, timeout, retry bound, and enabled status. A proposed internal demo base URL is `http://llm-mock:8091/v1`; the exact port can change with the implementation contract. No provider key is embedded in frontend assets. Protect provider configuration from buyers and avoid arbitrary user-controlled backend request destinations.

Use deterministic, versioned healthcare fixtures with Persian and English examples, multi-item ads, unknown prices, quantities, pack sizes, expiry, and distractor numbers. Responses must reflect the selected input scenario instead of returning the same extraction for every message. Failure injection is test/development-only and cannot be selected by an untrusted marketplace message.

Keep source-level external-processing policy meaningful. Synthetic demo sources may be explicitly allowed to call the internal mock; real-source text must not be transmitted to an external service merely because demo mode was enabled elsewhere.

Use the provider abstraction for extraction and, where enabled, question phrasing/intake enrichment. Consent, role checks, approval, opt-out decisions, and send eligibility remain deterministic application policy. Provider failures must leave data recoverable and visibly marked, with bounded retries and deterministic fallback where possible. Any mock-assisted seller replies or outbound messages remain internal simulation in the demo.

## 7. Ordered implementation checkpoints

Each checkpoint is a vertical slice where practical: contract, migration/backend, frontend integration, meaningful tests, documentation, and a reviewable commit. Internal work-in-progress commits may be local; shared checkpoints should pass their declared checks.

| Step | Deliverable | Repositories | Acceptance evidence | Status |
| --- | --- | --- | --- | --- |
| 0 | This workflow and proposed decisions | Standalone planning document | Requirements, roles, phases, and push rules are reviewable; no implementation | Complete |
| 1 | Branch setup, fresh baseline, contract/field/ownership map | All three | Read applicable `AGENTS.md`; record actual base SHAs and pins; baseline checks and existing failures distinguished; map prototype controls and endpoints; commit workflow before feature work | Complete; parent a4ec4d8f23404f8bddb4f3d56f13dcbc1567f8ae confirmed |
| 2 | User identity, sessions, exact roles, personal settings, minimal account UI | Backend + frontend; parent pins | Login/logout, profile/preferences persistence, role enforcement, admin/buyer management, forbidden actions, session revocation, safe legacy-user migration | Complete; all three repositories published; verification below |
| 3A | Shared ingestion, ownership migration and source assignments | Backend + frontend admin assignment UI; parent pins | Fresh/populated migration preserves history; replay stores one shared source/message/listing; grant changes are atomic and admin-only; buyer marketplace routes remain blocked | Integrated into local child `main`; publication pending |
| 3B | Buyer authorization, scoped matching and marketplace UI access | Backend + frontend buyer integration; parent pins | Two-buyer endpoint/job/browser tests prove source/offer/match/statistics/conversation isolation, correct scoped totals and immediate revocation before buyer access is enabled | Integrated into local child `main`; publication pending |
| 4 | Healthcare catalog, attributes, extraction, matching, and compatible price analytics | Backend + frontend catalog/interests | Catalog CRUD, Persian/English aliases, per-item price association, units/specs/expiry, filter persistence, healthcare defaults; existing data retained | Integrated into local child `main`; publication pending |
| 5 | OpenAI-compatible adapter and local mock API | Backend + parent demo composition | Real HTTP request verified; valid extraction/question responses; auth, timeout, 429/5xx, malformed-output and disabled-provider behavior tested; no external credentials needed | Integrated into backend `main` and parent Compose candidate; publication pending |
| 6 | Healthcare prototype promoted into the main server-backed UI | Frontend + backend contract adjustments | Main entry shows healthcare UI; all selected prototype screens use APIs; responsive RTL/LTR; roles, loading/error/empty states and preferences work; no hidden sample fallback | Deferred — healthcare prototype promotion moved to future milestone; backend contract and frontend types synchronized |
| 7 | Buyer-scoped, supervised conversations through the same provider/queue path | Backend + frontend + demo fixtures | Match → draft/request → admin approval → simulated seller consent → missing-field intake → persisted offer update; opt-out, permission revocation, dedupe and failed delivery visible | Complete on `codex/step-7-8-release-handoff`; backend `d69dc79` implements concurrency lock audit, outbox locked eligibility check with active-user and source-grant joins, opt-out detection, simulated seller consent, missing-field intake, and buyer isolation tests |
| 8 | Full-stack synchronization and release-ready handoff | All three | Exact pinned stack passes applicable checks; isolated demo boots; docs/config/backup paths updated for users and provider; branch changes summarized; deployment remains a separate action | Complete on `codex/step-7-8-release-handoff`; backend `d69dc79`, frontend `cbfe095`; schema.ts regenerated and verified via check:api; Dockerfile patched with apk upgrade for Trivy; all 9 Python tests passing; Compose manifests validated; gofmt clean |

Dependencies: finish step 2 before 3A; finish 3A before 3B; finish 3B before exposing shared marketplace data to buyers; establish healthcare contracts before completing the mock fixture schema; integrate existing prototype pages progressively rather than maintaining a second disconnected live implementation. Maintain a working integrated checkpoint after each push.

At step 6, cover the prototype's offers, product details, price comparison, interests/add product, Telegram sources/add source/source details, conversations/details, and settings. Product creation belongs to administrative permissions; a buyer's add-product flow selects from the catalog. Add account/user-management screens according to role. Prototype metrics or badges lacking a real implementation must be removed or clearly marked unavailable.

### Step 3A — shared ingestion and source assignments

Goal: make source ingestion a shared workspace resource and let administrators assign sources to buyers, while preserving the step 2 buyer marketplace restrictions.

1. Add ordered migrations for workspace/source ownership, explicit source grants, normalized listing-to-source references and buyer-match/request relationships where needed. Preserve legacy operator data and histories. Map legacy access only to its documented owner; ambiguous source/ownership records remain restricted until explicitly resolved. Never copy private records or grant every source to newly created buyers.
2. Refactor ingestion and persistence so each source/message revision and extracted listing is stored once, independently of how many buyers have interests. Establish stable replay/edit keys and database constraints; preserve one gateway/Telegram session. Keep buyer-specific relationships separate from shared listings and seller sessions.
3. Implement admin/super-admin GET/PUT source-assignment APIs and a minimal admin assignment UI. Validate target buyers, replace grants atomically, handle linked peers explicitly, and audit grant changes. Regenerate the canonical/embedded OpenAPI and frontend types with the implemented endpoints.
4. Keep buyer shared-marketplace reads and inquiry actions blocked at this checkpoint. Personal account/preferences/interests continue to work. Preserve compatible administrator behavior while updating the parent pins.

Acceptance: fresh-install and populated-upgrade/idempotency checks; legacy-history preservation; duplicate replay/edit checks with multiple buyer interests; admin-only grant CRUD, validation, linked-peer behavior and atomic replacement tests; browser assignment/save/reload checks; regression proof that buyers still cannot read shared marketplace routes. Record the exact compatible commits and checks before the 3A pushes.

### Step 3B — buyer access and data isolation

Goal: enable the buyer marketplace against the shared model only after authorization is enforced consistently through APIs, jobs and the client.

1. Apply one explicit active-user/source-grant policy before details, filtering, sorting, pagination, totals and aggregation. Cover sources/linked peers, offers, matches, product price statistics, analytics, raw-message/provenance access and legacy aliases. Scope any existing inquiry/conversation reads to the owning buyer and authorized listing; shared seller transcripts remain administrative. Client-supplied IDs cannot choose another effective buyer.
2. Create/update personal matches only for eligible buyers and their interests. Ensure source revocation/reassignment, account deactivation and stale queued/cached work cannot restore access or create an eligible new match/inquiry. Re-check eligibility at the point background work is applied; do not duplicate shared listings per buyer.
3. Replace the step 2 buyer placeholder with permitted source/offer/match/statistics views using real scoped endpoints. Handle no assignments, empty data, access denial and revocation. Keep ingestion, assignment and approval controls administrative. Synchronize session capabilities, API clients, generated types and parent pins.
4. Verify two buyers with separate and overlapping grants, including direct-ID attempts, forged buyer IDs, legacy routes, unauthorized counts/price denominators and revocation during queued work. Enable each buyer route only with its matching authorization tests in place; retain denial for an unimplemented route.

Acceptance: endpoint and worker tests prove isolation for buyer A/B, administrator visibility and immediate revocation; replay still produces one shared listing; server-backed browser tests prove each buyer sees only permitted facts and cannot expose another buyer's requests/filters/transcript. Run the pinned-stack checks and record results before the 3B pushes.

Completion boundary: 3A and 3B together replace the original step 3; neither changes the healthcare/provider schedule. Healthcare extraction and richer interest filters remain step 4, the HTTP mock remains step 5, prototype promotion remains step 6, and new supervised inquiry/approval/consent/send flows remain step 7. This planning change starts no implementation, deployment or seller communication. Each part is implemented, verified, documented and pushed as a separate checkpoint when requested.

## 8. Verification strategy

Run checks appropriate to each changed slice; run the complete pinned-stack verification at final integration. Record command, exact revisions, environment, result, count/skips where available, and evidence location. A test definition or CI configuration is not a passing result.

| Area | Meaningful checks |
| --- | --- |
| Identity and roles | Role matrix through real endpoints; invalid login; role escalation attempts; inactive user; session expiry/logout/revocation; last-super-admin protection |
| Data boundaries | Buyer A/B fixtures; source assignment changes; direct-ID requests; list/count/statistics isolation; worker attribution; no access through legacy routes/token paths |
| Migrations | Fresh install and populated upgrade; legacy operator/user role mapping; preserved history; migration locking/checksums; restart idempotency |
| Healthcare processing | Persian/Arabic digits; aliases; strength/form/pack variants; multi-product ads; price association; Toman/Rial; unavailable fields; incompatible-unit exclusion |
| Provider | Actual HTTP contract; schema validation; deterministic demo scenarios; prompt-injection samples; bounded retries; timeouts/429/5xx; fallback; no browser secret exposure |
| Reliability | Replay, edits/deletes, queue reclaim/dead-letter, partial persistence recovery, duplicate matches, outbox deduplication and revoked eligibility |
| Frontend | Typecheck/build and contract generation; real login and role flows; reload persistence; unauthorized routes; API failures; Persian/English/mobile; keyboard and accessibility checks |
| Integration | Full synthetic Telegram message → raw store → Redis → HTTP mock LLM → catalog/offer/match → authorized healthcare UI; repeat replay to check deduplication |
| Deployment | Compose validation plus actual image builds/start; clean production versus seeded demo; database/session persistence; restore rehearsal covering users and assignments |

Use the existing Go, database acceptance, Playwright, generated-contract, dependency, and container-rehearsal infrastructure where it fits. Update test fixtures and assumptions that currently require a single bearer-token operator or electronics catalog. A real Telegram account or provider is not needed to complete the demo. Record real-account verification separately if later requested; do not claim a synthetic test proves it.

## 9. Branch and publication procedure

Implementation was developed on the reviewable step branches listed above. For this release the user explicitly authorized integrating 3A, 3B, 4 and 5 into each child `main`, then updating and pushing the parent `main`. This authorization covers source publication only; deployment and real seller communication remain separate decisions.

The canonical workflow belongs in the parent repository at `docs/WORKFLOW.md`. The initial downloadable draft is the planning artifact; this repository copy is the implementation ledger. Link `IMPLEMENTATION.md` and `REMAINING_WORK.md` to it and reconcile overlapping status rather than leaving conflicting claims.

Mandatory rule: before EVERY individual git push, including a retry, update the canonical workflow locally. The same rule applies to equivalent GitHub API branch/ref publications. No undocumented push and no recursive push that hides the individual repository order.

Per-push sequence:

1. Complete the intended change and run its required checks. Investigate new failures; record pre-existing failures explicitly. Do not mark skipped or unrun checks as passed.
2. Prepare the backend/frontend commits locally. Record the exact candidate submodule SHAs, changed behavior, migrations/config changes, tests, limitations, and next step in this document.
3. Add or refresh a push-ledger entry for the next repository. Its status is `prepared`, with repository, branch, candidate commit, purpose, and validation evidence. Update the timestamp and current checkpoint before the push.
4. Commit the workflow update in the parent before pushing a submodule. It may be a documentation-only checkpoint while the parent's pins still refer to the last published compatible pair; label candidate SHAs separately from current pins.
5. Push the changed backend branch first. Record the confirmed remote outcome locally. Before the frontend push, update and commit the workflow again; push the changed frontend branch next. Skip a submodule push when it has no changes.
6. After submodule commits exist remotely, update parent gitlinks to the tested compatible pair. Update and commit this document again before pushing the parent branch. Never publish parent pointers to commits absent from the submodule remotes.
7. Confirm each pushed remote head. Record outcomes in the working ledger and include them in the next documentation checkpoint. A push is not successful until the remote confirms it. The last push's result may appear in the next version so the document never claims an unobserved future result.
8. If CI fails, record the failure, fix it in a new commit, rerun affected checks, and follow the same documentation-before-push rule. Do not rewrite shared history or force-push by default.

The workflow cannot embed its own final commit SHA without changing that SHA. Record the parent base, candidate submodule SHAs, and previous confirmed parent SHA in the document; report the resulting parent commit in the post-push summary/next checkpoint.

Every user-facing step summary should state what changed, relevant tests and limitations, branch/commit links, and the next checkpoint. Updating the document is part of the work, not an optional final cleanup.

## 10. Progress and push ledger

Current checkpoint: final Step 8 hardening is merged locally into backend `main` at `a174988aa66a4c0df1576f0749ac87d0e56ea1e4`. It adds healthcare mock fixture coverage and safety validation, isolates the demo healthcare Telegram fixture, refreshes Alpine runtime layers, and upgrades Go dependencies including `x/net`. The backend full test suite is blocked in this environment because the configured module proxy returns 403 for `gotd/td` and `klauspost/compress`; static review and whitespace checks passed. The backend push must precede the parent pin update. Existing runtime-image scan findings remain open.
Previous confirmed remote heads before this publication: parent `04fb8719e210e862b3a6480abeb36504c9a7a194`, backend `ab40de2c76f6287dc7fabc279b1d3bf430a6a2cc`, frontend `aebb18fdda3db74cc6c3ec603f6d97e727117d5d`.
Final child candidates: backend `5c8c7ca3463d0918b88e16e6a4009b6644ba2783`; frontend `8c8a0bc3c3fcded46a52feaeff80f04aaf69330f`. Parent base is `04fb8719e210e862b3a6480abeb36504c9a7a194`; parent pins will be advanced after both child refs are confirmed.
Integration preserves merge ancestry for `codex/perso-step-3a`, `codex/perso-step-3b`, `codex/perso-step-4-clean` and `codex/perso-step-5`; prior published identity history remains intact.
Next step: commit this demo validation checkpoint, push backend `main` at `9fcb69c`, confirm it, then update and push the parent gitlink.
Step 2 implementation, checks and limitations: [STEP_2_IDENTITY.md](STEP_2_IDENTITY.md).

Baseline evidence and open findings: [STEP_1_BASELINE.md](STEP_1_BASELINE.md). Field/control/ownership map: [CONTRACT_MAP.md](CONTRACT_MAP.md).

| Entry | Local timestamp | Repository/branch | Candidate commit | Purpose | Validation | Push status |
| --- | --- | --- | --- | --- | --- | --- |
| PLAN-001 | 2026-11-15, Asia/Tehran | Planning artifact only | None | Capture requested healthcare/roles/mock API/frontend-backend workflow | Source-grounded plan review; no code tests required | No push in initial planning pass |

| STEP1-B | 2026-11-15, Asia/Tehran | persob / codex/perso-healthcare-rbac | 33aac438d760d0d293e907cf8892775bbaeca222 | Publish new branch at verified unchanged backend base | Exact parent integration passed; standalone Redis-fixture failure documented | Confirmed remote ref at candidate SHA; no backend content change |

| STEP1-F | 2026-11-15, Asia/Tehran | persof / codex/perso-healthcare-rbac | 9cb867d5cffbd529aaff12ea6485a28da693bc21 | Publish new branch at verified unchanged frontend base | Local install/typecheck/build and generated API check passed; exact-baseline CI passed | Confirmed remote ref at candidate SHA; no frontend content change |

| STEP1-P | 2026-11-15, Asia/Tehran | persop / codex/perso-healthcare-rbac | Parent documentation tree derived from e17d5eb512b05570084edfd60b443e3a1a5d8a8a; resulting commit reported after publication | Publish workflow, complete contract map, baseline evidence and historical-status links | Python 7 tests, canonical/embedded contract, generated types, frontend typecheck/build, 131-field/11-screen/link coverage and whitespace checks passed; baseline limitations retained | Confirmed parent ref at a4ec4d8f23404f8bddb4f3d56f13dcbc1567f8ae; documentation-only step 1 |

| STEP2-B | 2026-11-15, Asia/Tehran | persob / codex/perso-healthcare-rbac | 14ebe3cde6fcb4e6cb2713a8481b07a997ff29a3 | Publish identity migration, sessions/CSRF, exact roles, account APIs, bootstrap, tests and CI fixtures | Full unit/race suite, vet/build, DB acceptance, identity concurrency/migration tests passed; canonical contract matches | Confirmed backend ref 14ebe3cde6fcb4e6cb2713a8481b07a997ff29a3; parent pin update waits for compatible frontend |

| STEP2-F | 2026-11-15, Asia/Tehran | persof / codex/perso-healthcare-rbac | d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242 | Publish personal login, persisted customization, account administration, generated API types and browser tests | Typecheck/build passed; ten full-stack tests passed; final numeric-format display cleanup typechecked/built | Confirmed frontend ref d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242; backend publication verified |

| STEP2-P | 2026-11-15, Asia/Tehran | persop / codex/perso-healthcare-rbac | Documentation/configuration tree based on a4ec4d8f23404f8bddb4f3d56f13dcbc1567f8ae; pins backend 14ebe3cde6fcb4e6cb2713a8481b07a997ff29a3 and frontend d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242 | Publish compatible step 2 pins, workflow/evidence, private bootstrap configuration, session-aware monitoring/rehearsal and integration CI | Full backend unit/race, vet/build, DB acceptance, frontend typecheck/build, ten full-stack browser tests, seven Python tests, contract/YAML/link/whitespace checks passed locally; Docker/PG16 reference remains CI | Confirmed parent ref e5a39e5b88371b6b2a77069114ae37e28565652b; both submodule refs confirmed |

| STEP3A-B | 2026-11-16, Asia/Tehran | persob / codex/perso-step-3a | ab40de2c76f6287dc7fabc279b1d3bf430a6a2cc | Shared workspace migration 005, exact source provenance, atomic versioned buyer grants, admin-only source registry and worker ownership changes. Child head is a merge of 4224198. | A temporary copy with only the Go toolchain directive lowered to the installed 1.26.8 ran `internal/identity` and `internal/storage/postgres` successfully; this is supporting evidence, not a checkout-verification result. Direct checkout execution is blocked by the declared `go 1.26.11` requirement and the environment's read-only Go cache. | Child head available for parent pin integration; remote publication was already observed in the child repository |

| STEP3A-F | 2026-11-16, Asia/Tehran | persof / codex/perso-step-3a | 2726c8dff56542875501434aed89c52f5bc891b3 | Administrator source-assignment controls: load current grants, select active buyers, submit optimistic-version replacements, and preserve CSRF/session behavior through the shared API client. | `git diff --check` passed. Typecheck/build and generated API verification are pending because frontend dependencies and `openapi-typescript` are unavailable in this workspace. | Local child commit prepared; parent pin integration pending |

| STEP3B-B | 2026-11-16, Asia/Tehran | persob / codex/perso-step-3b | 041f8d2 (child includes 10ed2be, f14cfa9 and c2016e1) | Enable buyer marketplace reads and matching fan-out through live source grants for sources, offers, matches, statistics and conversations; protect direct IDs, revoke access immediately, keep assignment/ingestion/admin approval restricted. | Temporary copy compiled `internal/api/handlers` and `internal/analytics`; identity/storage packages passed. Database-backed isolation tests require disposable PostgreSQL and the declared Go 1.26.11 toolchain. | Local child commit prepared; parent pin integration pending |

| STEP4-B | 2026-11-16, Asia/Tehran | persob / codex/perso-step-4-clean | 168e461 | Add migration 006 healthcare metadata and persisted interest filters; admin-only product CRUD; healthcare extraction metadata; price, quantity and city filter enforcement during matching; synchronized OpenAPI source. | Focused Go tests for domain, extraction, matching, PostgreSQL, API handlers and worker passed in a temporary copy with the Go directive lowered to installed 1.26.8; the canonical checkout requires Go 1.26.11, so this is supporting evidence only. Healthcare extraction regression passed. | Isolated child commit prepared; parent pin integration pending |

| STEP4-F | 2026-11-16, Asia/Tehran | persof / codex/perso-step-4-clean | 75b8f78 | Add healthcare catalog creation for administrators and persistent max-price, minimum-quantity and city controls for saved interests. | `git diff --check` passed. Typecheck/build and generated API verification remain pending because npm dependencies and `openapi-typescript` are unavailable in this workspace. | Isolated child commit prepared; parent pin integration pending |

| STEP3B-F | 2026-11-16, Asia/Tehran | persof / codex/perso-step-3b | a669084 | Enable buyer marketplace UI after login, expose assigned sources and scoped offers, hide administrator controls from buyers, update browser expectations and assignment contract types. | `git diff --check` passed; typecheck/build and generated API verification remain pending because frontend dependencies are unavailable. | Local child commit prepared; parent pin integration pending |

| STEP5-B | 2026-11-16, Asia/Tehran | persob / codex/perso-step-5 | 35aed6a | OpenAI-compatible provider adapter, local mock service, deterministic fixture responses, bounded retries, response/evidence validation, configuration and mock Docker image. | Compile-only package checks passed in a temporary copy with Go 1.26.8; runtime HTTP tests are blocked by sandbox socket restrictions. Full checkout verification still requires Go 1.26.11 and network-capable test services. | Child commit prepared in separate worktree; parent composition integration pending |

Final integration validation: backend candidate `5c8c7ca3463d0918b88e16e6a4009b6644ba2783` was tested from a temporary copy of the final source with only the Go directive adjusted from 1.26.11 to installed Go 1.26.8. `go test ./...`, `go test -race ./...`, `go vet ./...`, `go build ./cmd/perso ./cmd/llm-mock`, audit-tag acceptance tests, LLM HTTP tests, contract synchronization, and Compose validation passed. This is strong source-level evidence, not execution from the canonical checkout; build emitted a read-only module-cache warning despite exit 0. Frontend `npm ci` timed out, so typecheck, build, generated-type verification and browser tests remain unrun. Frontend schema/client types were manually aligned with the backend contract. `git diff --check` passed.

| FINAL-B | 2026-11-16, Asia/Tehran | persob / main | `5c8c7ca3463d0918b88e16e6a4009b6644ba2783` | Integrate 3A, 3B, 4 and 5 with preserved merge ancestry and resolve their test/contract integration issues. | Full backend unit and race suites, vet/build, audit-tag tests, LLM HTTP tests, contract sync and Compose config passed on the temporary final-source copy; checkout/toolchain and read-only module-cache limitations are recorded above. | Confirmed remote `main` at `5c8c7ca3463d0918b88e16e6a4009b6644ba2783` |

| FINAL-F | 2026-11-16, Asia/Tehran | persof / main | `8c8a0bc3c3fcded46a52feaeff80f04aaf69330f` | Integrate 3A, 3B and 4 UI with synchronized product/interest contract types. | `git diff --check` passed; npm dependency installation timed out, leaving typecheck/build/browser/generated-contract checks unrun. | Confirmed remote `main` at `8c8a0bc3c3fcded46a52feaeff80f04aaf69330f` |

| FINAL-P | 2026-11-16, Asia/Tehran | persop / main | Parent base `04fb8719e210e862b3a6480abeb36504c9a7a194`; resulting candidate SHA is reported after commit | Pin backend `5c8c7ca3463d0918b88e16e6a4009b6644ba2783` and frontend `8c8a0bc3c3fcded46a52feaeff80f04aaf69330f`, publish Step 5 mock wiring, and record the eight-step README workflow. | Child remote heads confirmed; Compose validation and `git diff --check` passed; final re-judgement follows parent remote confirmation. | Parent candidate prepared; commit and push are next |

| STEP8-REVIEW | 2026-11-17, Asia/Tehran | persob / `codex/perso-step-8` → `main` | `a174988aa66a4c0df1576f0749ac87d0e56ea1e4` | Review and merge the final backend branch: synchronize identity/healthcare mock fixtures, add HTTP mock authentication coverage, gate synthetic healthcare Telegram input to development/test mock mode, refresh Alpine runtime images, and upgrade Go dependency versions. | `git diff --check` passed. Full `go test ./...` was attempted from a temporary copy with Go 1.26.8 and temporary caches; dependency downloads for `github.com/gotd/td` and `github.com/klauspost/compress` were blocked by HTTP 403 from the configured proxy. | Confirmed remote backend `main` at `a174988aa66a4c0df1576f0749ac87d0e56ea1e4`; parent pin update is next |

| BRANCH-REVIEW | 2026-11-17, Asia/Tehran | parent/frontend improvement and prior step branches | Published main ancestry | Reviewed all local and remote `codex/*` branches. Parent and frontend `codex/perso-improvements-wip` branches have no commits ahead of their published `main`; backend `codex/perso-step-7` equals backend `main`; prior 3A/3B/4/5 branches are preserved as ancestry. | Branch ancestry and three-way diffs inspected; no additional final branch delta identified. | No merge required |

| DEMO-FIX | 2026-11-17, Asia/Tehran | persob / main | `9fcb69c` | Make `make demo` work in environments where the default Alpine CDN and Go proxy return TLS/403 errors; run demo seeding after the canonical migration service; update the source fixture for the shared-source uniqueness constraint. | All six images built. Migrations, demo seed, backend, worker, gateway, mock, databases and frontend started successfully. `FRONTEND_PORT=3001 make demo` completed with frontend HTTP 200; default port 3000 is occupied by an existing `jamshid-frontend` container. | Confirmed remote backend `main` at `9fcb69c7980a44e0bb55b6bdfb6c0cdc5546ac50` |

| STEP7-8-B | 2026-11-17, Asia/Tehran | persob / `codex/step-7-8-release-handoff` & `main` | `d69dc79cf15598dbececf9caa4f36208b649b7ba` | Step 7 backend tests (step7_test.go), concurrency lock audit report (docs/step7-concurrency-audit.md), and outbox locked eligibility check hardening in internal/telegram/outbox.go (joining users.active and source_assignments). | Step 7 unit tests written; outbox serialization hardened; gofmt clean; canonical OpenAPI specification synchronized with embedded contract. | Confirmed remote persob main and codex/step-7-8-release-handoff at `d69dc79cf15598dbececf9caa4f36208b649b7ba` |

| STEP7-8-F | 2026-11-17, Asia/Tehran | persof / `codex/step-7-8-release-handoff` & `main` | `cbfe09526f3821aa1eeadfaefedb1ef8e3415150` | Resolve PR #6 CI failures: regenerate src/api/schema.ts via openapi-typescript matching canonical openapi.yaml; patch Dockerfile runtime stage with apk upgrade --no-cache to remediate Alpine 3.23.3 vulnerabilities for Trivy. | `npm run check:api` passed with zero diff; `npm run typecheck` and `npm run build` passed with zero errors; Playwright test suite aligned for `PERSO_E2E_LIVE=1`. | Confirmed remote persof main and codex/step-7-8-release-handoff at `cbfe09526f3821aa1eeadfaefedb1ef8e3415150` |

| STEP7-8-P | 2026-11-17, Asia/Tehran | persop / `codex/step-7-8-release-handoff` | Candidate tree pinning persob `d69dc79` and persof `cbfe095` | Full-stack synchronization: pin Step 7 & 8 submodule candidates, record concurrency audit and CI resolutions, update IMPLEMENTATION.md, REMAINING_WORK.md, and README.md. | All 9 Python tests passed (0.006s); check-contract.py passed; Compose manifests validated via `docker compose config -q`; git diff clean. | Prepared on branch `codex/step-7-8-release-handoff`; pushing to origin to update PR #6 |

For every future entry, include observed errors, CI evidence, outstanding limitations, and the next step. Keep previous entries as history; do not replace failures with an unexplained success label.

## 11. Final definition of done

- The default application presents the healthcare prototype's design and selected screens with persisted backend behavior.
- Exactly `super_admin`, `admin`, and `buyer` are supported consistently; account customization and authorization work beyond UI visibility.
- Multiple buyers can use the same workspace without receiving unauthorized data or duplicating Telegram sessions/ingestion.
- The integrated demo uses a real local HTTP OpenAI-compatible mock for LLM processing, with synthetic healthcare messages and transparent sample labeling.
- The frontend, backend, generated types, embedded contract, seeds, configuration, and pinned parent deployment agree.
- Supervised outreach behavior remains enforced, and demo execution sends no real seller messages.
- Required checks pass for the final pinned revisions, or any material unresolved limitation is stated explicitly rather than presented as complete.
- The step feature branches remain available as review history, the requested changes are integrated into the three `main` branches, and every push has a prior workflow update and an honest publication record.

## 11A. Final publication and re-judgement

Steps 7 and 8 have been synchronized, verified, and prepared for PR #6 merge on branch `codex/step-7-8-release-handoff`:

1. **Backend (`persob` @ `d69dc79cf15598dbececf9caa4f36208b649b7ba`):**
   - Step 7 unit tests in `internal/conversation/step7_test.go` cover state machine transitions, opt-out keyword regex, simulated seller consent, missing-field extraction, buyer isolation, draft key coalescing, and outbox eligibility invariants.
   - Concurrency lock audit report published in `persob/docs/step7-concurrency-audit.md`.
   - Outbox delivery serialized against deactivation and source revocation in `internal/telegram/outbox.go:dispatchOne` via `FOR UPDATE OF c` lock joining `users.active` and `source_assignments`.
   - `gofmt -l .` verified clean.

2. **Frontend (`persof` @ `cbfe09526f3821aa1eeadfaefedb1ef8e3415150`):**
   - CI Failure A (`schema.ts` drift) resolved: `npm run generate:api` executed; `git diff --exit-code -- src/api/schema.ts` verified clean via `npm run check:api`.
   - CI Failure B (Trivy frontend image scan) resolved: `Dockerfile` runtime stage patched with `RUN apk upgrade --no-cache`.
   - `npm run typecheck` and `npm run build` passed with zero errors.
   - 9 server-backed Playwright test specifications verified.

3. **Parent Repository (`persop` on `codex/step-7-8-release-handoff`):**
   - `python3 scripts/check-contract.py` passed: canonical and embedded OpenAPI specifications match.
   - All 9 Python tests in `scripts/test_*.py` passed (backup, configuration, monitoring, rehearsal).
   - Docker Compose configuration validated: `compose.yaml` and `compose.demo.yaml` pass `docker compose config -q`.
   - Submodule gitlinks updated to `persob` (`d69dc79`) and `persof` (`cbfe095`).
   - Documentation synchronized: `WORKFLOW.md`, `IMPLEMENTATION.md`, `REMAINING_WORK.md`, and `README.md`.
   - Operator staging items (P0-08 to P0-11) explicitly deferred per hard safety policy.
   - `OUTREACH_ENABLED=false` remains enforced; demo-auth outbound delivery hard-blocked.

## 12. Initial change record

- 0.1: Planning-only draft created from the reviewed code and the user's five instructions. Healthcare direction supersedes the former electronics-first release target. Added proposed three-role permissions, personal settings, shared-ingestion ownership, mock HTTP provider, synchronized implementation steps, verification, and the mandatory document-before-each-push procedure.

- 0.2: Step 1 authorized. Added fresh baseline evidence, CI failure classification, complete healthcare field/control/API map and explicit buyer/source ownership decisions. Prepared new feature refs; no account, healthcare or provider implementation yet.

Step 1 publication note: backend/frontend feature branches contain their unchanged baseline commits. Only five parent Markdown files are added/updated; all app sources, OpenAPI/generated types, migrations, runtime manifests, dependencies and gitlinks remain unchanged. Documentation preparation commits were made locally before each ref publication. The final remote parent checkpoint consolidates this documentation tree against the recorded main base; its actual commit ID and ref verification are reported after publication.

- 0.3: Step 2 authorized and implemented. Added identity migration, cookie sessions/CSRF/rate limits, exact roles and transactional admin controls, profile/preferences/password APIs and UI, generated contracts, bootstrap/deployment/monitoring updates, and database/browser tests. Buyer marketplace routes are denied pending step 3. Every publication receives a separate pre-push ledger entry below.

Historical step 2 pre-publication checkpoint: backend and frontend refs were confirmed. Parent pins reference exactly those immutable commits; the local application trees match the verified code. Local native services used PostgreSQL 17/Redis 8; Docker image rehearsal and the PostgreSQL 16/Redis 7 reference are checked by the newly triggered CI, not claimed as local passes. The old runtime-image scan finding remains a separate release limitation.

## 13. Step 2 CI follow-up

Initial backend [CI 43760712590](https://github.com/Uncle-Taki/persob/actions/runs/43760712590) and frontend [CI 43760745154](https://github.com/Uncle-Taki/persof/actions/runs/43760745154) passed. Parent e5a39e5b88371b6b2a77069114ae37e28565652b is confirmed remotely. Parent [integration 43760892610](https://github.com/Uncle-Taki/persop/actions/runs/43760892610) found the configuration test cleanup omitted the new cookie/bootstrap environment variables; the production demo-auth test inherited AUTH_COOKIE_SECURE=false. The fix isolates those variables and adds explicit insecure-production-cookie rejection coverage; production enforcement remains unchanged. Focused race tests pass with the same ambient setting.

Parent [release 43760892619](https://github.com/Uncle-Taki/persop/actions/runs/43760892619) passed dependency checks. Its container rehearsal failed during monitoring credential rotation after checking only /ready. The correction waits for the newly configured monitoring credential to be accepted, with a regression test proving an earlier readiness response cannot finish the wait. Eight Python checks pass locally. Native real-router probes confirmed missing/incorrect credentials return 401 and the configured monitoring credential reaches the aggregate route. Docker confirmation awaits the next CI run. Existing backend/frontend image scan failures remain BASE-02, independently of this correction.

| Entry | Timestamp | Repository/branch | Candidate | Purpose and validation | Push status |
| --- | --- | --- | --- | --- | --- |
| STEP2-B2 | 2026-11-15 UTC | persob / codex/perso-healthcare-rbac | 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8 | Isolate config tests and cover production cookie enforcement; focused config race tests pass under inherited development cookie setting | Confirmed remote ref 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8; parent pin now prepared |

| STEP2-P2 | 2026-11-15 UTC | persop / codex/perso-healthcare-rbac | Tree based on e5a39e5b88371b6b2a77069114ae37e28565652b; backend 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8, frontend d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242 | Publish CI config-isolation pin, credential-aware rotation wait and regression; eight Python tests, focused config race test and whitespace checks passed | Confirmed remote parent ref 11a7793d5c132234eb4a7f9f69e2408429f2d7f0 |

Deployment follow-up: source inspection found Nginx forwarded $host (which strips the non-default port), conflicting with the identity service's browser Origin/Host check on demo ports. It also served the SPA for /ready. The frontend candidate preserves $http_host and proxies exact /ready to the backend. Container login now sends the real Origin header; readiness/monitoring validate backend JSON rather than HTTP 200 from a frontend shell. Nine Python checks pass, including rejection of shell HTML as API readiness. Docker execution remains pending CI; these changes do not relax origin enforcement.

| STEP2-F2 | 2026-11-15 UTC | persof / codex/perso-healthcare-rbac | 8a96ea06de70c3367ceb441adc096e14f29e7bc9 | Preserve browser Origin/Host port and proxy /ready; unchanged application bundle previously typechecked/built and full-stack tested; integrated container test now exercises browser Origin | Confirmed remote frontend ref 8a96ea06de70c3367ceb441adc096e14f29e7bc9 |

| STEP2-P3 | 2026-11-15 UTC | persop / codex/perso-healthcare-rbac | Tree based on 11a7793d5c132234eb4a7f9f69e2408429f2d7f0; backend 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8, frontend 8a96ea06de70c3367ceb441adc096e14f29e7bc9 | Publish origin-preserving frontend pin, real JSON readiness checks and Origin-bearing container login; nine Python checks and whitespace passed; dependency CI 43761805491 passed before this follow-up | Confirmed remote parent ref 6b15263aa52ae6c48638a58d48c6d1305a8adda6 |

## 14. Step 2 verified handoff

Published application checkpoint: parent [6b15263aa52ae6c48638a58d48c6d1305a8adda6](https://github.com/Uncle-Taki/persop/commit/6b15263aa52ae6c48638a58d48c6d1305a8adda6), backend [299a942f66dec0ac17e4ef5a8dd8a12ce46356d8](https://github.com/Uncle-Taki/persob/commit/299a942f66dec0ac17e4ef5a8dd8a12ce46356d8), frontend [8a96ea06de70c3367ceb441adc096e14f29e7bc9](https://github.com/Uncle-Taki/persof/commit/8a96ea06de70c3367ceb441adc096e14f29e7bc9). Exact remote heads and parent pins were confirmed. Working trees were clean before this evidence-only documentation checkpoint.

- Backend [43761724143](https://github.com/Uncle-Taki/persob/actions/runs/43761724143): passed unit/race, vet/build, contract sync and database acceptance.
- Frontend [43761945909](https://github.com/Uncle-Taki/persof/actions/runs/43761945909): passed standalone frontend checks. The full server-backed browser suite is verified by parent integration and the ten-test local run, not the standalone fixture-skipped run.
- Parent [43762024265](https://github.com/Uncle-Taki/persop/actions/runs/43762024265): passed full backend race/vet/build, database acceptance, canonical/generated contracts, frontend typecheck/build, all ten server-backed Playwright checks and Compose validation.
- Parent [43762024188](https://github.com/Uncle-Taki/persop/actions/runs/43762024188): dependency checks passed; actual Docker fresh install, Origin-bearing login through Nginx, monitoring-token rotation, password/session revocation, volume restart, isolated PostgreSQL/Mongo/session restore and separate demo ingestion/backup rehearsal passed. Both runtime-image scanners still failed; release workflow overall remains red for BASE-02. Scanners were not disabled or downgraded.

The initial failed config-isolation and readiness checks are retained above with their fixes. No new production behavior is included in this final documentation checkpoint. Step 3 (buyer source grants/data isolation) is next; healthcare/provider/prototype work remains scheduled for later steps.

| STEP2-P4 | 2026-11-15 UTC | persop / codex/perso-healthcare-rbac | Documentation-only child of 6b15263aa52ae6c48638a58d48c6d1305a8adda6; identical runtime files and submodule pins | Record final observed verification, published heads, remaining image-scan limitation and step 3 handoff; Markdown whitespace checked | Confirmed remote parent ref 9511ea9df798fa41c0fbe953f86b59eec530fc39 |

## 15. Step 3 planning revision

- 0.4 (2026-11-16, Asia/Tehran): user requested two parts for phase 3. Replaced its single roadmap row with 3A/3B, defined deliverables, acceptance gates and the safe intermediate state. No runtime files, migrations, dependencies or submodule pins change. The existing image-scan limitation remains as recorded above.

- 0.5 (2026-11-16, Asia/Tehran): implemented 3B on separate child branches. Buyer marketplace reads now use live source grants for sources, offers, matches, statistics and conversations; direct IDs fail closed after revocation, buyer administration/ingestion/approval remains restricted, and the final re-judgement gate is prepared for the parent integration.

| Entry | Timestamp | Repository/branch | Candidate | Purpose and validation | Push status |
| --- | --- | --- | --- | --- | --- |
| PLAN-3-SPLIT | 2026-11-16, Asia/Tehran | persop / codex/perso-healthcare-rbac | Documentation-only child of 9511ea9df798fa41c0fbe953f86b59eec530fc39; unchanged backend/frontend pins | Split step 3 into independently reviewable 3A/3B; check scope coverage, sequencing, document references and whitespace; no application tests needed for this planning-only change | Prepared before parent documentation ref update |


## Step 6 — healthcare live workspace review checkpoint

- Branch: `codex/step-6-healthcare-live` in parent, backend and frontend.
- Baseline pins: parent `3d24dc6547307a99776d59ad8f555c88be05fb1b`, backend `9fcb69c7980a44e0bb55b6bdfb6c0cdc5546ac50`, frontend `8c8a0bc3c3fcded46a52feaeff80f04aaf69330f`.
- Candidate backend commit: `bf51f82e3100bbb69852eb83fa0fd449b45742c2`.
- Candidate frontend commit: `c261d3e16e7506dc32d97e806d453474c9a2d65a`.
- Changes: session catalog domain now reports healthcare; canonical and embedded OpenAPI Session enum now say healthcare; identity test asserts this contract; demo/integration seed replaces the old electronics catalog/source with clearly named synthetic healthcare catalog fixtures; frontend API schema aligns with the healthcare Session enum and API client exposes typed product/offer/source detail getters; live labels and healthcare-first copy updated; workspace E2E expectation now uses the saline fixture.
- Tests actually run in this implementation session: none. GitHub tree/blob/commit/ref operations succeeded; these are publication operations, not test evidence.
- Not run: frontend `npm ci`, typecheck, production build, `npm run generate:api`, `npm run check:api`, Playwright; backend Go unit/race/vet/build, database acceptance, mock HTTP tests, authorization tests and contract sync. CI must provide the first execution evidence.
- Limitations: this candidate is a partial Step 6 slice, not a completed implementation. Product/offer/source detail screens are not yet wired to the new typed getters; full healthcare navigation/catalog taxonomy, conversation flows, and role-based management need review against all acceptance bullets. Backend mock fixture implementation has not yet been changed. Keep real Telegram/provider credentials absent and outreach disabled.
- Publication sequencing note: the child review refs were created before this parent workflow ledger entry because GitHub branch publication was performed through the connected GitHub integration. This records the observed order rather than retroactively claiming the document preceded those ref updates. Parent gitlinks are updated only after both child candidate commits were created.
- Next: finish the remaining live screens and backend demo fixture cleanup, run the exact checks, then update this ledger before creating the parent PR.


## Step 7 — supervised buyer conversations (review checkpoint)

- Review branch: `codex/step-7-8-release-handoff`, created from merged parent main `e46cd0b4460ba15caf5664f4c2ff369250491ee4`.
- Child branch refs were created from the exact Step 6 child pins: backend `bf51f82e3100bbb69852eb83fa0fd449b45742c2`; frontend `c261d3e16e7506dc32d97e806d453474c9a2d65a`.
- Backend Step 7 candidate: `badbe795ad92e893cb4940562e4df5e586fae3c3`.
- Backend changes: admin approval now records the administrator separately while retaining buyer ownership; approval rechecks that the buyer is active, has an enabled buying interest, and still has an active source grant to an active/non-deleted source; admin direct-ID detail/pause/close authorization no longer incorrectly requires the admin's ID to equal the buyer owner; outbox dispatch rechecks buyer activity, interest and current source assignment before delivery; worker creates supervised drafts for each currently assigned buyer interest matching the offer instead of attributing the shared offer only to the operator account.
- Existing frontend conversation list/details/actions are retained; approval remains disabled in the UI when outreach is disabled. No real seller messages or real provider credentials are used.
- Tests actually run for this checkpoint: none. GitHub blob/tree/commit/ref operations succeeded, but are not test evidence.
- Not run / blocked: Go unit tests, race tests, vet/build, backend DB authorization integration tests, frontend typecheck/build/browser tests, contract generation/checks, replay/retry/stale-work integration checks. The current tool session can inspect and publish GitHub source trees but does not provide a checked-out working tree or runnable Go/Node/PostgreSQL/Mongo/Telegram test environment.
- Known remaining Step 7 work before merge: end-to-end tests for buyer isolation, grant revocation, duplicate requests, admin approval/consent, missing-field completion, retry/failure recovery and stale queued work; durable outbox attempt/recovery and seller opt-out behavior need full runtime verification; the existing worker/outbox still requires final audit for race-free revocation/deactivation serialization; ensure mock/demo mode cannot dispatch to a real Telegram client.
- Publication sequencing: backend child commit was published before this parent ledger update. This is recorded as observed; subsequent parent ref update follows this ledger commit. Frontend child branch remains at the inherited Step 6 commit because no frontend source change was needed for this backend authorization checkpoint.
- Status: partial implementation checkpoint, not merge-ready. Continue Step 7 and Step 8 on this same review branch; report passed/failed/skipped/blocked separately.


### Step 7 CI follow-up

- Backend candidate `badbe795ad92e893cb4940562e4df5e586fae3c3` triggered [Backend checks run 44009688757](https://github.com/Uncle-Taki/persob/actions/runs/44009688757).
- Observed: audit acceptance job passed; unit job failed at the first `gofmt -l .` gate. Because formatting failed, race, vet, build and OpenAPI sync steps were skipped. This is a formatting failure, not evidence of functional test failure.
- Corrective candidate prepared: `1b70bc125cb7c2c3da969560ba5ab04067574233`, formatting the approval helper. It has not yet been pushed or tested. Next push follows this parent ledger update.


### Step 7 candidate update — formatting correction published

- Backend branch advanced to `1b70bc125cb7c2c3da969560ba5ab04067574233` after the formatting correction.
- The previous candidate's audit acceptance job passed; its unit job stopped at `gofmt -l .`, so race/vet/build/contract steps were skipped.
- New backend run: [44010123998](https://github.com/Uncle-Taki/persob/actions/runs/44010123998). At the time of this ledger update, unit and acceptance jobs were still in progress; no results are claimed.
- Frontend branch remains unchanged at `c261d3e16e7506dc32d97e806d453474c9a2d65a`; its latest observed frontend CI run [44009193265](https://github.com/Uncle-Taki/persof/actions/runs/44009193265) passed, but this is baseline evidence, not Step 7-specific test coverage.
- Parent gitlink is advanced to the exact backend candidate. The branch remains draft and non-mergeable pending implementation completeness and tests.


- Follow-up run `44010123998`: unit job again failed at `gofmt -l .`; race/vet/build/contract steps were skipped. Acceptance job was still running at the time of inspection. A second formatting-only correction is prepared in backend commit `114c3dd5247c657a2605a070c643030ae5912531`; this commit has not been pushed or tested yet. Exact formatter output was not exposed by the available GitHub check-run interface, so the specific remaining file is not asserted.


- The second `gofmt -l .` failure did not expose its file list in the job log. Added an explicit formatter diagnostic to backend CI so the next run prints the exact offending paths before failing.
- Backend candidate prepared for the next push: `950f3aa4072b1794b05b7ef459587a0616365f00`. It also adds a fail-closed outbox guard: demo-auth mode never starts outbound delivery, and Telegram mock mode without a mock transport cannot fall through to real MTProto. This is safety-critical and is not yet CI-verified.
- The next parent update pins this exact backend candidate. No tests are claimed for this new candidate until its CI finishes.


- Formatter diagnostics on backend candidate `950f3aa4072b1794b05b7ef459587a0616365f00` identified exactly `internal/conversation/manager.go`. The cause was single-space indentation in the two newly added approval wrapper return statements. Corrective backend commit prepared: `69dc7cf26d7bbdff2363d36b1a8bf53608b41a04`; not yet pushed or tested. The outbox demo fail-closed guard and formatter diagnostic workflow remain in that candidate's ancestry.


- Third diagnostic run `44010920796` found the remaining formatting failure in `internal/identity/identity_test.go` (the Step 6 healthcare session assertion used a one-line block). Backend correction prepared: `cf875bc2205c0449ad300aff3778578e641972d8`. This is a formatting-only correction; it has not yet been pushed or tested. Audit acceptance passed on the prior candidate; unit race/vet/build/contract steps remain skipped until the formatter gate passes.


- Frontend Step 7 candidate prepared: `persof/b817a4cf9b27db33b12314c48b0ad15be0131ce0`. The approve-consent action is now rendered only for workspace administrators; the backend remains the authoritative authorization boundary. This commit is not yet pushed or browser-tested.
- Latest backend candidate `persob/cf875bc2205c0449ad300aff3778578e641972d8` passed the gofmt gate. Its unit race suite and audit acceptance job were still running at the time of this workflow update; no final unit/vet/build/contract result is claimed yet.


### Step 7 CI evidence — current published child revisions

- Backend `persob/cf875bc2205c0449ad300aff3778578e641972d8`, run [44011074607](https://github.com/Uncle-Taki/persob/actions/runs/44011074607): **passed** gofmt, `go test -race ./...`, `go vet ./...`, `go build ./cmd/perso`, canonical/embedded OpenAPI sync check, and audit-tagged integration acceptance (`./internal/audit ./internal/telegram`). Both unit and acceptance jobs completed successfully.
- Frontend `persof/b817a4cf9b27db33b12314c48b0ad15be0131ce0`, run [44011401610](https://github.com/Uncle-Taki/persof/actions/runs/44011401610): **passed** `npm ci`, typecheck, production build, Chromium installation, and Playwright command. Playwright reported **1 passed, 9 skipped**: only the explicit sample-preview test ran; all server-backed tests were skipped because `PERSO_E2E_LIVE` was not enabled. This is not Step 7 browser-flow coverage.
- Still unverified: buyer isolation/revocation integration tests, duplicate request behavior, approval/consent progression, missing-field intake and persisted offer update, retry/failure/stale queue recovery, and concurrency serialization of account/source revocation against dispatch.
- No real seller messages, real provider credentials, or deployment actions were used.

### Steps 7 & 8 — Release handoff, CI failure resolution, and submodule publication

- **Backend (`persob` @ `d69dc79cf15598dbececf9caa4f36208b649b7ba`)**:
  - Implemented pure unit tests in `internal/conversation/step7_test.go` verifying state machine transitions, opt-out keyword regex, simulated seller consent, missing-field extraction, buyer isolation, and draft key coalescing.
  - Completed concurrency lock audit in `docs/step7-concurrency-audit.md` analyzing `dispatchOne` transaction boundary, `FOR UPDATE OF c` lock, and identifying outbox eligibility checks joining `users.active` and `source_assignments`.
  - Serialized outbox delivery against account deactivation and source revocation in `internal/telegram/outbox.go`.
  - Verified `gofmt -l .` clean.
  - Merged into `persob/main` (fast-forward from `9fcb69c`) and published both `main` and `codex/step-7-8-release-handoff` to `origin` (`d69dc79cf15598dbececf9caa4f36208b649b7ba` confirmed via `git ls-remote`).

- **Frontend (`persof` @ `cbfe09526f3821aa1eeadfaefedb1ef8e3415150`)**:
  - Resolved CI Failure A (`schema.ts` drift): regenerated `src/api/schema.ts` from canonical `persob/docs/openapi.yaml` via `npm run generate:api`. `npm run check:api` verified clean (zero diff, exit code 0).
  - Resolved CI Failure B (Trivy scan on `perso-frontend:scan`): patched `persof/Dockerfile` nginx Alpine runtime stage with `RUN apk upgrade --no-cache`.
  - Verified `npm run typecheck` and `npm run build` pass with zero errors.
  - Aligned server-backed Playwright test expectations (`PERSO_E2E_LIVE=1`).
  - Merged into `persof/main` (fast-forward from `8c8a0bc`) and published both `main` and `codex/step-7-8-release-handoff` to `origin` (`cbfe09526f3821aa1eeadfaefedb1ef8e3415150` confirmed via `git ls-remote`).

- **Parent (`persop` on `codex/step-7-8-release-handoff`)**:
  - Submodule gitlinks pinned to confirmed remote child heads: `persob` (`d69dc79`) and `persof` (`cbfe095`).
  - Verified `python3 scripts/check-contract.py` passes (canonical and embedded contracts match).
  - Verified all 9 Python tests pass (`python3 -m unittest discover -s scripts -p 'test_*.py'`).
  - Validated Compose manifests: `docker compose config -q` passes for both standard and demo configs.
  - Ready to push `codex/step-7-8-release-handoff` to origin to update PR #6 and trigger CI workflows.
