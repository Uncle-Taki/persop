# Implementation checkpoint

> Step 2 identity work is now implemented on codex/perso-healthcare-rbac: see [implementation and verification](docs/STEP_2_IDENTITY.md) and the [current workflow](docs/WORKFLOW.md). Password accounts replace browser API-token login. Buyer shared-source access remains blocked until step 3. Historical checkpoint descriptions below do not describe these new account capabilities.

> Current healthcare/RBAC work is tracked in [docs/WORKFLOW.md](docs/WORKFLOW.md), with the [contract map](docs/CONTRACT_MAP.md) and [verified step 1 baseline](docs/STEP_1_BASELINE.md). The electronics/single-operator scope and older pending-test statements below describe the historical checkpoint. Exact-baseline parent integration now passed eight browser tests and the container rehearsal; standalone backend fixture and runtime-image scan failures remain documented. Healthcare, roles, and mock HTTP LLM are planned and are not implemented by this documentation change.

Branch: `codex/perso-improvements-wip` in the parent and both submodules.
This reviewable checkpoint is published on the branch above in all three repositories. It has not been deployed. The GitHub connection created new commit IDs for the same submodule file trees; the parent pins those published commits.

## Implemented scope

- **Backend:** migration ledger, per-item offers and immutable message revisions, retryable Redis processing, Mongo dispatch reconciliation, normalized price comparison, stricter product matching, authenticated operator API, and one session-owning Telegram gateway.
- **Conversations:** operator approval, application-owned consent, persisted intake, deduplication, durable outbox, delivery failure recording, and optional quiet hours. Outreach and external LLM processing remain disabled by default.
- **Frontend:** server-backed offers, interests, sources, conversations and settings; explicit loading/error/empty states; Persian/English navigation; local fonts; responsive mint styling. The healthcare fixture is available only through explicit demo mode.
- **Deployment:** parent Compose manifests, separate demo/test environments, random credential generation, API contract checks, and integration CI for the pinned submodule combination.

The live catalog is electronics. The deployment supports one operator workspace and one Telegram account; independent customer accounts are outside this checkpoint.

## Validation status

- Frontend typecheck and production build passed after formatting.
- Generated API types and the embedded/canonical backend API contract match.
- Frontend dependency audit reported no advisories.
- Whitespace checks passed for both submodules.
- Earlier backend unit and disposable database acceptance runs exercised the implementation. Subsequent backend changes and the patched Go toolchain still require a completed final run.
- The most recent full-stack browser run passed seven of eight tests. The remaining failure concerned the accessible name of navigation with a count badge; a fix is committed, but its full-stack rerun is pending.
- The race build exceeded local compiler resources. Race checks remain configured in CI; no passing final race result is claimed.
- Docker is unavailable in this workspace, so container build/start and Compose runtime verification remain pending.

## Before deployment

Run the full pinned-stack CI, including unit/race/vet/build, database acceptance, generated-contract checks, browser tests and deployment manifest validation. Repeat vulnerability scanning with the pinned Go toolchain. Rehearse backup and restore on staging.

Real Telegram authentication, history recovery, delivery and external LLM behavior require operator-owned credentials and staging verification. No real seller messages have been sent. Review configuration and explicitly enable outreach only when these checks are complete.

See [backend operations](persob/docs/operations.md) for operational procedures and [integration CI](.github/workflows/integration.yml) for the repeatable verification commands.

See [REMAINING_WORK.md](REMAINING_WORK.md) for the prioritized follow-up jobs, completion evidence and later product scope.
