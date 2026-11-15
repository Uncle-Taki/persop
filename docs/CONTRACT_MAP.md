# Healthcare prototype → shared contract map

Step 1 design artifact; no endpoints, schemas, migrations, or UI behavior are implemented by this document. Read with [WORKFLOW.md](WORKFLOW.md) and [STEP_1_BASELINE.md](STEP_1_BASELINE.md).

## Source of truth and transport rules

Baseline prototype: `persof/src/types/perso.ts`, `src/DemoApp.tsx`, `src/pages/*.tsx`, Header/BottomNav/OfferCard. Current live transport: `persof/src/api/client.ts` and backend `internal/api/router.go`; canonical OpenAPI is `persob/docs/openapi.yaml`. Proposed routes below do not exist unless marked existing.

Use snake_case transport fields and generated types; adapt localized UI view models explicitly. Persist canonical timestamps/values, localize at render time. Preserve `{success,data,meta}` envelopes for normal application endpoints; return accurate errors and scoped pagination. Missing facts are nullable/unknown. The mock provider uses its own documented OpenAI-style envelope.

The current offers handler returns scored wrappers only for best_offer/default/with_scores while the client always expects `ScoredOffer[]`. Normalize that response contract for all UI sorts in step 4/6 and add a regression check. `GET /watch-sources` already delegates to the normalized source handler but its older documented body differs: align/deprecate it without a permission bypass. Internal Telegram access hashes/session secrets must not be in buyer DTOs.

## Screen and control map

All routes in the next table are relative to `/api/v1`. Existing routes need new role/ownership checks before multiple buyers use them.

| Prototype screen/control | Current behavior | Intended synchronized behavior / endpoint | Roles; step |
| --- | --- | --- | --- |
| `best_offers`: search, category, city, Rx visibility, sort, pagination, offers/catalog switch | Filters in-memory fixture arrays; fake sync timer | Existing GET `/offers` and `/products`; extend query with search/category/city/spec filters, `show_rx`, consistent scored response, total before pagination; map match_desc→best_offer, price_asc→lowest_price, price_desc→highest_price, newest→newest | All roles, assigned sources for buyer; 3/4/6 |
| Offers: refresh/sync button, badges | Simulated sync and synthetic stats | Refresh re-fetches server resources, shows real last_synced/status; it does not claim to trigger Telegram synchronization. No manual sync endpoint in this iteration | All roles; 6 |
| Offer card: interest toggle, details, compare, start chat | Local array updates and fake thread creation | Existing POST/DELETE `/interests`, GET `/offers/{id}`, product routes; proposed POST `/inquiries` creates private request, never directly sends | Own interests/inquiries; 4/6/7 |
| `product_details`: catalog facts, seller/source/raw excerpt, interest, comparison | All fixture values | Existing GET `/products/{id}`, `/offers`, `/sources/{id}`; joined healthcare detail DTO and permission-checked provenance | All authorized roles; 4/6 |
| `price_comparison`: product/city selection, min/avg/max/distribution, start inquiry | Fixture calculations | Existing `/products/{id}/statistics` and `/offers`; extend compatible product/unit/pack filters and user scope; no unauthorized aggregate denominator | All authorized roles; 3/4/6 |
| `interests`: list, remove, target-price edit, compare/details | Local state | Existing GET/POST/DELETE `/interests`; proposed PATCH `/interests/{id}` for owned constraints; update persisted data then invalidate resources | Owner; 2/4/6 |
| `interests`: notification toggle | Local boolean, no delivery | Deferred; hide/disable with explanatory state until an in-app delivery path exists | No active toggle; 6 |
| `add_product`: product identity + price/qty/city form | Creates synthetic catalog product and interest together | Split roles: buyer chooses existing product and POST `/interests`; admin uses proposed catalog POST/PATCH `/products` then optionally creates own interest. No fabricated market prices/counts | Buyer selection; admin catalog edit; 4/6 |
| `telegram_sources`: search/type filters, detail, add, pause/resume/delete | Fixture mutations | Existing GET `/sources`, GET `/{id}`, PUT `/{id}/status`, DELETE `/{id}`; role-limited mutations and assigned-source read model | Admin mutations; buyer read assigned only; 3/6 |
| `add_telegram_source`: address, auto-detect, type/public/access/discussion controls | Client simulates detection and allows capability assertions | Existing POST `/sources/resolve` then POST `/sources`; server/gateway determines peer/access/capabilities; editable admin labels/city/keywords via proposed PATCH `/sources/{id}`. Display access/type facts read-only; expected type may validate mismatch. No client assertion of membership | Admin; 3/6 |
| `source_details`: capabilities, sync, metrics, monitoring, raw offers | Fixture/source-local counters | Existing source detail/capabilities/status plus authorized source-filtered offers; defer unsupported member/precision metrics. Source outbound Telegram link shown only where access allows | Admin mutation; authorized reader; 3/6 |
| `conversations`: search, state filters, thread opening | Fixture list/unread reset | Existing GET `/conversations` augmented with buyer inquiry projection; planned GET `/inquiries` for buyer requests. Use canonical states; defer unread badge | Buyer own; admins workspace; 3/7 |
| `conversation_details`: transcript, templates, free-text send, product/compare | Local seller replies generated by timer | Existing detail/approve/pause/close; buyer sees own request progress and authorized messages. Replace free-send with structured inquiry/request notes, not direct seller send. Templates are local draft helpers. Only approved application intake reaches gateway | Admin approval; owner pause/close; 7 |
| `settings`: language, city/default sort, profile/password | Language local; most profile controls absent | Proposed GET/PATCH `/me`, GET/PATCH `/me/preferences`, POST `/me/password`; local language fallback before login; enforce saved preferences after login | All own; 2/6 |
| Settings: match threshold, auto Tehran, deduplicate, Rx, buy/sell modes | Some local-only toggles | Threshold as own minimum_match_score preference used by query; Rx as display preference only; dedupe and extraction are application invariants (read-only explanation), sell deferred | All own preferences; 2/4/6 |
| Settings: reset sample data | Restores fixture arrays in browser | Demo reset via explicit demo-only admin command/reseed, absent from production UI/API; resetting demo must never target production volumes | Demo admin only; 5/8 |
| Header/back/bottom navigation, language, filter drawer, toast | In-memory screen history | URL-addressable navigation and accessible controls; loading/error/result from actual mutations; five buyer tabs; admin controls do not crowd mobile tabs | Role-aware presentation; 6 |
| New login/logout, account management, source assignments | Not in prototype | Session/auth/user routes below; account create/deactivate/reset, last-super-admin protection, source assignment management | As workflow role matrix; 2/3 |

## Endpoint deltas and responsibility

| Domain | Existing | Proposed addition/change | Owner |
| --- | --- | --- | --- |
| Identity | GET `/session`, fixed bearer operator | POST `/auth/login`, POST `/auth/logout`, GET `/session` expanded user/permissions; session cookie + CSRF policy; no public signup | Backend identity + frontend auth; 2 |
| Personal account | No profile/preferences API | GET/PATCH `/me`, GET/PATCH `/me/preferences`, POST `/me/password` | 2 |
| Users | Internal users table/repo only | GET/POST `/users`, GET/PATCH `/users/{id}`, POST `/users/{id}/reset-password`; role/state restrictions; no credential/secret in read DTOs | 2 |
| Source grants | Single operator source ownership | GET/PUT `/sources/{id}/assignments`; replace grants atomically; invalidate access immediately; buyer list only assigned | 3 |
| Catalog | GET products/details/statistics only | Admin POST/PATCH products, aliases/localized fields and domain; retire/archive flag rather than deleting historical products | 4 |
| Interests | GET/POST/DELETE | PATCH owned constraints; buyer_id from session; GET matches filtered by active grants/constraints | 3/4 |
| Offers/statistics | Existing offers/details/statistics and analytics | Add source_id, healthcare spec/unit/search filters, uniform ScoredOffer wrapper, nullable unknowns, permission-filtered denominators | 3/4/6 |
| Inquiries | Conversations currently operator-owned | POST/GET `/inquiries`, GET `/inquiries/{id}`, POST `/inquiries/{id}/pause` or `/close`; separate from shared seller conversation. Admin approval stays `/conversations/{id}/approve` | 3/7 |
| Provider/configuration | Gemini env/in-process mock; CLI settings | Configurable server-side OpenAI-compatible adapter/internal mock service; no browser provider secret. Operational configuration stays environment/CLI in this iteration; no generic URL edit endpoint | 5 |

Proposed DTOs: Session/User/Profile/Preferences, UserCreate/UserUpdate/PasswordReset; SourceAssignment; HealthcareProduct/Attributes/Aliases; HealthcareOffer/ScoredOffer/PriceStatistics; Interest/InterestConstraints; BuyerInquiry/InquiryProgress; Conversation/AdminTranscript; ProviderMetadata without credentials. Required/nullable fields, validation, paging and errors enter OpenAPI alongside the implementing slice; step 1 does not falsely advertise planned endpoints as working.

## Ownership and migration decisions

- One installation/workspace, one shared catalog/source ingestion and one Telegram session. Add explicit workspace identity where required by shared entities; buyer access comes from source grants, not an arbitrary offers.owner_id rewrite.
- Raw source revisions remain singular; offers get a normalized source FK. Buyer-specific matches link user+interest+offer. Interests/preferences/inquiries are user-owned; shared seller sessions and outbox remain workspace-controlled.
- Authorization precedes sorting/pagination/counts/aggregation. The same predicate applies to raw text, product statistics, source relations, inquiry details and background matching. Buyers cannot select effective identity using request bodies, headers or role strings.
- One active seller intake for the same workspace/seller/listing-purpose prevents duplicate outreach; buyer inquiries link separately. Admin sees the seller-session transcript. Buyer receives only own request messages/progress and authorized listing facts; shared transcripts must not disclose other buyers' identity or preferences. Stop sending when no active eligible linked request remains.
- Source revocation/deactivation immediately removes buyer reads and future matches/inquiries; do not let a cached match reopen access. Admins retain operational source visibility; read-only/shared data does not create permission to send.
- Legacy migration: map `user`→`buyer`, `admin`→`admin`; only the explicitly configured installation operator may bootstrap `super_admin`. Unknown/ambiguous roles require explicit migration resolution and never implicit promotion. Protect the last active super admin; retire operator-token authorization before enabling multiple accounts.
- Existing migration files remain immutable. Later migrations add accounts/sessions/preferences, grants/shared-source links, healthcare fields and inquiry ownership in ordered steps. Preserve electronic catalog and historical offers; filter the healthcare default instead of destroying old data.

## Prototype enum reconciliation

- Healthcare categories: otc_medicine, pharmacy_products, medical_devices, medical_consumables, health_monitoring, hygiene_products, supplements.
- Source peer type: prototype group → canonical basic_group; supergroup/forum/broadcast_channel remain distinct. Access/ingestion/capability facts come from the gateway.
- Offer status: in_stock/immediate_dispatch/limited_stock/corporate_quota are seller availability claims, not lifecycle active/sold/expired/unverified. rx_verification is a restriction/requirement, not stock or verified eligibility.
- Conversation status: awaiting_reply → WAITING_FOR_REPLY; archived → a user presentation/archive flag if implemented, not an invented lifecycle transition. price_quoted is a known-price fact. confirmed must not imply a purchase; show collected/completed intake instead. Add AWAITING_APPROVAL/AWAITING_CONSENT/DECLINED/OPTED_OUT/PAUSED to the UI.
- Exact final roles: super_admin/admin/buyer. Language fa/en. No fixture ID, date, stock state or seller-verification badge becomes a default production fact.

## Complete prototype field classification

P = persisted source/catalog/user fact (includes relations); C = calculated or joined from persisted facts; V = presentation-only; D = deliberately deferred. Categories describe target behavior, not a claim of existing backend support. Each property of all exported prototype interfaces is classified below. Optional fields stay optional when unknown.

### LinkedDiscussionRelationship

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `hasLinkedDiscussion` | C | Derived from resolved linked peer/capabilities; never user-asserted. |
| `discussionUsername` | P | Linked-source metadata; actual title with optional admin translations, no invented translation. |
| `discussionTitleFa` | P | Linked-source metadata; actual title with optional admin translations, no invented translation. |
| `discussionTitleEn` | P | Linked-source metadata; actual title with optional admin translations, no invented translation. |
| `memberCount` | D | Omit until a timestamped real Telegram measurement is available. |
| `autoSyncReplies` | P | Admin-controlled discussion monitoring setting; all linked peers inherit explicit source authorization. |

### TelegramSource

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `id` | P | Workspace source UUID; ownership is workspace-scoped with separate buyer assignments. |
| `usernameOrUrl` | P | Source address/username; resolve through gateway before creating. |
| `titleFa` | P | Actual Telegram title plus optional translations; original title is fallback. |
| `titleEn` | P | Actual Telegram title plus optional translations; original title is fallback. |
| `peerType` | P | source_type; translate prototype group to canonical basic_group. |
| `isPublic` | C | Derived from access_type public/private. |
| `accessStatus` | C | Gateway resolution and account authorization; unverified/pending is not proof of access. |
| `monitoringStatus` | P | ingestion_status; keep unauthorized distinct from paused/error. |
| `memberCount` | D | No fabricated audience or precision metric; require a measured population/denominator before exposing. |
| `extractedOffersCount` | C | Count actual source offers within viewer authorization. |
| `matchPrecisionPercent` | D | No fabricated audience or precision metric; require a measured population/denominator before exposing. |
| `lastSyncedFa` | V | Format last_synced_at; null means not synchronized. |
| `lastSyncedEn` | V | Format last_synced_at; null means not synchronized. |
| `cityFocusFa` | P | Admin-authored source metadata/translations, not a city preference that silently filters other buyers. |
| `cityFocusEn` | P | Admin-authored source metadata/translations, not a city preference that silently filters other buyers. |
| `descriptionFa` | P | Admin-authored source metadata/translations, not a city preference that silently filters other buyers. |
| `descriptionEn` | P | Admin-authored source metadata/translations, not a city preference that silently filters other buyers. |
| `keywords` | P | Admin-authored source metadata/translations, not a city preference that silently filters other buyers. |
| `linkedDiscussion` | P | Linked peer relation and explicit monitoring setting; see nested field map. |
| `resolutionOrigin` | C | Server environment/resolver provenance; live gateway versus synthetic demo, never client-selected. |

### Product

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `id` | P | Catalog UUID. |
| `nameFa` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `nameEn` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `brandFa` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `brandEn` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `modelOrSpecFa` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `modelOrSpecEn` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `category` | P | Healthcare category enum below; add catalog_domain=healthcare. |
| `unitFa` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `unitEn` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `ircCode` | P | Optional catalog identifier with provenance; no verification claim. |
| `isPrescriptionOnly` | P | Catalog flag; UI visibility preference grants no license or authorization. |
| `regulatoryNoteFa` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `regulatoryNoteEn` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `descriptionFa` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `descriptionEn` | P | Localized catalog metadata; normalized strength/form/pack/unit attributes stored independently for matching. |
| `avgMarketPriceToman` | C | Authorized eligible offers with compatible specs and price basis; zero samples yields null prices/count 0. |
| `minMarketPriceToman` | C | Authorized eligible offers with compatible specs and price basis; zero samples yields null prices/count 0. |
| `maxMarketPriceToman` | C | Authorized eligible offers with compatible specs and price basis; zero samples yields null prices/count 0. |
| `activeOfferCount` | C | Authorized eligible offers with compatible specs and price basis; zero samples yields null prices/count 0. |
| `iconType` | V | Deterministic category/icon mapping, no image or icon stored per offer. |

### Offer

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `id` | P | Offer/catalog/workspace-source UUIDs; source_item_key + source_revision preserve replay identity. |
| `productId` | P | Offer/catalog/workspace-source UUIDs; source_item_key + source_revision preserve replay identity. |
| `productNameFa` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `productNameEn` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `brandFa` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `brandEn` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `modelSpecFa` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `modelSpecEn` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `category` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `priceToman` | C | Derived from persisted nullable price_amount/price_currency; normalize Rial by integer /10; unknown is null. |
| `unitFa` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `unitEn` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `minOrderQty` | P | Nullable minimum order quantity, distinct from offered stock quantity. |
| `cityFa` | P | Canonical seller city/area codes or raw location plus localized labels; preserve unknown. |
| `cityEn` | P | Canonical seller city/area codes or raw location plus localized labels; preserve unknown. |
| `tehranDistrictFa` | P | Canonical seller city/area codes or raw location plus localized labels; preserve unknown. |
| `tehranDistrictEn` | P | Canonical seller city/area codes or raw location plus localized labels; preserve unknown. |
| `status` | P | Nullable availability/dispatch claim, distinct from lifecycle listing_status and any access restriction. |
| `sellerNameFa` | P | Source-provided seller metadata; no invented translated names. |
| `sellerNameEn` | P | Source-provided seller metadata; no invented translated names. |
| `sellerTelegramHandle` | P | Source-provided seller metadata; no invented translated names. |
| `sellerVerified` | D | No verification badge until an explicit evidence-backed verification process exists. |
| `sellerLicenseCode` | P | Optional seller claim with provenance; do not label verified. |
| `matchScore` | C | Authorized buyer-specific match score and explainable offer ranking are separate DTO fields, not one ambiguous score. |
| `postedAtFa` | V | Format actual source_published_at timestamp, never fixed fixture dates. |
| `postedAtEn` | V | Format actual source_published_at timestamp, never fixed fixture dates. |
| `postedMinutesAgo` | V | Format actual source_published_at timestamp, never fixed fixture dates. |
| `expiryDateSampleFa` | V | Replace sample field names with formatted nullable product_expires_on and source date precision; separate listing expiry/warranty. |
| `expiryDateSampleEn` | V | Replace sample field names with formatted nullable product_expires_on and source date precision; separate listing expiry/warranty. |
| `paymentTermsFa` | P | Optional terms claimed by seller; original text plus explicitly recorded translation only. |
| `paymentTermsEn` | P | Optional terms claimed by seller; original text plus explicitly recorded translation only. |
| `sourceId` | P | Offer/catalog/workspace-source UUIDs; source_item_key + source_revision preserve replay identity. |
| `sourceTitleFa` | C | Authorized source metadata join. |
| `sourceTitleEn` | C | Authorized source metadata join. |
| `rawTelegramExcerptFa` | V | Show the same preserved original text unless a separately attributed translation exists; never fabricate bilingual originals. |
| `rawTelegramExcerptEn` | V | Show the same preserved original text unless a separately attributed translation exists; never fabricate bilingual originals. |
| `isPrescriptionOnly` | C | Join canonical catalog metadata; unmatched listings retain unknown product rather than false match. |
| `isSampleData` | C | Server-supplied demo provenance; replace literal-true prototype type with explicit environment/sample metadata. |

### WatchlistInterest

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `id` | P | Interest UUID/product UUID; add authenticated user_id server-side. |
| `productId` | P | Interest UUID/product UUID; add authenticated user_id server-side. |
| `productNameFa` | C | Canonical product join. |
| `productNameEn` | C | Canonical product join. |
| `brandModelFa` | C | Canonical product join. |
| `brandModelEn` | C | Canonical product join. |
| `category` | C | Canonical product join. |
| `targetMaxPriceToman` | P | Nullable user-owned constraints; canonical city/area + labels, validated positive quantities, no fabricated defaults. |
| `currentBestPriceToman` | C | Only actual eligible, authorized matches; no fallback to sample price or count 1. |
| `preferredCityFa` | P | Nullable user-owned constraints; canonical city/area + labels, validated positive quantities, no fabricated defaults. |
| `preferredCityEn` | P | Nullable user-owned constraints; canonical city/area + labels, validated positive quantities, no fabricated defaults. |
| `requiredQty` | P | Nullable user-owned constraints; canonical city/area + labels, validated positive quantities, no fabricated defaults. |
| `notifyOnDrop` | D | Disable/omit until a persisted in-app notification pipeline is delivered; external notifications out of scope. |
| `matchedOffersCount` | C | Only actual eligible, authorized matches; no fallback to sample price or count 1. |
| `createdAtFa` | V | Format server created_at. |
| `createdAtEn` | V | Format server created_at. |

### ChatMessage

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `id` | P | Transcript/outbox message UUID; retain source inbound identity for dedupe. |
| `sender` | P | Canonical assistant/seller/system (+buyer only for private requests); no fake buyer label for automated assistant. |
| `textFa` | P | Persist one original text/language plus optional attributed translation, not mandatory duplicated bilingual text. |
| `textEn` | P | Persist one original text/language plus optional attributed translation, not mandatory duplicated bilingual text. |
| `timestampFa` | V | Format created_at/sent_at; queued is not sent; retain status/last_error/delivery semantics. |
| `timestampEn` | V | Format created_at/sent_at; queued is not sent; retain status/last_error/delivery semantics. |

### ConversationThread

| Prototype property | Class | Target / handling |
| --- | --- | --- |
| `id` | P | Buyer inquiry/request identity links an offer to a buyer; distinct from shared seller-session identity. |
| `offerId` | P | Buyer inquiry/request identity links an offer to a buyer; distinct from shared seller-session identity. |
| `productId` | P | Buyer inquiry/request identity links an offer to a buyer; distinct from shared seller-session identity. |
| `productNameFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `productNameEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `offeredPriceToman` | C | Nullable normalized amount from offer/attributed intake; not a purchase commitment. |
| `unitFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `unitEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sellerNameFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sellerNameEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sellerHandle` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sellerCityFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sellerCityEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `tehranDistrictFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `tehranDistrictEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sourceTitleFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `sourceTitleEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `status` | C | Display actual approval/consent/intake/outbox state; never equate completed intake or known price with a confirmed purchase. |
| `unreadCount` | D | Hide until per-user read cursor is persisted; a single global unread count is incorrect for multiple buyers. |
| `updatedAtFa` | V | Format actual updated_at. |
| `updatedAtEn` | V | Format actual updated_at. |
| `rawTelegramPostFa` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `rawTelegramPostEn` | C | Authorized product/offer/source/original-message join; expose only buyer-permitted facts and text. |
| `messages` | P | Authorized transcript/private-request projection; no cross-buyer message leakage; see ChatMessage map. |

Coverage: 131 properties across 7 exported interfaces; all explicitly classified. The screen/control map covers all 11 ScreenId values plus shared navigation and new account administration.
