# Architecture

Django modular monolith with explicit frontend/backend code separation, dependency inversion for
persistence, selective domain isolation, and PostgreSQL-enforced integrity.
Reasons live in the ADRs (index at the end); this file states the rules.

Status markers: **Open** = not decided yet, with the evidence or milestone that will decide it.
Everything not marked Open is approved.

## 1. Modules

| Module | Owns | May import (only via `api.py`) |
| --- | --- | --- |
| `core` | Shared value objects (`Money`), base domain errors, transaction port, configuration that references no other module (e.g. currency) | — |
| `media` | Image assets, upload validation, storage, variants, deletion protection, tombstones | `core` |
| `catalog` | Products (primary image, ordered gallery), categories (flat in V1), brands (description, logo), prices, catalogue rules | `core`, `media` |
| `content` | Homepage sections (configuration, visibility, banners and editable content), featured products/brands and their order, menus and submenus, institutional pages, site identity (name, logo, contacts, general information) | `core`, `catalog`, `media` |
| `storefront` | Public controllers (home, listing, detail) | all domain modules |
| `backoffice` | Owner-facing controllers and forms not provided by the chosen admin tool | all domain modules |

Rules (ADR-0002, ADR-0006):

1. Direction is one-way: `content → catalog → media → core`. `storefront` and `backoffice` sit on top; nothing
   imports them.
2. A module's public surface is `api.py` (use-case factories, query services, DTOs, public errors). Everything
   else in a module is private.
3. Modules reference each other's data **by ID**; no module holds another module's entities.
4. Database foreign keys across modules are allowed only in the same direction, declared by string label
   (`"media.Asset"`), with `related_name="+"`, and listed in the relation allowlist test.
5. No ORM traversal across a module boundary. Catalog gets image URLs by calling `media.api` in one batched call.
6. If Django Admin or Wagtail is chosen, its registration file lives inside the owning module, which may import
   its own models and services. `backoffice` never imports another module's models.
7. Site identity lives in `content`, not `core`, because it references a media asset (the logo) and `core` may not
   depend on `media`. Media association rules are owned by the module that holds the reference.

**Open — Services and Events placement** (D20, ADR-0017 before M11). Both are V1 capabilities (`docs/product.md`
§2). Proposal: sibling modules `services` and `events`, each importing only `core` and `media`, at the same level as
`catalog`; `content` may reference them by ID. No shared base entity and no inheritance with Product. Until
ADR-0017 is accepted, no package is created and the module list above, ADR-0002 and `AGENTS.md` rule 1 are unchanged;
the ADR's PR updates all three.

## 2. Responsibilities

| Component | Responsible for | Django implementation | Must not |
| --- | --- | --- | --- |
| Presentation | Rendering DTOs | Templates, CSS, JS in `frontend/` | Query data, decide prices or visibility |
| Controller | HTTP, permission checks, form parsing, building commands, mapping errors to responses | Views, `forms.Form` | Write via ORM; hold business rules |
| Use case | One workflow: check references, call domain, persist, own the transaction | Plain class, dependencies via constructor | Import `django` or models |
| Domain | Entities, value objects, invariants, domain errors | Plain Python | Import Django; do I/O |
| Repository contract | Persistence operations a use case needs, in domain terms | `typing.Protocol` in the module's `application.py` | Expose Django types |
| Infrastructure | ORM models, repository implementations, storage, image processing | `models.py`, `repositories.py`, `storage.py` | Make business decisions |
| Query service | Read models for pages and lists | ORM (`values`, `annotate`, `prefetch_related`) returning DTOs | Return model instances or querysets |
| Composition root | Wiring use cases to implementations | `services.py` factory functions, no DI framework | Hold state or logic |

Input validation is split: forms check shape; the domain checks meaning; the database enforces what must always
hold. Authorization is checked in controllers; use cases receive already-authorised commands.

## 3. Write path and read path

- **Write** (rules exist): controller → use case → domain → repository contract → Django repository → PostgreSQL.
- **Read**: controller → query service → DTO → template. Aggregates are never loaded for lists.

- **Visibility:** products are public as soon as they exist (no status field). Homepage sections and menu entries
  have a visibility flag; hiding never deletes their content or configuration.

Category, Brand, site identity and institutional pages have no repository contract until a rule beyond what
database constraints enforce appears; they are edited through simple forms backed by database constraints and
ModelForm validation (ADR-0005). Categories and brands referenced by products cannot be deleted (P2, P3 approved):
`Product.category` and `Product.brand` are `PROTECT` foreign keys, and the deletion surfaces as a form error. Category
and brand slugs are stable (D22, approved part): no write path changes a slug once it is assigned; the M2 spec decides
whether the database also enforces it.

Services and Events are expected to carry rules beyond constraints (prices, date ordering, slugs), so their writes go
through use cases like Product's. Each spec confirms this; ADR-0017 extends `AGENTS.md` rule 5 and ADR-0008 to them.

## 4. Repository contracts (ADR-0003, ADR-0016)

- Contracts never contain Django types.
- The consumer owns the contract: it is declared next to the use cases that need it. A module that needs another
  module's data declares a small port, implemented by an adapter that calls the other module's `api.py`.
- One contract per aggregate written through use cases, with methods named after what use cases need. No generic
  `Repository[T]`, no repository per model.
- Planned V1 contracts: `ProductRepository`, `TaxonomyLookup` (category/brand existence), `AssetRepository`,
  `HomepageRepository`, `MenuRepository`, and one each for Service and Event if their specs confirm use cases.
- Query services are concrete classes, not protocols, until a second implementation exists.
- Every contract has a shared contract test suite run against both the fake and the Django implementation.

**Contract style for rule-bearing aggregates:**
- **Product** (ADR-0016): `ProductRepository` exchanges `Product` entities. The entity enforces its invariants on
  every construction, including rehydration; a domain factory normalises input; the Django repository maps
  rows ↔ entities. A spec that tightens a Product invariant assesses existing rows first (ADR-0016, Consequences).
  Real rows exist from the G-DATA gate (section 13), the first private production deployment.
- **Other aggregates** (Asset, Homepage, Menu, Service, Event): **Open**, chosen in the spec that introduces each, between primitive/DTO
  contracts (invariants in pure functions/value objects) and entity contracts. Hard gates for either style: no Django
  imports in domain/application; application tests run without Django settings; contract suite passes for fake and
  Django implementations; failure-injection test leaves no rows; database constraints present.

## 5. Transactions and errors (ADR-0004)

- The use case wraps its work in the `core` transaction port (`transaction.atomic()` in Django; no-op in fakes).
  `ATOMIC_REQUESTS` is off.
- Repositories never open outer transactions or commit.
- An expected constraint violation is caught inside a **savepoint** (nested `atomic()`) in the repository, matched
  by constraint name, and translated to a domain error. Other `IntegrityError`s propagate. Reason: in PostgreSQL a
  failed statement aborts the transaction until rolled back.
- Slugs: the unique constraint decides (no pre-check). On `DuplicateSlug` the use case retries with the next
  candidate (`base`, `base-2`, `base-3`), at most 3 attempts, then raises `SlugUnavailable`.
- Files are not transactional: uploads store the file first, then commit the row. Orphan files are tolerated.
- Post-commit work uses `transaction.on_commit` in adapters, never in the domain.

| Failure | Raised as | Controller response |
| --- | --- | --- |
| Invariant broken | Domain error (e.g. `InvalidProduct`) | Form error |
| Unknown category, brand or asset | `ReferenceNotFound` | Form error on that field |
| Slug unavailable after retries | `SlugUnavailable` | Form error |
| Asset still referenced | `ProtectedError` → `AssetInUse` | Message: asset in use |
| Database unavailable / unexpected | Not caught | 500, logged |

## 6. Integrity (ADR-0005)

`Model.save()`, `bulk_create()`, `queryset.update()` and raw SQL skip model validation, so invariants that must
always hold are database constraints, declared in `Meta.constraints` and tested by writing invalid rows directly.

The list below covers the rules as currently proposed. Business values (e.g. price rules, P4) become constraints
only once approved in the milestone spec (`docs/product.md` §7).

- `CHECK (price > 0)`
- `CHECK (promo_price IS NULL OR (promo_price > 0 AND promo_price < price))`
- `UNIQUE (slug)` on product, category and brand; `UNIQUE (Lower(name))` on brand and category (flat categories)
- `Product.category` and `Product.brand`: `PROTECT` (P2, P3)
- Product images: `UNIQUE (product, asset)`, `UNIQUE (product, position)` deferrable, `CHECK (position >= 0)`
- Featured selections: unique item, `UNIQUE (position)` deferrable
- `NOT NULL` on required fields
- Cross-module FKs: `PROTECT` for every reference to a media asset (product gallery, brand logo, homepage content,
  site logo, service and event images); featured selection behaviour per D4 (proposal: `CASCADE`)

Rules that cannot be constraints (asset must be an image, featured-count limit, menu depth) live in use cases.

## 7. Concurrency

| Case | Handling |
| --- | --- |
| Homepage or menu saved by two people | Repository `get` inside the use case locks the row (`select_for_update`); second writer validates fresh state |
| Same product edited twice | Last write wins in V1 (D13); optimistic locking deferred |
| Asset deleted while a product references it | FK `PROTECT`; PostgreSQL makes one transaction fail cleanly |
| Slug race | Unique constraint + savepoint retry |
| Reordering images or featured items | Position uniqueness checked at commit (deferrable) |

## 8. Media (ADR-0009)

- One shared asset library reused across contexts: product primary image and gallery, brand logos, homepage and
  site content. Each module that references an asset owns that association and its rules; media owns the file,
  its validation, variants and deletion protection.
- Files are immutable: generated names, never overwritten; variants are new files.
- Upload validation: size limit, decoded by Pillow to confirm a real image, decompression-bomb limit kept, files
  renamed to generated names, uploads never executed. Limits per D14.
- Output contract: WebP variants at a fixed set of widths; templates use `srcset`, `sizes`, explicit width/height
  and `loading="lazy"` below the fold; variant URLs only through `media.api`.
- **Open — variant timing** (eager at upload vs on demand at first request). M3 implements eager generation as the
  measured baseline; decided by ADR before M5 from staff upload time vs first-request latency.
  Eager: a failed variant fails the upload without leaving an `Asset` row. On demand: the original is served until
  the variant exists.
- Delivery split:

  | Concern | Milestone |
  | --- | --- |
  | Asset model, upload validation, storage, variants, tombstones, `PROTECT` deletion protection (backend), batched `media.api` lookups | M3 |
  | Product–image association and its constraints; images attached when a product is created (first image primary) | M3 |
  | Staff upload of a **new** image while creating a product (J1) | M5 |
  | Central library: browse and filter assets, **select an existing asset** for reuse, delete with the "in use" message | M7b |
  | Add, remove, reorder and set the primary image on existing products | M7b |
  | Brand logo (selected from the library or uploaded) | M7c |

  M5 offers upload only; selecting an existing asset arrives with the library in M7b, so there is one chooser, not two.
- Deleting an asset removes its row and records a tombstone in the same transaction; files stay on disk.
  Physical removal happens only in the backup job (see `docs/engineering.md`, Backups). Until that step exists,
  no file is ever deleted.

## 9. Frontend/backend separation (ADR-0007)

- `frontend/` holds templates, CSS, JS and static images; `backend/` holds all Python. One deployment.
- Templates receive DTOs (`ProductCard`, `ProductDetail`, `HomepageView`, `MenuTree`); display decisions such as
  `has_promo` and `display_price` are made in the DTO.
- Progressive JavaScript enhances server-rendered HTML; no private JSON endpoints in V1.
- A future React frontend adds API controllers that call the same use cases and query services.

## 10. Administration (ADR-0008)

Every write to Product, Asset, Homepage or Menu goes through its use case, whatever the tool.

**Open — administration technology:** Django Admin or Wagtail, the V1 candidates. A fully custom backoffice is a
future capability (`docs/product.md` §5) unless explicitly approved for V1. Decided before M5 by a timeboxed
spike per candidate implementing W1 (create/edit product with promo price, primary image and ordered gallery) and W4
(homepage featured products/brands with ordering), measuring: bypass paths, effort, owner usability, dependency
footprint, fit with Media ownership (no second image model). The spike also assesses on paper, without implementing,
the fit for institutional pages, services and events.

Known bypass paths to close in any option: inline formsets and `form.save()` writing rows directly; Django Admin's
"delete selected" action (calls `queryset.delete()`, skips `delete_model`).

**Server-side authorization (from M5).** Every administrative entry point checks permission on the server, on every
request, whatever the interface shows:

- every view and every HTTP method, including direct `POST`s to add, change and delete URLs;
- selectors that reveal data: autocomplete endpoints, raw-ID lookups, related-object pop-ups, asset choosers;
- bulk actions, history views, "view on site" links, exports and user, group and permission administration;
- capability gating (from M11): with a capability off, its public and administrative entry points refuse the
  request even when called directly;
- combined profiles: a user holding both profiles gets exactly the union of their permissions, tested as its own
  actor.

A route inventory test lists every URL pattern (public from M4, administrative from M5) and fails when one is not
classified as public, capability-gated or permission-checked and covered by a test. The permission matrix covers
anonymous, staff without permission, Platform Administrator, Setup Administrator and a user with both profiles.

## 11. Folder structure

```text
backend/
  config/                 settings (base, dev, test, prod), urls, wsgi, env.py
  core/                   domain.py, transactions.py, models.py, api.py
  media/                  domain.py, application.py, models.py, repositories.py, storage.py, services.py, api.py, tests/
  catalog/                same files + queries.py
  content/                same files + queries.py
  storefront/             views.py, urls.py
  backoffice/             views.py, forms.py, urls.py
frontend/
  templates/              storefront/, backoffice/, components/
  static/                 css/, js/
tests/
  fakes/                  in-memory repositories
  e2e/                    Playwright journeys
docs/                     product, architecture, engineering, design-system (from UX0), adr/, specs/, runbooks/
```

This is the target layout. Each module and file is created by the milestone that first needs it, together with
its import-linter contracts. Files, not layer directories; a module grows a sub-package only when a file passes
roughly 400 lines.
`models.py` stays at the app root (Django convention) and is treated as infrastructure.

## 12. Tests

| Level | Runs against | Django settings |
| --- | --- | --- |
| Domain | Pure Python | No |
| Application | Fakes from `tests/fakes/` | No |
| Contract suite | Fake and Django implementation | Django half only |
| Repository / query integration | PostgreSQL (never SQLite) | Yes |
| HTTP and permissions | Django test client + PostgreSQL; route inventory test (section 10) | Yes |
| End-to-end | Playwright, four critical journeys J1–J4 (section 13) | Yes |

## 13. Delivery plan (V1)

Approved by the owner on 2026-11-19: milestones M0–M13, the UX0 track and the G-UX and G-DATA gates. Decisions
still open stay open until approved (`docs/product.md` §7, `docs/engineering.md`).

- **Implementation gate:** a milestone's code starts only after its spec shows `Approval: approved (owner)`, as in
  spec 002. The next gate is the M2 spec. A milestone may have several specs (M7 has three).
- **Exit checks** below are the minimum; each spec adds detail. The continuous quality requirements in
  `docs/engineering.md` §9 apply to every milestone.
- **Dependencies:** "Requires" is technical: the milestone cannot start or finish without it. The preferred order
  is a scheduling choice and may change at no technical cost.
- Before M1: the contract-style PoC (section 4; done, ADR-0016). Before M5: the administration spike (section 10).

### 13.1 Dependencies

```text
Required (══>)
  UX0 ══> G-UX ══> M4
  M1 ══> M2 ══> M3 ══> M4 ══> M6
               M3 ══> M5 ══> M6                     J1 needs M4 and M5
                      M5 ══> M7a, M7b, M7c          M7b and M7c also need M3
  M3, M4, M5 ══> M8         M7c, M8 ══> M9          M4, M5 ══> M10
  M3, M4, M5 + D17, D20, D21 ══> M11                M3, M4, M5 + D19, D21 + switch ══> M12
  G-DATA ══> first real data and first production deployment
  M2–M12 + G-DATA ══> M13

Preferred (-->)
  M6 --> M7 --> M8 --> M9 --> M10 --> M11 --> M12 --> M13
  G-DATA --> alongside M10
  UX0 Services/Events discovery --> D17 and D19 decided before the M9 spec
```

Services and Events come last because they are the least specified; they need none of M7–M10 and may move earlier
once D17/D19 are decided. The capability switch is built by whichever of M11/M12 comes first. If M9/M10 come first,
M11 adds the switch checks to the menu, homepage and sitemap.

### 13.2 UX0 — product discovery, creative exploration and design

Runs in parallel with M2/M3 and needs no backend code.

| Stage | Content |
| --- | --- |
| UX0.1 Discovery | Business goals and customer tasks (find a product, compare prices and promotions, contact by WhatsApp, find a service, see upcoming events); inventory of existing content and representative volumes (D29); current website URLs (D23); reference sites for inspiration, not copying. Early Services and Events discovery: real services, how they are priced and requested; real events, frequency and what customers need to know. Feeds D17, D19, D21 |
| UX0.2 Creative exploration | Two or three **alternatives that differ in interaction and engagement, not only in visual style**: how customers discover products (category-first, brand-first, editorial homepage), how gallery and detail behave on touch and keyboard, where and when the WhatsApp contact is offered, how the homepage invites return visits, and first concepts of how services and events draw attention. Each alternative applies a visual language to the same tasks at mobile width. The owner chooses one, or a combination |
| UX0.3 Catalogue design foundation | Design system v0 in `docs/design-system.md`: tokens (colour pairs with text contrast ≥ 4.5:1 and UI contrast ≥ 3:1, type scale, spacing, breakpoints); components (header, mobile navigation, footer, product card with and without image, normal and promotional price, gallery, WhatsApp action, breadcrumbs, pagination, empty and error states, focus styles); interaction patterns; responsive prototypes of listing and detail at 360, 768 and 1280 px |
| UX0.4 Later-capability concepts | Low-fidelity concepts only, to inform decisions: homepage sections (D8), menu and submenus (P5), service and event lists and details, identity footer. Final designs belong to each milestone's spec |
| UX0.5 Usability check | Three to five people complete the UX0.2/UX0.3 tasks on a phone; findings and resulting changes recorded |

Rules: UX0 content goes into a public repository (E4), so it uses only material the owner allows to be published.
No paid tool without owner approval. **Open:** U1, the prototype tool and location (proposal: static HTML/CSS in a
folder excluded from the Docker image, or a free design tool); U2, who takes part in the usability check (proposal:
real customers or contacts of the business).

**G-UX gate (required before M4 starts):**
- Owner approval recorded for the chosen alternative, design system v0 and the listing and detail prototypes at
  three widths.
- The prototypes pass contrast, keyboard and visible-focus checks (WCAG 2.2 AA, P7).
- Usability findings are fixed or explicitly deferred.
- D18, P8, D22 (remaining part), D28 and D29 are decided.

Final designs for the homepage, menu, services and events are not required at G-UX.

### 13.3 Milestones

| # | Scope | Requires | Exit check |
| --- | --- | --- | --- |
| M0 | Repository foundation | — | Done (spec 001) |
| M1 | Catalog domain, `CreateProduct`, contracts, fakes, contract suite (fake half) | M0 | Done (spec 002) |
| M2 | Catalog persistence: models, migrations, constraints, Django `ProductRepository` and `TaxonomyLookup`, Django half of the contract suite. Minimal Category (name, stable slug) and Brand (name, description, stable slug), `PROTECT` from Product. Destructive-migration CI check. `prod` Docker target, `/healthz` and the CI `image` job | M1; approved M2 spec, including the category and brand slug format (D22) | Every obligation in spec 002 "Consequences for M2" has a named test (listed below this table). Contract suite green on PostgreSQL. Deleting a referenced category or brand fails by direct ORM write. `image` job green: prod image runs against PostgreSQL, `/healthz` 200, non-root user |
| M3 | Media foundation and product image association (split in section 8) | M2; D14; E11 | Rejected: non-images, oversize files, decompression bombs, mismatched extensions. A failed variant leaves no `Asset` row. An asset referenced by a product image, or by a fixture foreign key from another module, cannot be deleted. Tombstone and row removal in one transaction; no file deleted. Position and uniqueness violations rejected by direct writes. Allowlist lists `ProductImage.asset`. Variant generation time recorded for the variant-timing ADR |
| M4 | Storefront listing and detail built from design system v0: query services, DTOs, templates; P8; D18; SEO and URL baseline (D22); one canonical base-URL setting; WhiteNoise static files in the prod image; public route inventory test | M2, M3, G-UX | HTTP tests; query budgets for listing and detail; templates receive no model instances; route inventory green; `docs/engineering.md` §9 checks pass; server p95 and mobile Lighthouse recorded on representative data (D29). Phase 1 closed: the prod image serves static files and answers `/healthz` |
| M5 | Administration technology (spike ADR) and variant timing (ADR). Two profiles (D15). Staff login hardening. Product creation with upload of a new image (section 8). Minimal category and brand creation (name; brand description) as forms backed by constraints. Server-side authorization (section 10). Phase 2 staging | M3; both ADRs; D13; D15; E9, E10, E12 (staging part), each with its cost approved separately | Permission matrix (five actors) and administrative route inventory green, including direct `POST`s, selectors and bulk actions; inline writes and "delete selected" closed; form errors mapped; a merged PR reaches staging without manual steps; a broken release fails smoke tests and is rolled back by the runbook |
| M6 | First end-to-end journey | M4, M5 | **J1** green in CI: log in → create a category → upload an image → create a product associated with that image → listing and detail show that image's variant. The owner completes J1 on staging without help; findings recorded |
| M7a | Product lifecycle: edit (name, description, category, brand), `ChangeProductPrice`, `DeleteProduct` (removes gallery associations, never assets); D12 remaining part | M5; D12 | Edit use cases exercise rehydration (ADR-0016); P4, N1 and N2 hold on the edit path; last write wins (D13); permission matrix extended |
| M7b | Gallery management and central media library (section 8) | M3, M5 | Removing the primary promotes the next image; setting a primary keeps the others' relative order; reordering passes deferrable position checks at commit; selecting an existing asset reuses it without copying; an asset in use cannot be deleted and the message says so; an unused asset is tombstoned; selector endpoints are in the permission matrix |
| M7c | Taxonomy: category CRUD (flat, ordering per D30); brand CRUD with description and logo | M3, M5; D30 | Deleting a category or brand with products is refused, by HTTP and by direct ORM; duplicate names are form errors; slugs do not change on rename; the logo is `PROTECT` |
| M8 | Business identity and contacts: site identity (name, logo, contacts, general information) with the Setup/Platform split (D15); WhatsApp number, general and per-product WhatsApp actions; social links; Open Graph from identity. Usage measurement only if the approved D25 outcome includes it | M3, M4, M5; D16; D25 disposed of by the owner, including a decision not to implement | Implementation matches the approved D25 outcome: with "not implemented", no measurement exists. WhatsApp actions absent without a valid number; no empty social icons; the prefilled message carries the product name and absolute canonical URL, correctly encoded; a Platform Administrator editing protected fields is refused by the server. **J4** (mobile, 360 px): listing → product → WhatsApp link with the correct prefilled text |
| M9 | Homepage and featured items: predefined sections, mandatory and optional; visibility toggles without data loss; banners and content; ordered featured products and brands; `HomepageRepository` with row lock | M7c, M8; D8; D4 | Hiding a mandatory section is refused, even by a direct `POST`; hiding keeps the data; deleting a featured item behaves per D4; featured positions unique (deferrable); homepage query budget set. **J2**: feature a product → it appears on the homepage |
| M10 | Navigation and institutional pages: menu and submenus (labels, destinations, order, visibility); a fixed set of destination types, extended additively; `MenuRepository`; institutional and legal pages. A contact form or newsletter only if the approved D26 or D27 outcome includes it | M4, M5; P5; P6; D24; D26 and D27 disposed of by the owner, including decisions not to implement | Implementation matches the approved D26 and D27 outcomes: with "not implemented", no form or subscription exists. Depth and destination rules enforced in the use case; hidden entries keep their data; concurrent saves behave per D13 |
| M11 | Services (module per ADR-0017) with use cases; public list and, per D17, detail. **Capability switch**: two booleans in the Setup configuration, Setup-only, checked on the server. Gating of every public and administrative entry point, menu, homepage and sitemap | M3, M4, M5; D17 (incl. D17-a); D20; D21 | With the capability off: public URLs return 404, absent from menu, homepage and sitemap, administrative screens refused to the Platform Administrator even by direct URL, data kept. The Platform Administrator cannot toggle the switch. Domain and application tests run without Django. Database constraints match the domain rules. If G-DATA has passed, the backup and restore scope covers services before they receive real data (`docs/engineering.md` §11). **J3**: switching off removes public access |
| M12 | Events (module per ADR-0017) with use cases; upcoming-events listing and, per D19, detail. No registrations, participants, payments or recurrence | M3, M4, M5; D19; D21; the switch | End before start rejected by the domain and by a database `CHECK`; "upcoming" computed in Europe/Lisbon (`USE_TZ=True`) with daylight-saving boundary tests; past events per D19; the same switch tests as M11; restore scope extended as in M11 |
| M13 | Public V1 release `v1.0.0`: full WCAG 2.2 AA audit, mobile Lighthouse on real content, SEO and URL checklist, security headers; redirects from the current website and DNS switch (D23); `docs/perf-baseline.md` with targets (E15); customer usability check on production content; runbooks complete | M2–M12; G-DATA | Every Phase 3b criterion in `docs/engineering.md` §13. On the public domain: private-indexing restrictions removed, the public `robots.txt` restored, implemented public routes crawlable and `sitemap.xml` available (`docs/engineering.md` §5); every V1 requirement in `docs/product.md` maps to a test or a recorded manual check; the human creates the `v1.0.0` tag |

**M2 obligations carried from spec 002** (each needs a named test):
- **Columns and checks**
  - `price` and `promo_price` are `NUMERIC(10, 2)`.
  - The two P4 `CHECK`s and the 99 999 999,99 maximum.
  - Direct writes that bypass the use case reject `NaN`, `±Infinity`, zero, negative values, values above the
    maximum, a `NaN` promotional price, and a promotional price equal to or above the normal price.
- **Precision**
  - Whether Django's `DecimalField` rounds before the value reaches PostgreSQL is established.
  - "Rejected, never rounded" is guaranteed by the entity and use case, because PostgreSQL rounds on direct writes.
- **Name and slug**
  - `name` is `varchar(200)` with a non-empty, trimmed `CHECK` aligned with Python's `strip()`, tested with a tab and a
    non-breaking space.
  - `slug` is `varchar(160)`, `UNIQUE`, with a format `CHECK`.
- **Transactions**
  - Each `add` runs in its own savepoint. `DuplicateSlug` is matched by constraint name. Other `IntegrityError`s
    propagate. No query runs after an uncaught database error.
  - Retry with `-2`, `-3`, then `SlugUnavailable`. An `add` after `DuplicateSlug` in the same transaction succeeds.
- **Concurrent removal**
  - A category or brand removed concurrently gives `ReferenceNotFound`, not `DuplicateSlug`, and stores nothing.
  - The test covers when the deferred foreign-key check fires (Django creates `DEFERRABLE INITIALLY DEFERRED` keys);
    the mechanism is the M2 spec's choice.
- **Rehydration and rollback**
  - Loading a row validates it (ADR-0016).
  - Failure injection leaves no rows.

**G-DATA gate** (before any real business data or real staff account reaches a hosted environment, and before the
first, private, production deployment; preferred alongside M10): defined in `docs/engineering.md` §11. From G-DATA,
real Product rows exist, so any tightened Product invariant follows the ADR-0016 procedure.

## 14. Critical workflows

Kept current by every PR that changes a listed entry point or use case. Cells are filled when implemented.

| Workflow | Entry point | Use case / query | Modules | Tests |
| --- | --- | --- | --- | --- |
| Create product | — (M5) | `CreateProduct` (`catalog/application.py`; M1: domain and application only, no persistence or media yet) | backoffice, catalog, media | `backend/catalog/tests/test_create_product.py`, `test_domain.py`, `test_contracts_fake.py` |
| Edit product | — (M7a) | edit use case | backoffice, catalog | — |
| Change product price | — (M7a) | `ChangeProductPrice` | backoffice, catalog | — |
| Delete product | — (M7a) | delete use case | backoffice, catalog | — |
| Manage product gallery (add, remove, reorder, set primary) | — (M7b) | gallery use cases | backoffice, catalog, media | — |
| Manage brands (description, logo) | — (minimal M5; full M7c) | form + constraints | backoffice, catalog, media | — |
| Manage categories | — (minimal M5; full M7c) | form + constraints | backoffice, catalog | — |
| Upload media | — (M5) | upload use case | backoffice, media | — |
| Browse and reuse media (library) | — (M7b) | media query service | backoffice, media | — |
| Delete media | — (M7b) | delete use case | backoffice, media | — |
| Product listing | — (M4) | `ProductListingQuery` | storefront, catalog, media | — |
| Product detail | — (M4) | `ProductDetailQuery` | storefront, catalog, media | — |
| Edit site identity, contacts, social links | — (M8) | form + constraints | backoffice, content, media | — |
| Set featured products/brands | — (M9) | `SetFeaturedProducts`, `SetFeaturedBrands` | backoffice, content, catalog | — |
| Configure homepage sections (visibility, content) | — (M9) | homepage use case | backoffice, content, media | — |
| Edit menu (labels, destinations, order, visibility) | — (M10) | menu use case | backoffice, content | — |
| Institutional pages | — (M10) | per spec P6 | storefront, content | — |
| Switch a capability on or off | — (M11) | per spec D21 | backoffice, core | — |
| Manage services | — (M11) | service use cases (D17) | backoffice, services, media | — |
| Services listing and detail | — (M11) | services query service | storefront, services, media | — |
| Manage events | — (M12) | event use cases (D19) | backoffice, events, media | — |
| Events listing and detail | — (M12) | events query service | storefront, events, media | — |

## 15. Decision index

| ADR | Decision |
| --- | --- |
| 0001 | Django/PostgreSQL modular monolith |
| 0002 | Module boundaries and dependency direction |
| 0003 | Repository contracts without framework types; query services for reads |
| 0004 | Transactions owned by use cases; savepoints for expected violations |
| 0005 | Validation layers and database constraints |
| 0006 | Cross-module foreign keys |
| 0007 | Frontend/backend separation through DTOs |
| 0008 | Administration writes go through use cases |
| 0009 | Immutable media files and deferred physical deletion |
| 0010 | Toolchain and reproducible environments |
| 0011 | Single immutable image and release verification |
| 0012 | Backward-compatible migrations |
| 0013 | Backups and tested recovery objectives |
| 0014 | Specification-driven process with independent agent review |
| 0015 | Agents share the developer's Git credentials (E4b b) |
| 0016 | Product repository contracts exchange domain entities |

ADRs to write when decided: administration technology (spike), variant timing (M3
measurement), slug policy (D12), repository visibility and plan (E4), hosting (E9), Services and Events placement
(ADR-0017, D20; amends ADR-0002 and ADR-0008), release identity before the first production deployment (revisits
ADR-0015, at G-DATA).
