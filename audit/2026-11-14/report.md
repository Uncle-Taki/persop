# Perso independent principal audit — 14 November 2026

## 1. Executive Summary

**Verdict: NOT READY.** The intended technologies are present and a clean local mock stack now starts, but the system does not yet operate as one product. In the clean Compose stack, health/readiness and the Nginx offers proxy return 200, while adding/resolving a Telegram source returns 503 because the API has no connected Telegram resolver. The React UI is a medical-supply demo backed by in-memory fixtures; Compose serves a different legacy dashboard. Nine of the opt-in PostgreSQL/Redis acceptance assertions still fail after safe fixes.

No live Telegram account or Gemini key was available. Live Telegram classification, authorization, update delivery and live LLM behavior therefore remain unverified. The working end-to-end result is a synthetic mock channel message that traverses MongoDB → Redis Stream → worker → PostgreSQL and appears through the legacy web proxy.

There are no known open P0 findings after the auth fix. The P1 findings below still prevent internal testing as an integrated product.

## 2. Architecture Overview

The repository has the requested main components: React/Vite/TypeScript in persof; a Go executable with api, collector and worker commands in persob; gotd/td MTProto; MongoDB for messages and extraction records; PostgreSQL for users, products, sources, offers, matches and conversations; Redis Streams; Docker Compose; and a Gemini provider.

Responsibility boundaries are recognizable, but process boundaries do not carry the Telegram client/resolver or outbound sender. The Compose API process, collector and worker each construct their own objects. The resolver becomes real only after the collector enters its MTProto loop, while the API subcommand never enters that loop. The worker also has no real Telegram sender. The configured LLM provider currently accepts Gemini only. These are concrete integration gaps; no replacement architecture is recommended.

Compose’s frontend service mounts persob/web into Nginx. It does not build or serve persof. The latter is a separate, locally renderable UI prototype.

## 3. Frontend Design and Mobile UX Results

I rendered the React app in Chromium at each requested size. It is Persian-first and RTL, defaults to Best Offers, has five bottom tabs, needs no product pictures, and had no horizontal page overflow or browser page errors. The initial screen showed 2 complete offer cards at 360×800, 3 at 390×844, 4 at 430×932 and 9 at 1440×900. At 360px, the next card is partially covered by the fixed bottom navigation. The desktop view has no left sidebar.

Screenshots:
- [360×800 Best Offers](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/best-offers-360x800.png)
- [390×844 Best Offers](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/best-offers-390x844.png)
- [430×932 Best Offers](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/best-offers-430x932.png)
- [1440×900 Best Offers](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/best-offers-1440x900.png)
- [Telegram Sources](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/telegram-sources-390x844.png)
- [Conversations](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/conversations-390x844.png)
- [Settings](/home/mehdi/Project/leela/persop/audit/2026-11-14/screenshots/settings-390x844.png)

The rendered mint palette is coherent but does not use the requested tokens. Main UI colors include #5F978B, #477D72, #A9D5C5, #D9EEE5, #F7FAF8, #263D38, #718780 and #E1EBE5 rather than the specified Clinical Mint values. Measured white text on #5F978B was 3.34:1; #718780 on white was 3.83:1, below the 4.5:1 normal-text target. The browser audit counted 165 controls below 44px in at least one dimension across the inspected React screens; this flags tap-target review, not a claim that every control violates WCAG minimum target sizing. At 390px all three initial cards fit without overlap.

The look is text-first and uses no required product imagery, but dense cards and many hard-coded Tailwind colors weaken the requested Notion × Stripe polish and token consistency. The 390px experience is the strongest of the four sizes.

## 4. Telegram Integration Results

The backend uses gotd/td and inspects actual Telegram entity constructors. The resolver distinguishes Channel broadcast, megagroup and forum flags, and uses ChannelFull for linked chat metadata. Telegram’s official schema describes these flags and the linked_chat_id field in [channel](https://core.telegram.org/constructor/channel) and [channelFull](https://core.telegram.org/constructor/channelFull); [channels.getFullChannel](https://core.telegram.org/method/channels.getFullChannel) is the relevant lookup.

Private invite resolution checks the invite and rejects ingestion when the connected account has not joined; it does not auto-join. Public/private visibility is represented separately from peer type. Invalid resolutions are sanitized before returning to clients. The API handler re-resolves client input and persists the detected type, rather than trusting supplied peer metadata.

Those checks are not reachable in the deployed split-process composition: the clean-stack request to POST /api/v1/sources/resolve returned 503 “Telegram resolver is unavailable.” There are mock resolver tests but no live Telegram credentials/session test. The repository has session encryption storage but no implemented first-login authorization flow; an unauthorized account waits for cancellation. Do not treat source addition as live-tested.

## 5. Source Type Classification Results

The Go enum covers Basic Group, Supergroup, Forum and Broadcast Channel. Linked discussion is represented as a relationship/capability, not a peer type, which is the correct model. Real resolver code uses gotd’s entity flags and rejects type mismatches; invite and account access are separate from entity classification. Mock regression tests now check invalid client metadata, mismatches, unavailable clients and numeric peer IDs without a verified entity cache.

A linked discussion’s peer ID is discovered for public resolved channels when full-channel lookup succeeds. Lookup failure is silently treated as no discussion, and the invite-already-member path reports the link flag but does not retrieve/store the linked peer ID. No private/public linked-discussion live case was exercised. Most importantly, the actual API process has no usable resolver.

## 6. Ingestion and Synchronization Results

Adapters are split by basic group, supergroup, forum, broadcast channel and linked discussion. Forum topic roots and replies are preserved in fixtures; broadcast-channel posts do not receive a fabricated personal sender; Telegram message timestamps and media metadata are retained. This audit also found and fixed group adapters that labeled every sender as a user. They now leave non-user/missing sender IDs unset and preserve the sender kind; the added regression test passes.

Only gotd new-message and edit-message callbacks are registered. There is no initial getHistory paging, delete-update handler, durable gap replay, or active FloodWait backoff call site. The helper for flood waits is not wired into update handling. Reconnect behavior depends on gotd’s client loop and was not validated against a real session. Checkpoint updates happen after Mongo/Redis writes; discussion messages intentionally do not advance the channel checkpoint.

Redis consumer group creation was corrected to start at message ID 0 so a new group does not skip existing backlog. Failed callbacks remain pending, but the consumer reads only “>” and never claims pending messages from a prior attempt/consumer. The audit reproduced one handler invocation after a transient failure and zero invocations after consumer restart.

## 7. MongoDB Audit

The raw message collection has a unique compound identity on Telegram chat/peer ID and message ID, plus indexes for processing status, received time, source, topic and linked post. Upsert uses a pipeline to preserve first-seen original text while replacing current message text and edit metadata. A real MongoDB fixture test passed after the edit fix. Required index creation now fails startup instead of merely warning.

Source ID is a string reference, not a foreign key, and can be empty for messages that do not resolve through the normalized source registry. Telegram message entity formatting is modeled but not populated by the adapters. Media stores metadata only. Raw messages, LLM extraction prompt/response fields and conversation histories have no configured retention/deletion policy or TTL index. No duplicate was observed in the edit upsert test.

## 8. PostgreSQL Audit

Migrations define users/interests, products/aliases, legacy and normalized sources, offers, price observations/aggregates, seller profiles, matches, conversations and audit logs with their core foreign keys and indexes. A clean fresh-volume Compose project started; the app migrations completed and the seeded database contained 5 products, 1 user and 1 source. Concurrent fresh migration assertions pass after adding an advisory lock and fixing extension schema selection. Demo seed SQL was moved out of migrations into the first-boot Compose init order.

Nine remaining acceptance failures reveal data integrity/statistics defects:
- One offer row per source message prevents retaining multiple products from one message.
- Replaying an unchanged offer creates a duplicate price observation.
- Comparisons average raw Rial and Toman numbers together.
- Expired offers remain in active price statistics.
- Best-offer sorting happens after SQL pagination.
- Conversation initialization creates duplicate rows for one offer.

Price, currency, condition, quantity and listing status columns lack CHECK constraints for valid ranges/enums. Price comparisons by condition, city and brand use raw amounts, so the mixed-currency issue affects all three. There is no distinct median-by-city/brand support in the inspected comparison endpoints. Rial/Toman normalization is not consistently applied.

## 9. LLM Pipeline Audit

The worker runs deterministic classification/extraction and optionally enriches through Gemini. The pipeline persists extraction in Mongo, matches products, upserts offers and attempts interest matches. The Gemini path uses a system extraction instruction, wraps input as untrusted, places the key in a request header, limits response bytes, validates schema values and verifies that evidence spans occur in the original text. Unit tests pass for buyer messages, English/mixed-language cases, prompt-injection extraction input, invalid model output and retry cancellation. These checks do not prove semantic truth: substring evidence only proves the cited text exists.

The deterministic extractor recognizes a narrow list of electronic brands/models. The React fixtures are medical supplies and do not match that catalog. The deterministic extractor sets Branded=true for every extracted message and assigns manufacturer=brand, so missing seller facts become affirmative offer data. It does not extract expiration date. Conversation intake only asks for price/city/Tehran area; it does not request condition, branded status, manufacturer or expiration.

Multiple products and prices are not linked by evidence spans. The worker pairs prices by array index, reuses the first price for later products when fewer prices exist, and the offer schema then collapses the rows by source message ID. Gemini is disabled in the Compose audit run; no live Gemini API call was made.

Extraction input has a system instruction. Conversation consent/question generation uses seller text and history interpolated into a user prompt without a separate system instruction; ambiguous consent falls back to model judgment. A crafted reply could try to influence whether the model returns consent=true. No consent-injection test exists. The deterministic opt-out/refusal precedence unit case passes, but this separate prompt path is not secured by the extraction test.

## 10. Conversation Workflow Audit

The state and history models persist to PostgreSQL and MongoDB. The initial consent message identifies the sender as Perso’s automated assistant. Opt-out and cooldown checks exist in manager code. However, the worker constructs the manager with no real Telegram client in the split deployment; update dispatch never routes incoming seller replies to HandleIncomingSellerMessage; send errors are ignored while the persisted history marks messages Delivered=true; and collected values are never applied back to the offer.

Only three missing fields are produced (price, seller city, Tehran area), while the requested flow has seven. The configured default is three questions. Duplicate conversation creation for the same offer was reproduced twice. SetCooldown exists as a repository method but is not called; no quiet-hours or outbound-rate limiter is wired. Approval, consent, field progression, restart recovery, opt-out on real inbound updates and termination were not proven end to end.

## 11. Frontend/Backend API Compatibility

| Feature | React frontend | Go backend | Database/worker | Result |
|---|---|---|---|---|
| Add source | Simulated auto-detect; in-memory | Resolve/create endpoints; API process resolver unavailable | Normalized source table | Broken in Compose; runtime resolve is 503 |
| Resolve type | UI enum includes “group” | Expects basic_group/supergroup/forum/broadcast_channel | Stored detected type and capabilities | Enum mismatch; React does not call backend |
| List sources | Initial mock data | Owner-scoped normalized and legacy routes | PostgreSQL | Backend exists; React remains mock |
| Pause/resume | Local state only | PUT status route with owner check | PostgreSQL status | React disconnected |
| Fetch messages | No API calls | No raw-message listing endpoint | Raw messages in Mongo | Not integrated/exposed |
| LLM extraction | Simulated/sample state | Worker-only optional Gemini | Extraction in Mongo | React disconnected; Gemini not live-tested |
| Interest matching | Local sample data | Worker + match API | PostgreSQL | Backend path exists; React disconnected |
| Best offers | Static INITIAL_OFFERS | Offers endpoint, scoring after page limit | PostgreSQL | Proxy works; UI sample is not backend data |
| Price comparison | Fixture calculations | Comparison/statistics endpoints | PostgreSQL aggregates | Endpoint exists; unit/expiry issues remain |
| Conversations | Timers and mock threads | State endpoints and manager | PostgreSQL + Mongo | Inbound/outbound workflow disconnected |

The clean Compose Nginx proxy returned HTTP 200 for /api/v1/offers. The source resolver returned 503. The React app issued zero API requests in browser inspection. The legacy dashboard does call backend APIs, but the default Compose configuration has production environment and demo auth disabled, so API v1 requests are rejected until a real authentication provider is supplied.

Runtime evidence is saved in [runtime-after-fixes.log](/home/mehdi/Project/leela/persop/audit/2026-11-14/evidence/runtime-after-fixes.log).

OpenAPI copies now parse as YAML, contain 28 paths each and are identical. A full OpenAPI schema validator was not run. API errors, pagination and nullability are not consistent across handlers. Currency is represented by unit names in API values without a uniform normalization boundary.

## 12. Security Findings

The audit reproduced anonymous and spoofed X-User-ID access before the patch: an untrusted identity reached a protected API and returned 200. This was changed to fail closed (401 by default); local demo access is an explicit development/test opt-in and ignores X-User-ID. Owner checks were added to normalized source reads/status changes. This fixes the bypass, but production still lacks a real identity provider and currently denies all API v1 requests.

A stored/reflected XSS payload in legacy web data executed before the fix. Dynamic values are now escaped before innerHTML rendering and user-controlled source values moved to data attributes; the same browser payload no longer executed. The code still uses innerHTML, so future dynamic fields must keep escaping.

Ports for PostgreSQL, MongoDB, Redis, backend and Nginx bind to loopback in Compose. Database default passwords and the Telegram session key are known development placeholders; Compose labels its default environment production and does not fail if placeholder DB passwords are retained. Redis has no password but is loopback-published and inside the Compose network. CORS allows any origin. SQL query values are parameterized in the inspected offer/source paths; no SQL injection was reproduced.

A tracked-history high-confidence secret-pattern scan found no matches. Its scope was tracked text in local commits; it did not inspect environment values, remote objects or entropy-based secrets. Do not treat it as proof that no secrets exist. LLM remains disabled by default. No retention policy is present for Telegram or seller conversation data.

## 13. Docker and Deployment Results

Docker Compose v2 built the Go image and started a new project with fresh named volumes. PostgreSQL, MongoDB and Redis became healthy; backend API became healthy; Nginx, collector and worker stayed up. The first-boot schema/seed ordering worked, migrations completed, and counts were products=5, users=1, sources=1. /ready returned 200 and the frontend proxy returned 200 for /api/v1/offers. The explicit mock collector injected a synthetic message; the worker persisted a sample offer visible through the proxy. This validates the mock stack only.

The legacy Docker Compose v1 client failed recreation with KeyError ContainerConfig; Docker Compose v2 succeeded. The source Compose file is structurally valid, database/API ports bind to localhost, and volumes are named. Health checks cover databases and API, not collector/worker. Default Compose values leave Telegram mock mode false with Telegram app ID 0 and no live credentials; real collector startup is therefore not a usable clean production path. The API process also lacks the connected client as described above. LLM is disabled by default.

## 14. Automated Test Results

- Go unit suite: PASS after the sender-attribution patch; all packages passed.
- Go race suite: PASS after the sender-attribution patch; all packages passed.
- Go vet and Go build: PASS after the sender-attribution patch. The sandbox Go module cache emitted a read-only stat-cache warning during build, but the command exited 0.
- Frontend npm install: initial dependency resolution failed with ERESOLVE; esbuild compatibility was corrected and package-lock added.
- Frontend TypeScript check (npm run lint): PASS; this script runs tsc --noEmit, not ESLint.
- Frontend production build: PASS (Vite emits a config-loader warning about __dirname).
- Frontend unit tests/ESLint: not available; no npm test or ESLint script.
- OpenAPI YAML parsing: PASS for both identical 28-path files; full schema validator not run.
- Audit acceptance against disposable PostgreSQL/MongoDB/Redis: 18 assertions PASS and 9 FAIL after fixes. Failures: multi-product offers; duplicate history; currency normalization; expired-offer exclusion; ranking before pagination; duplicate conversation prevention; Redis retry; medical catalog compatibility; pending-work recovery. The backlog-start and Mongo edit assertions now pass.
- Live Telegram and live Gemini: NOT EXECUTED; credentials/session were unavailable.
- The final sender regression test passed in the normal and race-enabled Go suites.
- Post-patch Go and Docker image build results are recorded in [final-verification.log](/home/mehdi/Project/leela/persop/audit/2026-11-14/evidence/final-verification.log).

## 15. P0/P1/P2/P3 Issue Register

Each entry states the observed behavior, expected behavior, reproduction, cause, recommendation, fix status and post-fix verification.

### P0-01 — Protected API trusted caller-controlled identity (fixed)

**Affected / reference:** API identity middleware, [middleware.go:45](/home/mehdi/Project/leela/persop/persob/internal/api/middleware.go:45), [auth_audit_test.go:15](/home/mehdi/Project/leela/persop/persob/internal/api/auth_audit_test.go:15).  
**Observed:** Before the patch, requests with no identity and with an arbitrary X-User-ID both received 200 on a protected route.  
**Expected:** Identity must come from a verified auth mechanism; anonymous users must not access protected data.  
**Reproduction:** The baseline regression log shows both requests accepted.  
**Root cause:** The development mock middleware trusted request data as identity.  
**Recommended fix:** Use a real authentication provider; until then fail closed and never trust X-User-ID.  
**Fix applied:** Yes. API v1 defaults to 401; optional demo identity is static, local-only and ignores caller identity.  
**Test after fix:** PASS in Go auth regression tests and full unit suite before final adapter-only edit. Production authentication remains a separate P1 blocker below.

### P1-01 — Production authentication provider is absent

**Affected / reference:** [middleware.go:47](/home/mehdi/Project/leela/persop/persob/internal/api/middleware.go:47), [router.go:50](/home/mehdi/Project/leela/persop/persob/internal/api/router.go:50), [docker-compose.yml:71](/home/mehdi/Project/leela/persop/persob/docker-compose.yml:71).  
**Observed:** With default demo auth false, every API v1 request is rejected; enabling demo auth assigns one fixed identity to every local caller.  
**Expected:** Authenticated users with ownership-scoped authorization.  
**Reproduction:** Run with DEMO_AUTH_ENABLED=false and call GET /api/v1/offers; expect 401.  
**Root cause:** No real session/token verifier or user identity mapping is implemented.  
**Recommended fix:** Add the intended identity provider and test per-user isolation before any shared or production deployment.  
**Fix applied:** Fail-closed behavior is applied; provider is not.  
**Test after fix:** Secure-deny unit test PASS; authenticated product flow BLOCKED.

### P1-02 — Source-resolution API has no connected Telegram resolver

**Affected / reference:** [main.go:155](/home/mehdi/Project/leela/persop/persob/cmd/perso/main.go:155), [collector.go:72](/home/mehdi/Project/leela/persop/persob/internal/telegram/collector.go:72), [collector.go:164](/home/mehdi/Project/leela/persop/persob/internal/telegram/collector.go:164), [source.go:30](/home/mehdi/Project/leela/persop/persob/internal/api/handlers/source.go:30).  
**Observed:** Clean Compose API returns 503 for source resolution while health/readiness report healthy.  
**Expected:** Resolve using the already authorized account and return verified entity/capability metadata.  
**Reproduction:** Start the audit Compose stack and POST /api/v1/sources/resolve with a Telegram address; observed 503 “Telegram resolver is unavailable.”  
**Root cause:** The API subcommand passes a resolver created with nil client; only the collector’s separate process later replaces its own resolver.  
**Recommended fix:** Add a deliberate API-to-collector resolver contract or shared authorized-client lifecycle.  
**Fix applied:** No; synthetic fallback was removed to prevent false verification.  
**Test after fix:** Runtime reproduction still FAILS as expected; resolver unit tests fail closed.

### P1-03 — React frontend is disconnected and describes another marketplace

**Affected / reference:** [App.tsx:44](/home/mehdi/Project/leela/persop/persof/src/App.tsx:44), [mockData.ts:686](/home/mehdi/Project/leela/persop/persof/src/data/mockData.ts:686), [AddTelegramSourcePage.tsx:47](/home/mehdi/Project/leela/persop/persof/src/pages/AddTelegramSourcePage.tsx:47), [docker-compose.yml:185](/home/mehdi/Project/leela/persop/persob/docker-compose.yml:185).  
**Observed:** React reads INITIAL_* arrays, simulates source detection and conversation timers, and makes zero API calls. Its catalogue is medical devices/supplies; backend deterministic extraction/catalog is electronics. Compose serves a different legacy HTML dashboard.  
**Expected:** The rendered product UI should consume the same API and data model the backend exposes.  
**Reproduction:** Render React and inspect network; zero API requests. Start Compose; Nginx mounts web/ rather than the React build. Add a React Telegram source; mock detector supplies UI-local metadata.  
**Root cause:** The two implementations were developed as separate prototypes without an API adapter/integration phase.  
**Recommended fix:** Agree one product catalog and API schema, replace fixtures with typed API clients and deploy the React build.  
**Fix applied:** No.  
**Test after fix:** TypeScript/build PASS, integration FAIL; audit acceptance marks medical product unsupported.

### P1-04 — Telegram cannot onboard a clean real account or backfill history

**Affected / reference:** [collector.go:79](/home/mehdi/Project/leela/persop/persob/internal/telegram/collector.go:79), [collector.go:149](/home/mehdi/Project/leela/persop/persob/internal/telegram/collector.go:149), [collector.go:153](/home/mehdi/Project/leela/persop/persob/internal/telegram/collector.go:153).  
**Observed:** Collector registers only live new/edit handlers. It has no initial history fetch, pagination or delete-update handler; an unauthorized session waits until shutdown, with no implemented first-login authorization flow.  
**Expected:** A connected user can authorize, add an accessible source and backfill/recover messages under Telegram limits.  
**Reproduction:** Source inspection found no history request or auth-code/login call; real account test was unavailable.  
**Root cause:** Session storage and update listening are implemented without account onboarding or synchronization state machine.  
**Recommended fix:** Implement consented session provisioning, paged history sync, durable update-gap recovery and delete/edit reconciliation; wire flood-wait handling.  
**Fix applied:** No.  
**Test after fix:** NOT EXECUTED live; only fixture new/edit adapter tests ran.

### P1-05 — Linked discussion comments are not tied to the original channel post

**Affected / reference:** [adapter.go:201](/home/mehdi/Project/leela/persop/persob/internal/telegram/adapter.go:201), [message.go:48](/home/mehdi/Project/leela/persop/persob/internal/domain/message.go:48).  
**Observed:** LinkedPostID is populated from the discussion group’s ReplyToMsgID/ReplyToTopID. Those are group message/thread IDs; the adapter does not preserve the forwarded channel-post identity.  
**Expected:** Comments should reference the original broadcast channel post while retaining their discussion peer/thread IDs.  
**Reproduction:** Existing fixture passes a reply root ID and asserts that value as LinkedPostID; it does not include or assert a forwarded channel post ID.  
**Root cause:** The adapter treats a forum/discussion thread root as the source channel post relation.  
**Recommended fix:** Read the Telegram forwarded-message origin/channel-post metadata and persist it separately from reply/thread IDs.  
**Fix applied:** No.  
**Test after fix:** Fixture test is insufficient; full linked-discussion scenario BLOCKED.

### P1-06 — Failed Redis work is stranded in the pending list

**Affected / reference:** [consumer.go:43](/home/mehdi/Project/leela/persop/persob/internal/queue/consumer.go:43), [consumer.go:78](/home/mehdi/Project/leela/persop/persob/internal/queue/consumer.go:78).  
**Observed:** Handler errors are logged but not acknowledged; subsequent reads request only new entries. Restarted workers do not reclaim pending work. maxRetries is configured but not used.  
**Expected:** Bounded retry/backoff, pending reclamation and a terminal dead-letter/manual-review path.  
**Reproduction:** Audit test observes one call for a transient failure; restart test observes zero calls by the replacement worker.  
**Root cause:** No XAUTOCLAIM/XCLAIM or retry loop/dead-letter policy exists.  
**Recommended fix:** Add pending-entry claiming, retry count/backoff and durable dead-letter visibility.  
**Fix applied:** New consumer groups now start at 0 to retain backlog, but pending recovery is not fixed.  
**Test after fix:** TestConsumerGroupDoesNotSkipExistingBacklog PASS; retry and restart recovery FAIL.

### P1-07 — One Telegram message can store only one offer

**Affected / reference:** [001_initial_schema.sql:85](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/migrations/001_initial_schema.sql:85), [001_initial_schema.sql:105](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/migrations/001_initial_schema.sql:105), [offer_repo.go:62](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/offer_repo.go:62), [processor.go:211](/home/mehdi/Project/leela/persop/persob/internal/worker/processor.go:211).  
**Observed:** All extracted products from a message use the same source_message_id; the unique constraint/upsert overwrites the prior product.  
**Expected:** Every product and its associated price from one message must persist independently.  
**Reproduction:** TestMultiProductMessageRetainsBothOffers extracts two offers; database returns one.  
**Root cause:** Message identity is used as offer identity without a product index/key.  
**Recommended fix:** Add a stable per-message product identity and migrate uniqueness/upsert semantics without dropping existing offers.  
**Fix applied:** No.  
**Test after fix:** FAIL; one offer stored where two are expected.

### P1-08 — Replayed offers create duplicate price history

**Affected / reference:** [offer_repo.go:85](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/offer_repo.go:85), [offer_repo.go:93](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/offer_repo.go:93).  
**Observed:** Create records another observation on every replay, even when amount and currency did not change; it also ignores observation persistence errors.  
**Expected:** Processing retries/edits should be idempotent; only a confirmed price change should create a new historical observation, and failures should be returned.  
**Reproduction:** Replaying the same source message yields two observations.  
**Root cause:** Observation append is unconditional and outside the offer upsert transaction.  
**Recommended fix:** Serialize offer update plus observation insertion and suppress unchanged values; propagate errors.  
**Fix applied:** No.  
**Test after fix:** FAIL; 2 observations where 1 expected.

### P1-09 — Currency units are mixed in comparisons/statistics

**Affected / reference:** [analytics_repo.go:111](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/analytics_repo.go:111), [analytics_repo.go:140](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/analytics_repo.go:140), [engine.go:47](/home/mehdi/Project/leela/persop/persob/internal/analytics/engine.go:47).  
**Observed:** Comparison queries average integer amounts without grouping/converting currency; product statistics silently ignore Rial.  
**Expected:** Normalize all supported currencies to one canonical unit before aggregation and label the result.  
**Reproduction:** Equivalent 100 Toman and 1000 Rial observations produce average 550, not 100.  
**Root cause:** Unit conversion is not an enforced database/domain boundary.  
**Recommended fix:** Canonicalize on ingest or normalize explicitly in all SQL/analytics paths; reject unsupported currency.  
**Fix applied:** Parser unit tests pass, but database analytics are unchanged.  
**Test after fix:** FAIL mixed-currency acceptance.

### P1-10 — Expired offers remain in “active” price statistics

**Affected / reference:** [analytics_repo.go:119](/home/mehdi/Project/leela/persop/persob/internal/storage/postgres/analytics_repo.go:119), [engine.go:35](/home/mehdi/Project/leela/persop/persob/internal/analytics/engine.go:35).  
**Observed:** Queries filter listing_status='active' but do not exclude expiration_date <= now.  
**Expected:** Expired inventory must not distort current market price or best-offer results.  
**Reproduction:** Seed one expired and one current offer; aggregate sample_count is 2.  
**Root cause:** Expiration is stored but omitted from filtering and lifecycle updates.  
**Recommended fix:** Exclude expired rows in active views/statistics and define an expiry transition/job.  
**Fix applied:** No.  
**Test after fix:** FAIL expired-offer acceptance.

### P1-11 — Best offers are ranked after pagination

**Affected / reference:** [offer.go:51](/home/mehdi/Project/leela/persop/persob/internal/api/handlers/offer.go:51), [offer.go:82](/home/mehdi/Project/leela/persop/persob/internal/api/handlers/offer.go:82), [engine.go:128](/home/mehdi/Project/leela/persop/persob/internal/analytics/engine.go:128).  
**Observed:** SQL applies LIMIT/OFFSET before the handler sorts scores, so the best global offer can be absent from a limited page.  
**Expected:** Rank the filtered result set before page selection, with stable sorting.  
**Reproduction:** With limit=1, a newer 150 offer is returned while a better 50 offer is outside the selected SQL page.  
**Root cause:** Scoring happens in memory after a paginated repository query.  
**Recommended fix:** Rank in SQL or fetch a bounded full candidate set before pagination with an explicit scoring strategy.  
**Fix applied:** No.  
**Test after fix:** FAIL TestBestOfferRankingBeforePagination.

### P1-12 — Conversation workflow duplicates and cannot complete the requested intake

**Affected / reference:** [manager.go:59](/home/mehdi/Project/leela/persop/persob/internal/conversation/manager.go:59), [processor.go:314](/home/mehdi/Project/leela/persop/persob/internal/worker/processor.go:314), [conversation.go:24](/home/mehdi/Project/leela/persop/persob/internal/domain/conversation.go:24), [main.go:119](/home/mehdi/Project/leela/persop/persob/cmd/perso/main.go:119).  
**Observed:** Same offer initializes multiple conversations. Worker only asks price/city/Tehran area. It does not route Telegram replies to the manager, apply collected data to the offer, or use a real Telegram sender in its process. Delivery errors are discarded but messages are stored as delivered. Cooldown method is not called.  
**Expected:** One durable consented conversation per seller/offer; one-at-a-time collection of seven fields; replies linked to the current conversation; final offer updated; opt-out/rate limits respected.  
**Reproduction:** TestDuplicateConversationInitialization creates two rows. Static route tracing finds no inbound update call to HandleIncomingSellerMessage.  
**Root cause:** No uniqueness/idempotency key and conversation manager is not connected to real inbound/outbound Telegram lifecycle.  
**Recommended fix:** Add a unique active conversation key, connect inbound message routing/outbound sender, update offers transactionally, and enforce consent/cooldown/quiet-hours limits.  
**Fix applied:** No. Initial consent text discloses the automated identity, but no end-to-end send was proven.  
**Test after fix:** Duplicate-conversation test FAIL; other conversation workflow NOT EXECUTED end to end.

### P1-13 — Extraction fabricates branded/manufacturer values

**Affected / reference:** [extractor.go:53](/home/mehdi/Project/leela/persop/persob/internal/extraction/extractor.go:53), [extractor.go:190](/home/mehdi/Project/leela/persop/persob/internal/extraction/extractor.go:190), [processor.go:262](/home/mehdi/Project/leela/persop/persob/internal/worker/processor.go:262).  
**Observed:** Deterministic extraction sets Branded=true universally and manufacturer equal to detected brand; no expiration extraction exists.  
**Expected:** Unknown seller/product attributes remain unknown until evidence or seller confirmation.  
**Reproduction:** Inspect extractor initialization and process any extracted product; Branded is true regardless of message evidence.  
**Root cause:** Domain booleans/strings are treated as affirmative facts without tri-state provenance.  
**Recommended fix:** Preserve nullable/unknown values, attach evidence, and only persist confirmed values.  
**Fix applied:** No.  
**Test after fix:** No negative test exists; observed directly in source.

### P1-14 — Seller prompt injection can influence consent classification

**Affected / reference:** [gemini.go:141](/home/mehdi/Project/leela/persop/persob/internal/llm/gemini.go:141), [gemini.go:190](/home/mehdi/Project/leela/persop/persob/internal/llm/gemini.go:190), [manager.go:220](/home/mehdi/Project/leela/persop/persob/internal/conversation/manager.go:220).  
**Observed:** Seller reply/history is interpolated into a model prompt as plain text for consent and question generation, without a separate system instruction or strict deterministic consent gate.  
**Expected:** Untrusted seller messages cannot override consent policy; only explicit affirmative consent allows follow-up.  
**Reproduction:** Send ambiguous text containing instructions to return consent=true; provider receives it in the same prompt asking for the consent decision. No live model call was made.  
**Root cause:** Extraction prompt hardening was not applied to conversation prompts.  
**Recommended fix:** Treat ambiguous replies as non-consent/manual review; separate system instructions and structured untrusted fields for question generation.  
**Fix applied:** No.  
**Test after fix:** Extraction injection test PASS, but consent-path injection is untested and remains open.

### P1-15 — Default Compose values are not a production secret configuration

**Affected / reference:** [docker-compose.yml:14](/home/mehdi/Project/leela/persop/persob/docker-compose.yml:14), [docker-compose.yml:28](/home/mehdi/Project/leela/persop/persob/docker-compose.yml:28), [.env.example:15](/home/mehdi/Project/leela/persop/persob/.env.example:15).  
**Observed:** Compose defaults to ENVIRONMENT=production while allowing known placeholder Postgres/Mongo credentials and a default Telegram session key.  
**Expected:** Production startup fails unless deployment secrets and session key are explicitly supplied.  
**Reproduction:** Run Compose without secret overrides; configuration resolves to committed placeholders.  
**Root cause:** Environment templates and production defaults are not separated or validated.  
**Recommended fix:** Require non-placeholder secrets in production and use a production secret store.  
**Fix applied:** Config rejects the Telegram default key when a real app ID is configured; DB defaults remain. Ports are loopback-bound.  
**Test after fix:** Telegram key guard PASS; production DB-secret fail-fast test NOT PRESENT.

### P1-16 — The Go executable entry point is still untracked

**Affected / reference:** [main.go:1](/home/mehdi/Project/leela/persop/persob/cmd/perso/main.go:1), [.gitignore](/home/mehdi/Project/leela/persop/persob/.gitignore).  
**Observed:** The original ignore pattern hid cmd/perso/main.go. The ignore rule is now anchored so the file appears in git status, but cmd/ remains untracked; a fresh checkout/archive of the current commit will not contain the executable source.  
**Expected:** The application entry point and required frontend lockfile are tracked in the implementation branch.  
**Reproduction:** Run git -C persob status --short; it reports ?? cmd/. Build succeeds only from this working directory, where the untracked file exists.  
**Root cause:** A broad ignore pattern plus no staging/commit of the newly created source.  
**Recommended fix:** Review and include cmd/perso/main.go and the other intended new files in the implementation commit.  
**Fix applied:** Ignore rule fixed; source tracking/commit remains pending.  
**Test after fix:** Docker image build PASS from working tree; clean Git archive test is BLOCKED until the file is committed.

### P2-01 — Requested design tokens and tap/scroll targets are not met consistently

**Affected / reference:** [App.tsx:383](/home/mehdi/Project/leela/persop/persof/src/App.tsx:383), [OfferCard.tsx:70](/home/mehdi/Project/leela/persop/persof/src/components/OfferCard.tsx:70), [Header.tsx:162](/home/mehdi/Project/leela/persop/persof/src/components/Header.tsx:162).  
**Observed:** Several colors differ from specified Clinical Mint; measured contrast values are 3.34:1 and 3.83:1; 360px initial cards overlap the bottom-nav region; 165 inspected controls are smaller than 44px in at least one dimension.  
**Expected:** Shared semantic tokens, readable contrast and reliable mobile tap/scroll areas at all listed sizes.  
**Reproduction:** See screenshots and browser-audit.mjs output at the sizes in section 3.  
**Root cause:** Many local color/size utilities and tight fixed-nav/card spacing.  
**Recommended fix:** Consolidate semantic tokens, raise low contrast, and tune 360px spacing/tap areas.  
**Fix applied:** No.  
**Test after fix:** Browser render itself PASS (RTL, zero horizontal overflow, 390px has three cards); visual acceptance remains partial.

### P2-02 — Product matching can accept partial name/model overlaps

**Affected / reference:** [matcher.go:83](/home/mehdi/Project/leela/persop/persob/internal/matching/matcher.go:83), [matcher.go:121](/home/mehdi/Project/leela/persop/persob/internal/matching/matcher.go:121).  
**Observed:** Alias matching accepts substring containment and brand/model matching accepts either-direction substring containment. Variant matching checks raw JSON text for a substring.  
**Expected:** Ambiguous/unknown variants should not silently group offers as the same product.  
**Reproduction:** Add catalog aliases/models with shared substrings or a mismatched storage variant and call MatchSellerProduct.  
**Root cause:** Heuristic matching returns fixed high confidence without ambiguity thresholds or normalized structured specs.  
**Recommended fix:** Token-boundary/structured-attribute comparison with confidence thresholds and manual review for ambiguous matches.  
**Fix applied:** No.  
**Test after fix:** Existing basic matcher tests PASS; ambiguous variant behavior not covered.

### P2-03 — Data retention and privacy controls are absent

**Affected / reference:** [client.go:48](/home/mehdi/Project/leela/persop/persob/internal/storage/mongodb/client.go:48), [message.go:117](/home/mehdi/Project/leela/persop/persob/internal/domain/message.go:117), [manager.go:300](/home/mehdi/Project/leela/persop/persob/internal/conversation/manager.go:300).  
**Observed:** Raw Telegram text, model prompt/response records and conversation histories have no TTL/deletion policy. Deleting a source does not define raw-message retention.  
**Expected:** Documented retention and deletion behavior for Telegram and seller data, including derived LLM records.  
**Reproduction:** Inspect indexes and source deletion paths; no TTL index or cascade cleanup exists.  
**Root cause:** Persistence is implemented without lifecycle/retention policy.  
**Recommended fix:** Define retention periods and implement data deletion/cascade/TTL with auditability.  
**Fix applied:** No.  
**Test after fix:** No retention test exists.

### P2-04 — Frontend checks are type/build checks only

**Affected / reference:** [package.json](/home/mehdi/Project/leela/persop/persof/package.json).  
**Observed:** lint runs TypeScript compiler; no unit test, component test or ESLint script is defined.  
**Expected:** Test coverage for API contract adapters, navigation, mobile layout and source-resolution errors before integration.  
**Reproduction:** Inspect npm scripts and run npm run lint/build; no npm test target exists.  
**Root cause:** The UI prototype has no automated behavior suite.  
**Recommended fix:** Add tests once API integration exists; avoid treating build success as functional acceptance.  
**Fix applied:** Lockfile/dependency compatibility applied.  
**Test after fix:** Typecheck/build PASS; behavioral frontend tests unavailable.

## 16. Fixes Applied

The following changes are in the workspace and remain uncommitted:

- Protected API routes now fail closed by default; caller-supplied X-User-ID is ignored. Local demo identity is static and cannot be enabled in production.
- Telegram source creation re-resolves the address, rejects invalid/mismatched/unavailable/private-inaccessible sources, ignores client entity metadata, sanitizes upstream errors and checks ownership on source reads/status mutation.
- Missing real Telegram credentials no longer enable mock mode; resolver numeric IDs require a verified entity cache.
- Mongo message upsert now preserves original text and updates the current edited text; required index initialization is fatal.
- Fresh migrations no longer insert demo-owner-dependent rows; Compose schema/seed order is fixed. Migration lock and extension schema selection now pass clean/concurrent DB acceptance.
- Redis consumer group starts at 0 to retain existing backlog.
- LLM response validation, evidence checks, safer API-key header, response size limit and retry cancellation were added; config rejects unsupported/missing LLM provider credentials.
- Legacy web dynamic HTML values are escaped; API proxy routing was added.
- Docker image session directory permissions are configured; Docker/API/database ports bind to loopback.
- OpenAPI copies are valid YAML and identical.
- React dependency compatibility was corrected and a lockfile added.
- Group adapter sender attribution now preserves non-user/unknown sender types and does not create personal sender IDs without a Telegram user peer; unit/race tests pass.

These fixes address observed defects but do not close the open P1 integration and data findings.

## 17. Remaining Blockers

1. Implement real authentication and per-user ownership for all protected routes.
2. Connect the source resolver to the authorized Telegram account across the API/collector boundary; implement first-login session provisioning.
3. Add history backfill, deletion handling, gap recovery, flood-wait handling and pending-message reclamation.
4. Give each product in a Telegram message a stable separate offer identity; make observations idempotent.
5. Normalize currencies and exclude expired offers before comparisons/ranking; rank before page selection.
6. Complete conversation routing, deduplication, seven-field collection, offer updates, consent safety and outbound limits.
7. Select one product domain and connect/deploy the React frontend to the backend API.
8. Replace production placeholder secrets and define raw Telegram/seller-data retention.
9. Fix Clinical Mint tokens/contrast and the 360px clipping/tap-target counts.

## 18. Release Readiness Verdict

**NOT READY.** The clean mock stack proves that Compose, databases, migrations, Nginx proxying and one synthetic worker pipeline can start and exchange data. It does not prove a real source can be added: the source-resolution request returns 503. React is not the frontend deployed by Compose and is disconnected from the API. Nine acceptance failures affect offer correctness, price statistics, ranking, conversations and queue recovery. Live Telegram and Gemini remain unverified.

