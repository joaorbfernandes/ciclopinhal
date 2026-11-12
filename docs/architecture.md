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
| `catalog` | Products (primary image, ordered gallery), categories (hierarchical when needed), brands (logo), prices, catalogue rules | `core`, `media` |
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
ModelForm validation (ADR-0005). Deletions that must respect existing associations are enforced by `PROTECT`
foreign keys; exact behaviour per product decisions P2 and P3.

## 4. Repository contracts (ADR-0003)

- Contracts never contain Django types.
- The consumer owns the contract: it is declared next to the use cases that need it. A module that needs another
  module's data declares a small port, implemented by an adapter that calls the other module's `api.py`.
- One contract per aggregate written through use cases, with methods named after what use cases need. No generic
  `Repository[T]`, no repository per model.
- Planned V1 contracts: `ProductRepository`, `TaxonomyLookup` (category/brand existence), `AssetRepository`,
  `HomepageRepository`, `MenuRepository`.
- Query services are concrete classes, not protocols, until a second implementation exists.
- Every contract has a shared contract test suite run against both the fake and the Django implementation.

**Open — contract style for rule-bearing aggregates** (decided by the PoC before M1):
- Variant D: primitive/DTO contracts, invariants in pure functions/value objects.
- Variant E: domain-entity contracts, repository maps record ↔ entity.
- Hard gates, both variants: no Django imports in domain/application; application tests run without Django
  settings; contract suite passes for fake and Django implementations; failure-injection test leaves no rows;
  database constraints present.
- Scored, only among variants passing all gates: rule locality (weighted first), mapping/DTO code, change cost
  (add a required unique `sku`), test clarity, effort, reviewability. Choose E if it wins rule locality and is
  not worse on more than two other criteria; otherwise D.

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
- `UNIQUE (slug)` on product; `UNIQUE (Lower(name))` on brand and category (scoped to parent if categories nest)
- Product images: `UNIQUE (product, asset)`, `UNIQUE (product, position)` deferrable, `CHECK (position >= 0)`
- Featured selections: unique item, `UNIQUE (position)` deferrable
- `NOT NULL` on required fields
- Cross-module FKs: `PROTECT` for every reference to a media asset (product gallery, brand logo, homepage content,
  site logo); featured selection behaviour per D4 (proposal: `CASCADE`)

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
footprint, fit with Media ownership (no second image model).

Known bypass paths to close in any option: inline formsets and `form.save()` writing rows directly; Django Admin's
"delete selected" action (calls `queryset.delete()`, skips `delete_model`).

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
docs/                     product, architecture, engineering, adr/, specs/, runbooks/
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
| HTTP and permissions | Django test client + PostgreSQL | Yes |
| End-to-end | Playwright, 2–4 critical journeys | Yes |

## 13. Delivery plan

Before M1: the contract-style PoC (section 4). Before M5: the administration spike (section 10).

| # | Scope | Exit check |
| --- | --- | --- |
| M0 | Repository foundation (spec 001) | See spec 001 |
| M1 | Catalog domain + `CreateProduct`, contracts, fakes, contract suite (fake half) | Domain/application tests pass without Django settings |
| M2 | Catalog persistence, constraints, Django repository with savepoint retry, minimal categories/brands | Contract suite on PostgreSQL; invalid ORM writes rejected; slug conflict commits; failure injection leaves no rows |
| M3 | Media: upload, validation, storage, one variant width set, `PROTECT` delete with tombstone, `media.api` lookups | Invalid files rejected; referenced asset not deletable; allowlist lists `ProductImage.asset` |
| M4 | Storefront listing and detail: query services, DTOs, templates | HTTP tests; query budgets; templates receive no model instances |
| M5 | Staff product creation through the chosen admin option, with permissions | Permission matrix tests; form errors; bypass review closed |
| M6 | E2E: log in → upload image → create product → visible on listing and detail | Playwright green in CI |

Second slice: homepage sections (configuration, visibility, banners and content, featured products and brands)
and menus. Remaining V1 workflows — product edit and delete, brand and category management, institutional pages,
site identity — are specified as later slices.

## 14. Critical workflows

Kept current by every PR that changes a listed entry point or use case. Cells are filled when implemented.

| Workflow | Entry point | Use case / query | Modules | Tests |
| --- | --- | --- | --- | --- |
| Create product | — | `CreateProduct` | backoffice, catalog, media | — |
| Change product price | — | `ChangeProductPrice` | backoffice, catalog | — |
| Delete product | — | delete use case | backoffice, catalog | — |
| Manage brands (incl. logo) | — | form + constraints | backoffice, catalog, media | — |
| Manage categories | — | form + constraints | backoffice, catalog | — |
| Upload media | — | upload use case | backoffice, media | — |
| Delete media | — | delete use case | backoffice, media | — |
| Product listing | — | `ProductListingQuery` | storefront, catalog, media | — |
| Product detail | — | `ProductDetailQuery` | storefront, catalog, media | — |
| Set featured products/brands | — | `SetFeaturedProducts`, `SetFeaturedBrands` | backoffice, content, catalog | — |
| Configure homepage sections (visibility, content) | — | homepage use case | backoffice, content, media | — |
| Edit menu (labels, destinations, order, visibility) | — | menu use case | backoffice, content | — |
| Edit site identity | — | form + constraints | backoffice, content, media | — |
| Institutional pages | — | per spec P6 | storefront, content | — |

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

ADRs to write when decided: contract style (PoC), administration technology (spike), variant timing (M3
measurement), slug policy (D12), repository visibility and plan (E4), release identity model (E4b), hosting (E9).
