"""Catalog application layer: repository contracts and the CreateProduct use case (SPEC-002).

Pure Python: no Django. Contracts are owned here, next to the use case that needs them (ADR-0003).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from backend.catalog.domain import BrandId, CategoryId, Product, ProductId, slug_candidates
from backend.core.api import Atomic, DomainError, ReferenceNotFound


class DuplicateSlug(DomainError):
    """Outcome of `ProductRepository.add` when the slug is taken. Handled by the use case; not a public error."""


class SlugUnavailable(DomainError):
    """Every slug candidate was taken."""


class ProductRepository(Protocol):
    """Persistence of the Product aggregate, in domain terms (ADR-0016).

    `add` requires `product.id is None`, never commits, and stores nothing when it raises:
      - `DuplicateSlug` when the slug is taken;
      - `ReferenceNotFound("category" | "brand", id)` when the referenced category or brand does not exist at
        persistence time (it may have been removed after the use case checked it).
    `get` rehydrates through the `Product` constructor, so a stored state that breaks an invariant fails to load.
    """

    def add(self, product: Product) -> ProductId: ...

    def get(self, product_id: ProductId) -> Product | None: ...


class TaxonomyLookup(Protocol):
    """Existence of the categories and brands a product may reference."""

    def category_exists(self, category_id: CategoryId) -> bool: ...

    def brand_exists(self, brand_id: BrandId) -> bool: ...


@dataclass(frozen=True, kw_only=True)
class CreateProductCommand:
    name: str
    description: str
    category_id: CategoryId
    brand_id: BrandId | None
    price: Decimal
    promo_price: Decimal | None


class CreateProduct:
    MAX_SLUG_ATTEMPTS = 3

    def __init__(self, *, products: ProductRepository, taxonomy: TaxonomyLookup, atomic: Atomic) -> None:
        self._products = products
        self._taxonomy = taxonomy
        self._atomic = atomic

    def execute(self, command: CreateProductCommand) -> ProductId:
        # Raises InvalidProduct before any I/O; no transaction is opened for invalid input.
        product = Product.new(
            name=command.name,
            description=command.description,
            category_id=command.category_id,
            brand_id=command.brand_id,
            price=command.price,
            promo_price=command.promo_price,
        )
        with self._atomic():
            if not self._taxonomy.category_exists(product.category_id):
                raise ReferenceNotFound("category", product.category_id)
            if product.brand_id is not None and not self._taxonomy.brand_exists(product.brand_id):
                raise ReferenceNotFound("brand", product.brand_id)
            # No slug pre-check: the unique constraint decides. Retry only after DuplicateSlug; ReferenceNotFound and
            # any other error propagate immediately.
            for candidate in slug_candidates(product.slug, self.MAX_SLUG_ATTEMPTS):
                try:
                    return self._products.add(product.with_slug(candidate))
                except DuplicateSlug:
                    continue
            raise SlugUnavailable("every slug candidate is taken")
