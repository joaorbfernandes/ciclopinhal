# 0002 — Module boundaries and dependency direction

Status: Accepted

**Context.** Catalogue, media and content rules must not leak into each other or form cycles.

**Decision.** Modules `core`, `media`, `catalog`, `content`, with direction `content → catalog → media → core`;
`storefront` and `backoffice` on top. Cross-module access only through `api.py`; references by ID. Enforced by
import-linter in CI.

**Consequences.** Some extra batched queries (e.g. image URLs from `media.api`); no module can modify another's
data directly.

Details: `docs/architecture.md` §1.
