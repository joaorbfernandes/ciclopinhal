# 002 — M1 Catalog domain

Status: done
Approval: approved (owner, 2026-11-15; recorded in PR #5 before any code)
Milestone: M1
ADRs: 0002, 0003, 0004, 0005, 0012, 0016

## Lifecycle

`Status` uses the template values only and tracks implementation; `Approval` records the owner's decision separately.
This milestone is delivered in a single PR (owner decision, 2026-11-15) that contains the spec, the product
documentation, the code and the tests.

| Stage | `Status` | `Approval` | Product decisions (P4, D12 format, N1, N2) |
| --- | --- | --- | --- |
| Spec drafted and reviewed | `draft` | `pending (owner)` | proposals |
| Owner approves the four decisions as written (2026-11-15) | `draft` | `approved (owner, 2026-11-15)` | approved; `docs/product.md` updated in the same first change, before any code |
| Implementation starts | `in progress` | unchanged | approved |
| PR merged, every acceptance criterion met | `done` | unchanged | approved |

No M1 code was written while `Approval` was `pending`: the approval and `docs/product.md` changes precede the code
in the PR's history. Approval was given explicitly by the owner in the session that started implementation, for the
four decisions exactly as written below.

## Goal

A Django-independent `Product` entity whose invariants hold on every construction path, and a `CreateProduct` use
case that uses the entity-based `ProductRepository` contract of ADR-0016, with in-memory fakes and the fake half of a
shared contract suite. Everything runs under `make test-fast` with no Django settings and no database.

ADR-0016 is not reopened by this spec.

## Decisions

### Resolved

| ID | Decision | Recorded in |
| --- | --- | --- |
| D7 | A product may exist with zero images; it is valid and publicly eligible. Images are optional at creation and afterwards. Removing all images neither invalidates nor deletes the product. When images exist, the first is primary; changing the primary image moves it to position 0 and keeps the relative order of the others (already approved). | `docs/product.md` §2 |

D7 consequences for this spec: the `Product` entity has no image field, `CreateProduct` has no image input, and there
is no asset-lookup port in M1. The product gallery is M3 (see "Milestone boundaries"). The public presentation of a
product without images is **D18**, an open presentation decision for M4, not a domain invariant.

### Decisions approved by the owner (2026-11-15)

Approved exactly as written. `docs/product.md` §2 ("Regras do produto") and §7 ("Resolvidas") carry the same text.

| ID | Approved rule |
| --- | --- |
| **P4** | Normal price is required and > 0. Promotional price is optional; when present it is > 0 and strictly less than the normal price. Each price has at most two decimal places, judged by numeric value (`10.500` equals `10.50` and is accepted; `10.505` is rejected). Over-precise values are rejected, never rounded. Maximum value of each price: 99 999 999,99. |
| **D12** (format and generation only) | The slug is generated automatically from the name at creation. Only `a–z`, digits and hyphens; accents are removed (`Ação` → `acao`); any other run of characters becomes one hyphen; no leading, trailing or repeated hyphens. Maximum 160 characters including the collision suffix. On collision the suffixes `-2` and `-3` are tried (three attempts in total); then creation fails. A name from which no valid slug can be derived (for example only symbols) is rejected. Manual slug editing and slug behaviour when the name changes stay open in D12 and are outside M1. |
| **N1** | The name is required, trimmed, non-empty, at most 200 characters (Unicode code points). |
| **N2** | The description is optional, trimmed, and may be an empty string. |

### Open, not blocking M1

- **D18** (M4): public presentation of a product without images on listing and detail.
- **D12** (remaining, before the product-edit slice): manual slug editing; slug when the name changes.

## Scope

In scope:

- `core` package: `DomainError`, `ReferenceNotFound`, the `Atomic` transaction port, `api.py`.
- `catalog` package: `domain.py` (`Product`, factory, slug policy, `InvalidProduct`) and `application.py`
  (`ProductRepository`, `TaxonomyLookup`, `CreateProductCommand`, `CreateProduct`, `DuplicateSlug`, `SlugUnavailable`).
- Fakes, builders, domain and application tests, the fake half of the contract suite.
- import-linter contracts for the new modules.

Out of scope:

- Django models, migrations, database constraints, Django repositories, `INSTALLED_APPS` or app configuration (M2).
- Category and brand CRUD; `catalog/api.py` and `services.py` (no consumer yet).
- Images, the gallery, asset ports and any `media` integration (M3).
- Storefront, query services, DTOs, templates (M4); backoffice, admin, permissions (M5); HTTP of any kind.
- Product editing and deletion, manual slug editing, SKU, `Money`, `durable=True`, services, events.

## Milestone boundaries

| Milestone | Owns |
| --- | --- |
| M1 | This spec: pure `Product` domain, `CreateProduct`, contracts, fakes, tests |
| M2 | Django persistence and database constraints, Django repositories with savepoint retry, Django half of the contract suite, failure injection, minimal categories and brands |
| M3 | Media and the product gallery |
| M4 | Public catalogue (query services, DTOs, templates), D18 |

M3 introduces image associations and gallery behaviour. It will change what it needs to change (the entity or a
separate association, the repository mapping, the contract suite); M1 makes no promise that M3 touches none of the M1
code. Whether and how `CreateProduct` accepts images, and the image-management workflow and its integration with
`Product`, are decided in M3's spec. `CreateProduct` does not need to accept images. Products created without images
in M1 and M2 remain valid.

## Product invariants

All rules are checked in `Product.__post_init__`, so they hold on every construction path: the factory, direct
construction, `dataclasses.replace`, the fake repository's storage and M2 rehydration. The factory only normalises
input before construction; it adds no rule the constructor lacks. Shared private check helpers avoid duplication.
`InvalidProduct(field, code)` reports the first violation, checking fields in declaration order; codes are stable
identifiers, not user-facing text.

| Field | Rule enforced by the constructor | Codes |
| --- | --- | --- |
| `id` | `None`, or an `int` (not `bool`) > 0 | `invalid` |
| `name` | `str`; equal to its `strip()`; non-empty; at most 200 code points; `slug_from_name(name)` is non-empty (the same pure helper `Product.new` uses) | `invalid_type`, `not_normalized`, `required`, `too_long`, `slug_not_derivable` |
| `slug` | matches `^[a-z0-9]+(-[a-z0-9]+)*$`; at most 160 characters | `invalid`, `too_long` |
| `description` | `str`; equal to its `strip()`; may be empty | `invalid_type`, `not_normalized` |
| `category_id` | required; an `int` (not `bool`) > 0 | `required`, `invalid` |
| `brand_id` | `None`, or an `int` (not `bool`) > 0 | `invalid` |
| `price` | a `Decimal` (`float`, `int`, `str` rejected); finite; > 0; at most two decimal places by value; at most 99 999 999,99 | `invalid_type`, `not_finite`, `not_positive`, `too_precise`, `too_large` |
| `promo_price` | `None`, or the same rules as `price`, and strictly less than `price` | same codes plus `not_below_price` |

`NewType` annotations are not runtime checks, so the id rules above are enforced at runtime.

The name rule requires only that **some** valid slug can be derived from the current name. It does not require the
stored `slug` to equal `slug_from_name(name)`: a valid name with any valid slug is accepted, so a later rename or a
historical row does not fail on that ground. A name such as `"!!!"` is rejected even when the slug is valid.

### Price representation

- **Precision is validated by numeric value**, not by the stored exponent: a price is valid if its numeric value can
  be written with at most two decimal places and it passes the other rules. `Decimal("10.5")`, `Decimal("10.50")`
  and `Decimal("10.500")` are all valid; `Decimal("10.505")` is `too_precise`.
- **The factory (`Product.new`) canonicalises** every accepted price to exponent −2 (`10` → `10.00`,
  `10.500` → `10.50`, `1E+2` → `100.00`). This is lossless: it is applied only when the numeric value is unchanged.
  A value that would change numerically is left untouched so that the constructor rejects it. **Nothing is ever
  rounded in a value-changing way.**
- **Direct construction does not canonicalise.** `Product(price=Decimal("10.5"), …)` is accepted and keeps its
  exponent. Consequently the exponent of a price is guaranteed only for entities built by the factory; code and tests
  that compare prices compare by value (`==`), never by string or exponent. Decimal is used throughout; floats are
  never accepted.
- **Independent of the ambient Decimal context.** Validation and canonicalisation give the same result whatever the
  caller's context: precision, rounding mode and enabled traps (including `Inexact`, `Rounded`, `InvalidOperation`).
  The implementation must not modify the caller's context, must never round a value that needs a numeric change in
  order to accept it, and must turn every Decimal signal it can raise into a defined `InvalidProduct` code
  (`not_finite`, `too_precise` or `too_large`); no `decimal` exception escapes. The algorithm is the implementer's
  choice.

### Factory (`Product.new`)

1. Check that `name` and `description` are `str`; trim both.
2. Check the name (`required`, `too_long`) before deriving the slug.
3. Derive the slug with `slug_from_name`; if empty, raise `InvalidProduct("name", "slug_not_derivable")` (the
   constructor applies the same check with the same helper).
4. Canonicalise prices as above.
5. Construct with `id=None`.

`with_slug(slug)` returns a copy through `dataclasses.replace`, so the constructor runs again.

### Slug policy (approved D12)

`slug_from_name`: NFKD normalisation; drop combining marks; lowercase; replace each run of characters outside
`[a-z0-9]` with one `-`; strip `-` at both ends; truncate to 160 characters and strip a trailing `-`.
`slug_candidates(base, 3)` yields `base`, then for `k` in 2 and 3, `base` truncated so the result fits in 160
characters, trailing `-` stripped, plus `-k`. Every candidate satisfies the slug rule. Known limitation, documented
in the tests: letters without an ASCII decomposition (`ß`, `ø`) act as separators.

## Application design

```python
# backend/core/domain.py
class DomainError(Exception): ...


class ReferenceNotFound(DomainError):
    reference: str
    id: int


# backend/core/transactions.py
class Atomic(Protocol):
    def __call__(self) -> AbstractContextManager[object]: ...


# Django's transaction.atomic satisfies this structurally; core.api never imports Django.


# backend/catalog/domain.py
@dataclass(frozen=True, slots=True, kw_only=True)
class Product:
    id: ProductId | None
    name: str
    slug: str
    description: str
    category_id: CategoryId
    brand_id: BrandId | None
    price: Decimal
    promo_price: Decimal | None


# backend/catalog/application.py
class DuplicateSlug(DomainError): ...  # contract outcome of add(); not a public error


class SlugUnavailable(DomainError): ...


class ProductRepository(Protocol):
    def add(self, product: Product) -> ProductId: ...
    # requires product.id is None; never commits; stores nothing when it raises:
    #   DuplicateSlug                        the slug is taken
    #   ReferenceNotFound("category"|"brand") the referenced category or brand does not exist at persistence time
    def get(self, product_id: ProductId) -> Product | None: ...  # rehydrates through the constructor


class TaxonomyLookup(Protocol):
    def category_exists(self, category_id: CategoryId) -> bool: ...
    def brand_exists(self, brand_id: BrandId) -> bool: ...


class CreateProduct:
    def __init__(self, *, products: ProductRepository, taxonomy: TaxonomyLookup, atomic: Atomic) -> None: ...
    def execute(self, command: CreateProductCommand) -> ProductId: ...
```

`CreateProductCommand` carries `name`, `description`, `category_id`, `brand_id`, `price`, `promo_price`. Ids are
repository-assigned positive integers. `get()` is kept because the shared suite needs it to prove the row ↔ entity
round trip that ADR-0016 relies on; its first production callers are the edit and price use cases of later slices.
`CreateProduct` does not depend on `media`.

### CreateProduct workflow

1. `Product.new(...)` raises `InvalidProduct` before any I/O; no transaction is opened.
2. `with atomic():`
   1. Category unknown → `ReferenceNotFound("category", id)`. Brand checked only when not `None`.
   2. For each of at most 3 candidates from `slug_candidates`: `products.add(product.with_slug(candidate))`, return
      the id; on `DuplicateSlug`, try the next.
   3. No candidate succeeded → `SlugUnavailable`.
3. `ReferenceNotFound` raised by `add` (the category or brand disappeared after the `TaxonomyLookup` check)
   propagates unchanged: it is not treated as `DuplicateSlug` and no further slug candidate is tried.
4. Any other exception propagates unchanged and is not retried.

The `TaxonomyLookup` check gives the normal-case error before any write; `add` is the authority for references at
persistence time. No locking is prescribed.

There is no slug pre-check; the unique constraint decides (architecture §5). The use case owns the transaction;
repositories never commit. In M2 each Django `add` runs in its own savepoint (ADR-0004). `RecordingAtomic` in the
fakes cannot roll back, so M1 does not claim rollback behaviour; "failure leaves no rows" is an M2 exit check on
PostgreSQL. No `durable=True` is introduced in M1.

| Failure | Raised as | Transaction |
| --- | --- | --- |
| Invariant broken | `InvalidProduct(field, code)` | never opened |
| Unknown category or brand at the lookup | `ReferenceNotFound` | exception leaves `atomic` |
| Category or brand removed between lookup and `add` | `ReferenceNotFound` from `add`, no retry | exception leaves `atomic` |
| Three slug collisions | `SlugUnavailable` | exception leaves `atomic` |
| Any other repository error | propagates | exception leaves `atomic` |

## Consequences for M2 (not implemented here)

- Columns and constraints aligned with the domain: `price`/`promo_price` `NUMERIC(10, 2)`; the two P4 `CHECK`s;
  `name` `varchar(200)` with a `CHECK` for non-empty and trimmed; `slug` `varchar(160)`, `UNIQUE`, with a format
  `CHECK`. The M2 spec confirms these.
- **PostgreSQL `NUMERIC(p, 2)` rounds over-precise values on direct writes; it does not reject them**, and no `CHECK`
  can see the value before rounding. "Rejected, never rounded" is therefore guaranteed through the use case and
  entity only. M2 must also check whether Django's `DecimalField` preparation rounds before the value reaches
  PostgreSQL.
- **`NUMERIC(10, 2)` and `CHECK (price > 0)` do not exclude `NaN`**: PostgreSQL accepts `NaN` in a constrained
  `numeric` column and orders it above every other value, so `NaN > 0` is true. M2 must enforce at database level the
  approved finite positive range for both prices, including the 99 999 999,99 maximum and the promotional-price
  relationship, and must test with direct writes (bypassing the use case) that `NaN`, `±Infinity`, zero, negative
  values, values above the maximum, a `NaN` promotional price and a promotional price equal to or above the normal
  price are all rejected.
- **Concurrent category/brand removal** (see "CreateProduct workflow"): the Django `add` must raise
  `ReferenceNotFound` for the affected reference, inside its savepoint, and store nothing. M2 must test this against
  PostgreSQL, covering when the foreign-key check fires (Django creates foreign keys as `DEFERRABLE INITIALLY
  DEFERRED`, so by default the violation surfaces at commit, outside the repository), savepoint handling,
  identification of the violated constraint by name, and translation to `ReferenceNotFound` rather than
  `DuplicateSlug`. The mechanism is M2's decision; no locking is prescribed.
- Python's `strip()` and PostgreSQL's whitespace handling differ; M2 aligns the name `CHECK` and tests a tab and a
  non-breaking space.
- Rehydration validates (ADR-0016). Until a first production release there are no stored rows, so M1/M2 may still
  tighten rules freely; afterwards any tightening follows the four steps in ADR-0016 Consequences. Image-free products
  stay valid when M3 adds the gallery. The name rule depends on `slug_from_name`, so a change to that helper (or to
  Python's Unicode data) that makes some name non-derivable is a tightening under that procedure.

## Acceptance criteria

- [x] AC1: before the first M1 code change, this spec shows `Approval: approved` and `docs/product.md`
  records P4, D12 (format and generation), N1 and N2 as approved requirements (§2 «Regras do produto», §7
  «Resolvidas»), D7 as resolved, and D18 and D12 (remaining) as open with their deadlines (M4; product-edit slice),
  with no contradiction with this spec.
- [x] AC2: every rule in "Product invariants" holds on direct construction, `dataclasses.replace` and `with_slug`;
  assigning to a field raises `FrozenInstanceError`. In particular a non-derivable name (`"!!!"`) with a valid slug is
  rejected through `Product.new`, direct construction, `dataclasses.replace(name="!!!")` and repository storage (the
  fake stores through the constructor; M2 rehydration uses the same constructor); a valid name with a valid slug that
  differs from the derived one is accepted.
- [x] AC3: price handling follows "Price representation": precision by value; factory canonicalises to exponent −2;
  direct construction keeps the given exponent; no value-changing rounding anywhere; results are identical under
  the default context and under restricted contexts with traps enabled; no `decimal` exception escapes.
- [x] AC4: slug derivation and candidates follow the approved policy, including the 160-character limit with suffix.
- [x] AC5: `CreateProduct` follows the workflow and error table, and its `add` attempts are bounded as follows:
  at most three `add` calls in total; it retries only after `DuplicateSlug`; it stops at the first successful `add`;
  a third `add` call occurs when the first two raise `DuplicateSlug`; `SlugUnavailable` is raised only when all three
  candidates raise `DuplicateSlug`; `ReferenceNotFound` raised by any `add` propagates immediately with no further
  `add`; any other repository exception propagates immediately with no further `add`.
- [x] AC6: the fakes pass the shared contract suite, whose classes are reusable by the M2 Django implementation.
- [x] AC7: no Django import in `domain` or `application` (direct or indirect); module boundaries respected; each new
  import-linter contract is shown to fail on a temporary fixture removed before merge.
- [x] AC8: `make test-fast` passes with `DJANGO_SETTINGS_MODULE` unset and collects more than 0 tests; the exit-5
  tolerance is removed from the Makefile.
- [x] AC9: no models, migrations, `INSTALLED_APPS` change, images, asset ports or `media` import.
- [x] AC10: `make check`, `make test` and CI are green; the spec status and the architecture §14 "Create product"
  row are updated in the implementation PR.

All criteria are met. PR #5 was merged into `main` on 2026-11-15 as `c3dc368`, with GitHub Actions green and the
independent Codex review approved; the evidence follows.

### Evidence (local run, 2026-11-15)

| AC | Evidence |
| --- | --- |
| AC1 | `Approval: approved` in this header; `docs/product.md` §2 «Regras do produto», §7 «Resolvidas» (P4, D12 formato e geração, N1, N2, D7 imagens), §7 «Em aberto» (D12 restante, D18) |
| AC2 | `test_domain.py`: the `construct` / `replace` / `with_slug` parametrised tests (`test_constructor_rejects_*`, `test_constructor_accepts_*`), `test_constructor_rejects_a_non_derivable_name_even_with_a_valid_slug`, `test_replace_rejects_renaming_to_a_non_derivable_name`, `test_constructor_accepts_a_slug_that_differs_from_the_derived_one`, `test_product_is_immutable`; the fake stores through the constructor (`replace`) and `get` rehydrates through it (`test_contracts_fake.py`) |
| AC3 | `test_factory_canonicalises_*`, `test_factory_rejects_invalid_prices_and_never_rounds_them`, `test_constructor_accepts_valid_prices_and_keeps_the_exponent`, `test_extreme_exponents_are_domain_errors_not_decimal_exceptions`, the thousands-of-trailing-zeros regression tests (`test_constructor_accepts_a_valid_price_with_thousands_of_trailing_zeros`, `test_factory_canonicalises_a_price_with_thousands_of_trailing_zeros_losslessly`, `test_factory_accepts_the_same_value_as_a_promotional_price`, `test_over_precise_price_with_thousands_of_digits_is_still_rejected`, `test_long_zero_prices_behave_the_same_in_every_decimal_context`), `test_price_validation_and_canonicalisation_do_not_depend_on_the_decimal_context` (five restricted contexts: `prec=3`, `ROUND_UP`, `ROUND_FLOOR`, `Inexact`/`Rounded`/`InvalidOperation` traps, narrow `Emax`/`Emin`), `test_ten_point_zero_zero_five_stays_rejected_under_every_rounding_mode` |
| AC4 | `test_slug_derivation`, `test_slug_is_truncated_to_160_without_a_trailing_hyphen`, `test_slug_candidates_*`, `test_every_derived_slug_and_candidate_is_a_valid_slug`, `test_constructor_rejects_invalid_slugs`, `test_constructor_enforces_the_slug_length_limit` |
| AC5 | `test_create_product.py`: `test_one_add_call_when_the_first_succeeds`, `test_a_taken_slug_gets_the_second_candidate`, `test_two_taken_slugs_give_the_third_candidate_with_exactly_three_calls`, `test_three_taken_slugs_raise_slug_unavailable_after_exactly_three_calls`, `test_never_makes_a_fourth_call`, `test_reference_removed_after_the_lookup_stops_after_exactly_one_call`, `test_brand_removed_after_the_lookup_is_reported_for_the_brand`, `test_reference_removed_after_a_collision_stops_after_exactly_two_calls`, `test_duplicate_slug_then_success_makes_exactly_two_calls`, `test_an_unexpected_repository_error_propagates_after_one_call`, `test_an_unexpected_error_after_a_collision_is_not_retried`, `test_invalid_input_raises_before_any_io_and_opens_no_transaction`, `test_unknown_category_*`, `test_unknown_brand_*`, `test_every_repository_call_happens_inside_a_single_atomic_block`, `test_the_atomic_block_sees_the_exception_on_failure` |
| AC6 | `test_contracts_fake.py`: `TestInMemoryProductRepository` (8 tests) and `TestInMemoryTaxonomy` (4 tests) subclass `ProductRepositoryContract` / `TaxonomyLookupContract` from `backend/catalog/tests/contracts.py`; `make typecheck` includes `test_contracts_fake.py` and checks its typed protocol assignments (a deliberately non-conforming assignment makes it fail, then reverted) |
| AC7 | `make check` exit 0 with 4 import-linter contracts kept. Temporary fixtures, removed afterwards (tree hash identical before and after): `import django` in a `*.domain` module → "Domain and application code is Django-free" BROKEN; `application → helper → django` → same contract BROKEN (indirect); `core` importing `catalog` → "catalog may import core, never the reverse" BROKEN; `catalog` importing `core.domain` and, separately, `core.transactions` → "use core only through its api.py" BROKEN |
| AC8 | `make test-fast` exit 0, 367 passed (325 `domain`, 42 `app`), run with `env -u DJANGO_SETTINGS_MODULE`; the exit-5 tolerance is gone from the `Makefile` (an empty selection now exits 5 and fails the target) |
| AC9 | `git status` shows no models, migrations, `INSTALLED_APPS` change, image field, asset port or `media` import; `makemigrations --check` reports "No changes detected" |
| Review | Independent Codex review of the implementation: **APPROVE**, no blocking findings; the two earlier findings (Decimal canonicalisation of values with thousands of trailing zeros; mypy coverage of the protocol-conformance assignments) are resolved. |
| AC10 | Local run before the PR: `make check` exit 0 (`make typecheck`: no issues in 11 source files, including `test_contracts_fake.py` and its fake-to-Protocol assignments); `make test` exit 0, 403 passed against PostgreSQL 17; `git diff --check` clean; architecture §14 row updated. **CI: PR #5 GitHub Actions passed, jobs `quality`, `test`, `migrations`, `security` and `secrets` all succeeded; merged into `main` on 2026-11-15 (`c3dc368`).** |

## Files expected to change

- New: `backend/core/{__init__,domain,transactions,api}.py`; `backend/catalog/{__init__,domain,application}.py`.
- New tests: `backend/catalog/tests/{__init__,builders,contracts,test_domain,test_create_product,test_contracts_fake}.py`;
  `tests/fakes/{__init__,core,catalog}.py`.
- Config: `pyproject.toml` (import-linter: catalog above core; `domain`/`application` must not import `django`; catalog
  must not import `core.domain` or `core.transactions` directly, indirect allowed); `Makefile` (contract suite and
  `test_contracts_fake.py`, which holds the fake-to-Protocol assignments, in `MYPY_SCOPE`; exit-5 tolerance removed from `test-fast`).
- Docs: this spec, `docs/product.md`, `docs/architecture.md` §14.

## Tests to add

- **domain** (`domain` marker):
  - Prices: accepted `10`, `10.5`, `10.50`, `10.500`, `99999999.99`; rejected `0`, `-0`, `-1`, `0.001`, `10.005`,
    `100000000.00`, NaN, sNaN, ±Inf, `float`, `int`, `str`, extreme exponent. Direct construction with
    `Decimal("10.5")` is accepted and the exponent is preserved; the factory returns exponent −2 for every accepted
    input and leaves a value that would change numerically unconverted so the constructor rejects it.
  - Decimal context: the accepted and rejected price tables above, and factory canonicalisation, give the same
    results inside `decimal.localcontext()` with (a) a deliberately small precision (for example `prec=3`, so that
    `99999999.99` and canonicalising to two places exceed it), (b) a non-default rounding mode, and (c) the `Inexact`,
    `Rounded` and `InvalidOperation` traps enabled. `10.005` and `0.001` stay rejected under every rounding mode, sNaN
    and extreme exponents yield `InvalidProduct`, and the ambient context is unchanged after each call.
  - Promotional price: `None`; rejected when equal, greater, zero, over-precise.
  - Name: trimmed by the factory; blank, empty, non-`str` rejected; 200 accepted, 201 rejected; constructor rejects
    untrimmed. Description: empty accepted; untrimmed and non-`str` rejected by the constructor.
  - Ids: for category and brand, `0`, `-1`, `True`, `"1"`, `1.0` rejected; `None` rejected for category, accepted for
    brand.
  - Slugs: derivation table (Portuguese accents, `º`, punctuation runs, leading/trailing symbols, digits only, `ß`,
    200-character name truncated to 160); symbol-only and non-Latin-only names give `slug_not_derivable`; candidates
    table including truncation, every candidate ≤ 160; constructor rejects invalid slugs.
  - Slug derivability in the constructor: `name="!!!"` with `slug="valid"` raises `slug_not_derivable` through direct
    construction and `dataclasses.replace(product, name="!!!")`; `Product.new(name="!!!", …)` raises the same code;
    `name="Bicicleta Nova"` with `slug="outro-slug"` is accepted.
- **app** (`app` marker, fakes):
  - Happy path returns an id and stores normalised fields; `None` brand and `None` promo both work.
  - Invalid input raises `InvalidProduct` with nothing stored and the journal empty.
  - Unknown category and unknown brand raise `ReferenceNotFound`; a `None` brand is not looked up.
  - Collisions: `x` taken → `x-2`; `x`, `x-2` taken → `x-3`; all three taken → `SlugUnavailable` after exactly 3
    `add` calls, nothing stored.
  - One `atomic` block around all repository calls; `atomic` sees failures; an unexpected repository error propagates
    without retry.
  - Concurrent removal: the taxonomy fake reports the category (or brand) as existing, but the repository fake raises
    `ReferenceNotFound` from `add` for it. The use case raises `ReferenceNotFound` for that reference after exactly one
    `add` call (no slug retry, not `SlugUnavailable`), nothing is stored, and `atomic` sees the exception.
  - Removal after a collision: the first `add` raises `DuplicateSlug` and the second raises `ReferenceNotFound`. The
    use case stops after exactly two `add` calls (the second with the `-2` candidate), raises `ReferenceNotFound` for
    that reference (not `SlugUnavailable`), nothing is stored, and `atomic` sees the exception.
  - Attempt counts: a successful first `add` gives exactly one call; `DuplicateSlug` then success gives exactly two;
    `DuplicateSlug` twice then success on the third candidate (`-3`) gives exactly three calls and returns the id, with
    no `SlugUnavailable`; `DuplicateSlug` on all three gives exactly three calls and `SlugUnavailable`; an unexpected
    repository exception on the first `add` gives exactly one call and propagates unchanged.
- **contract suite** (fake half in M1, Django half in M2 through the same classes):
  - `add` then `get` round-trips every field, including a 200-character name, a 160-character slug, `99999999.99`,
    `None` brand and `None` promo; prices compare by value.
  - Ids are distinct; a duplicate slug raises `DuplicateSlug` and leaves state unchanged; another `add` after
    `DuplicateSlug` in the same transaction succeeds (the PostgreSQL savepoint proof in M2); `get` of an unknown id
    returns `None`; `TaxonomyLookup` answers true and false correctly.
  - `add` with a category or brand unknown to the repository raises `ReferenceNotFound` for that reference (not
    `DuplicateSlug`) and stores nothing; another `add` in the same transaction then succeeds. The fixture provides the
    known categories and brands to each implementation.
- **typing**: mypy checks the fakes against the protocols through typed assignments.

## Implementation order (single PR, after the approval change)

One focused PR, split only if a concrete review or integration benefit appears. Suggested commits: (1) `core`,
import-linter contracts with fixture proofs, Makefile; (2) `Product` and factory with domain tests; (3) slug policy
with tests; (4) contracts, errors, command; (5) fakes, builders, contract suite; (6) `CreateProduct` with tests;
(7) docs and evidence.

## Risks and checks at the start of the implementation

- import-linter wildcard support and handling of modules that do not exist yet on the pinned version; fallback: list
  modules explicitly.
- import-linter with `backend/catalog/tests` importing `tests.fakes`; fallback: move the tests to `tests/catalog/`,
  as M0 did.
- The fake can diverge from PostgreSQL; mitigated by the add-after-`DuplicateSlug` contract test and by M2 running the
  same suite.
