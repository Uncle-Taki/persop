# Perso healthcare app — implementation workflow

Version: 0.3 — step 2 identity implementation
Prepared: 2026-11-15, Asia/Tehran
Status: STEP 2 IMPLEMENTED; final verification and publication in progress. Individual password accounts, sessions, roles, customization and minimal account UI are included. Step 3 source assignments and subsequent healthcare/provider work remain pending.
Feature branch in all three repositories: `codex/perso-healthcare-rbac`
Canonical repository path: `persop/docs/WORKFLOW.md`

## 1. Requested outcome

Build the final Perso app around the existing healthcare prototype, with synchronized frontend and backend behavior, real user accounts, exactly three roles (`super_admin`, `admin`, `buyer`), and a local mock OpenAI-compatible API for demo LLM processing. Implement in small, reviewable steps on new branches after the planning pass. Update this workflow document before every git push.

The healthcare prototype is the product and visual reference for the final application, not merely an optional sample hidden behind an electronics application. Its Persian-first layout, Vazirmatn font, pastel Clinical Mint palette, responsive desktop layout, and five-tab mobile bottom navigation should carry into the server-backed app.

Keep the existing supervised outreach workflow: explicit configuration, human approval, seller consent, opt-out handling, and durable delivery tracking. This plan does not authorize deployment, merging to main, or sending messages to real sellers.

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
| 2 | User identity, sessions, exact roles, personal settings, minimal account UI | Backend + frontend; parent pins | Login/logout, profile/preferences persistence, role enforcement, admin/buyer management, forbidden actions, session revocation, safe legacy-user migration | Complete; backend/frontend published; final parent ref prepared |
| 3 | Buyer authorization and shared-ingestion data model | Backend + frontend assignments UI | Two buyers receive only authorized sources/offers/matches/stats/conversations; background jobs respect ownership; replay creates no duplicate shared listings; unauthorized totals do not leak | Not started |
| 4 | Healthcare catalog, attributes, extraction, matching, and compatible price analytics | Backend + frontend catalog/interests | Catalog CRUD, Persian/English aliases, per-item price association, units/specs/expiry, filter persistence, healthcare defaults; existing data retained | Not started |
| 5 | OpenAI-compatible adapter and local mock API | Backend + parent demo composition | Real HTTP request verified; valid extraction/question responses; auth, timeout, 429/5xx, malformed-output and disabled-provider behavior tested; no external credentials needed | Not started |
| 6 | Healthcare prototype promoted into the main server-backed UI | Frontend + backend contract adjustments | Main entry shows healthcare UI; all selected prototype screens use APIs; responsive RTL/LTR; roles, loading/error/empty states and preferences work; no hidden sample fallback | Not started |
| 7 | Buyer-scoped, supervised conversations through the same provider/queue path | Backend + frontend + demo fixtures | Match → draft/request → admin approval → simulated seller consent → missing-field intake → persisted offer update; opt-out, permission revocation, dedupe and failed delivery visible | Not started |
| 8 | Full-stack synchronization and release-ready handoff | All three | Exact pinned stack passes applicable checks; isolated demo boots; docs/config/backup paths updated for users and provider; branch changes summarized; deployment remains a separate action | Not started |

Dependencies: finish identity before buyer scoping; finish scoping before exposing data to multiple buyers; establish healthcare contracts before completing the mock fixture schema; integrate existing prototype pages progressively rather than maintaining a second disconnected live implementation. Maintain a working integrated checkpoint after each push.

At step 6, cover the prototype's offers, product details, price comparison, interests/add product, Telegram sources/add source/source details, conversations/details, and settings. Product creation belongs to administrative permissions; a buyer's add-product flow selects from the catalog. Add account/user-management screens according to role. Prototype metrics or badges lacking a real implementation must be removed or clearly marked unavailable.

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

Once implementation is requested, create `codex/perso-healthcare-rbac` from the verified baseline in each affected repository. Do not change `main`, merge, or deploy as part of these feature pushes. Check for an existing branch before choosing the name and preserve unrelated work.

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

Current checkpoint: step 2 — implementation and ten full-stack browser checks complete; full backend race run passed; all three published; CI follow-up fixes in progress.
Confirmed starting branch heads: parent a4ec4d8f23404f8bddb4f3d56f13dcbc1567f8ae; backend 33aac438d760d0d293e907cf8892775bbaeca222; frontend 9cb867d5cffbd529aaff12ea6485a28da693bc21.
Feature branch: `codex/perso-healthcare-rbac` in all three repositories.
Next step: step 3, shared ingestion/source assignments and buyer-specific data visibility. It is not included in step 2.
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

For every future entry, include observed errors, CI evidence, outstanding limitations, and the next step. Keep previous entries as history; do not replace failures with an unexplained success label.

## 11. Final definition of done

- The default application presents the healthcare prototype's design and selected screens with persisted backend behavior.
- Exactly `super_admin`, `admin`, and `buyer` are supported consistently; account customization and authorization work beyond UI visibility.
- Multiple buyers can use the same workspace without receiving unauthorized data or duplicating Telegram sessions/ingestion.
- The integrated demo uses a real local HTTP OpenAI-compatible mock for LLM processing, with synthetic healthcare messages and transparent sample labeling.
- The frontend, backend, generated types, embedded contract, seeds, configuration, and pinned parent deployment agree.
- Supervised outreach behavior remains enforced, and demo execution sends no real seller messages.
- Required checks pass for the final pinned revisions, or any material unresolved limitation is stated explicitly rather than presented as complete.
- All implementation work is on the new branches, and every push has a prior workflow update and an honest publication record.

## 12. Initial change record

- 0.1: Planning-only draft created from the reviewed code and the user's five instructions. Healthcare direction supersedes the former electronics-first release target. Added proposed three-role permissions, personal settings, shared-ingestion ownership, mock HTTP provider, synchronized implementation steps, verification, and the mandatory document-before-each-push procedure.

- 0.2: Step 1 authorized. Added fresh baseline evidence, CI failure classification, complete healthcare field/control/API map and explicit buyer/source ownership decisions. Prepared new feature refs; no account, healthcare or provider implementation yet.

Step 1 publication note: backend/frontend feature branches contain their unchanged baseline commits. Only five parent Markdown files are added/updated; all app sources, OpenAPI/generated types, migrations, runtime manifests, dependencies and gitlinks remain unchanged. Documentation preparation commits were made locally before each ref publication. The final remote parent checkpoint consolidates this documentation tree against the recorded main base; its actual commit ID and ref verification are reported after publication.

- 0.3: Step 2 authorized and implemented. Added identity migration, cookie sessions/CSRF/rate limits, exact roles and transactional admin controls, profile/preferences/password APIs and UI, generated contracts, bootstrap/deployment/monitoring updates, and database/browser tests. Buyer marketplace routes are denied pending step 3. Every publication receives a separate pre-push ledger entry below.

Step 2 pre-publication checkpoint: backend and frontend refs are confirmed. Parent pins reference exactly those immutable commits; the local application trees match the verified code. Local native services used PostgreSQL 17/Redis 8; Docker image rehearsal and the PostgreSQL 16/Redis 7 reference are checked by the newly triggered CI, not claimed as local passes. The old runtime-image scan finding remains a separate release limitation.

## 13. Step 2 CI follow-up

Initial backend [CI 43760712590](https://github.com/Uncle-Taki/persob/actions/runs/43760712590) and frontend [CI 43760745154](https://github.com/Uncle-Taki/persof/actions/runs/43760745154) passed. Parent e5a39e5b88371b6b2a77069114ae37e28565652b is confirmed remotely. Parent [integration 43760892610](https://github.com/Uncle-Taki/persop/actions/runs/43760892610) found the configuration test cleanup omitted the new cookie/bootstrap environment variables; the production demo-auth test inherited AUTH_COOKIE_SECURE=false. The fix isolates those variables and adds explicit insecure-production-cookie rejection coverage; production enforcement remains unchanged. Focused race tests pass with the same ambient setting.

Parent [release 43760892619](https://github.com/Uncle-Taki/persop/actions/runs/43760892619) passed dependency checks. Its container rehearsal failed during monitoring credential rotation after checking only /ready. The correction waits for the newly configured monitoring credential to be accepted, with a regression test proving an earlier readiness response cannot finish the wait. Eight Python checks pass locally. Native real-router probes confirmed missing/incorrect credentials return 401 and the configured monitoring credential reaches the aggregate route. Docker confirmation awaits the next CI run. Existing backend/frontend image scan failures remain BASE-02, independently of this correction.

| Entry | Timestamp | Repository/branch | Candidate | Purpose and validation | Push status |
| --- | --- | --- | --- | --- | --- |
| STEP2-B2 | 2026-11-15 UTC | persob / codex/perso-healthcare-rbac | 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8 | Isolate config tests and cover production cookie enforcement; focused config race tests pass under inherited development cookie setting | Confirmed remote ref 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8; parent pin now prepared |

| STEP2-P2 | 2026-11-15 UTC | persop / codex/perso-healthcare-rbac | Tree based on e5a39e5b88371b6b2a77069114ae37e28565652b; backend 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8, frontend d1a413bfbafb3dfbbb3bf2b27f9f9aeecc59a242 | Publish CI config-isolation pin, credential-aware rotation wait and regression; eight Python tests, focused config race test and whitespace checks passed | Confirmed remote parent ref 11a7793d5c132234eb4a7f9f69e2408429f2d7f0 |

Deployment follow-up: source inspection found Nginx forwarded $host (which strips the non-default port), conflicting with the identity service's browser Origin/Host check on demo ports. It also served the SPA for /ready. The frontend candidate preserves $http_host and proxies exact /ready to the backend. Container login now sends the real Origin header; readiness/monitoring validate backend JSON rather than HTTP 200 from a frontend shell. Nine Python checks pass, including rejection of shell HTML as API readiness. Docker execution remains pending CI; these changes do not relax origin enforcement.

| STEP2-F2 | 2026-11-15 UTC | persof / codex/perso-healthcare-rbac | 8a96ea06de70c3367ceb441adc096e14f29e7bc9 | Preserve browser Origin/Host port and proxy /ready; unchanged application bundle previously typechecked/built and full-stack tested; integrated container test now exercises browser Origin | Confirmed remote frontend ref 8a96ea06de70c3367ceb441adc096e14f29e7bc9 |

| STEP2-P3 | 2026-11-15 UTC | persop / codex/perso-healthcare-rbac | Tree based on 11a7793d5c132234eb4a7f9f69e2408429f2d7f0; backend 299a942f66dec0ac17e4ef5a8dd8a12ce46356d8, frontend 8a96ea06de70c3367ceb441adc096e14f29e7bc9 | Publish origin-preserving frontend pin, real JSON readiness checks and Origin-bearing container login; nine Python checks and whitespace passed; dependency CI 43761805491 passed before this follow-up | Prepared before parent ref update |
