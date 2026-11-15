"""In-memory implementations of the catalog contracts."""

from collections import deque
from collections.abc import Iterable
from dataclasses import replace

from backend.catalog.application import DuplicateSlug
from backend.catalog.domain import BrandId, CategoryId, Product, ProductId
from backend.core.api import ReferenceNotFound


class InMemoryTaxonomy:
    """`TaxonomyLookup` over fixed sets of ids. Lookups are journaled when a journal is given."""

    def __init__(
        self,
        *,
        categories: Iterable[int] = (),
        brands: Iterable[int] = (),
        journal: list[str] | None = None,
    ) -> None:
        self.categories = set(categories)
        self.brands = set(brands)
        self._journal = journal

    def category_exists(self, category_id: CategoryId) -> bool:
        if self._journal is not None:
            self._journal.append(f"category_exists:{category_id}")
        return category_id in self.categories

    def brand_exists(self, brand_id: BrandId) -> bool:
        if self._journal is not None:
            self._journal.append(f"brand_exists:{brand_id}")
        return brand_id in self.brands


class InMemoryProductRepository:
    """`ProductRepository` in memory.

    Storage goes through the `Product` constructor (`replace`), so an invalid state cannot be stored. When a taxonomy is
    given, `add` checks the references like a database foreign key would. `script` queues outcomes for the next `add`
    calls: an exception is raised, `None` means "behave normally"; it simulates what the real database may do (a
    reference removed after the use case's check, an unexpected failure).
    """

    def __init__(self, *, taxonomy: InMemoryTaxonomy | None = None, journal: list[str] | None = None) -> None:
        self._taxonomy = taxonomy
        self._journal = journal
        self._rows: dict[ProductId, Product] = {}
        self._slugs: set[str] = set()
        self._next_id = 1
        self.script: deque[Exception | None] = deque()
        self.add_calls: list[str] = []  # the slug of every `add` call, in order

    def add(self, product: Product) -> ProductId:
        if product.id is not None:
            raise ValueError("add() requires a product without an id")
        self.add_calls.append(product.slug)
        if self._journal is not None:
            self._journal.append(f"add:{product.slug}")
        if self.script:
            outcome = self.script.popleft()
            if outcome is not None:
                raise outcome
        if self._taxonomy is not None:
            if not self._taxonomy.category_exists(product.category_id):
                raise ReferenceNotFound("category", product.category_id)
            if product.brand_id is not None and not self._taxonomy.brand_exists(product.brand_id):
                raise ReferenceNotFound("brand", product.brand_id)
        if product.slug in self._slugs:
            raise DuplicateSlug(product.slug)
        product_id = ProductId(self._next_id)
        self._next_id += 1
        self._rows[product_id] = replace(product, id=product_id)
        self._slugs.add(product.slug)
        return product_id

    def get(self, product_id: ProductId) -> Product | None:
        stored = self._rows.get(product_id)
        return None if stored is None else replace(stored)  # rehydrates through the constructor

    @property
    def stored(self) -> list[Product]:
        return list(self._rows.values())
