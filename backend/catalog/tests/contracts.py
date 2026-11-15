"""Shared contract suite for the catalog contracts (ADR-0003).

The classes are not collected on their own. Each implementation subclasses them in a `Test...` class and provides the
`environment` fixture: M1 runs them against the in-memory fakes, M2 runs the same classes against the Django
implementations on PostgreSQL.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

import pytest

from backend.catalog.application import DuplicateSlug, ProductRepository, TaxonomyLookup
from backend.catalog.domain import BrandId, CategoryId, Product, ProductId
from backend.catalog.tests.builders import a_product
from backend.core.api import ReferenceNotFound


@dataclass(frozen=True)
class RepositoryEnvironment:
    """A repository plus ids it knows (`category_id`, `brand_id`) and ids it does not (`missing_*`)."""

    repository: ProductRepository
    category_id: CategoryId
    brand_id: BrandId
    missing_category_id: CategoryId
    missing_brand_id: BrandId


@dataclass(frozen=True)
class TaxonomyEnvironment:
    taxonomy: TaxonomyLookup
    category_id: CategoryId
    brand_id: BrandId
    missing_category_id: CategoryId
    missing_brand_id: BrandId


class ProductRepositoryContract:
    @pytest.fixture
    def environment(self) -> RepositoryEnvironment:
        raise NotImplementedError("the implementation's test class provides this fixture")

    def _product(self, environment: RepositoryEnvironment, **overrides: object) -> Product:
        fields: dict[str, object] = {"category_id": environment.category_id, "brand_id": environment.brand_id}
        fields.update(overrides)
        return a_product(**fields)

    def test_add_then_get_round_trips_every_field(self, environment: RepositoryEnvironment) -> None:
        repository = environment.repository
        product = self._product(environment)

        product_id = repository.add(product)

        assert repository.get(product_id) == replace(product, id=product_id)

    def test_round_trip_keeps_boundary_values_and_nones(self, environment: RepositoryEnvironment) -> None:
        repository = environment.repository
        boundary = self._product(
            environment,
            name="N" * 200,
            slug="s" * 160,
            description="",
            price=Decimal("99999999.99"),
            promo_price=Decimal("99999999.98"),
        )
        bare = self._product(environment, slug="bare", brand_id=None, promo_price=None, price=Decimal("0.01"))

        boundary_id = repository.add(boundary)
        bare_id = repository.add(bare)

        assert repository.get(boundary_id) == replace(boundary, id=boundary_id)  # prices compare by value
        assert repository.get(bare_id) == replace(bare, id=bare_id)

    def test_ids_are_distinct(self, environment: RepositoryEnvironment) -> None:
        repository = environment.repository

        first = repository.add(self._product(environment, slug="one"))
        second = repository.add(self._product(environment, slug="two"))

        assert first != second

    def test_get_unknown_id_returns_none(self, environment: RepositoryEnvironment) -> None:
        assert environment.repository.get(ProductId(987654321)) is None

    def test_duplicate_slug_raises_and_leaves_state_unchanged(self, environment: RepositoryEnvironment) -> None:
        repository = environment.repository
        first = self._product(environment, slug="taken", name="First")
        first_id = repository.add(first)

        with pytest.raises(DuplicateSlug):
            repository.add(self._product(environment, slug="taken", name="Second"))

        assert repository.get(first_id) == replace(first, id=first_id)

    def test_add_after_duplicate_slug_succeeds_in_the_same_transaction(
        self, environment: RepositoryEnvironment
    ) -> None:
        # On PostgreSQL this proves the repository's savepoint: without it the failed statement aborts the transaction.
        repository = environment.repository
        repository.add(self._product(environment, slug="taken"))
        with pytest.raises(DuplicateSlug):
            repository.add(self._product(environment, slug="taken"))

        product_id = repository.add(self._product(environment, slug="taken-2"))

        assert repository.get(product_id) is not None

    def test_unknown_category_raises_reference_not_found_and_stores_nothing(
        self, environment: RepositoryEnvironment
    ) -> None:
        repository = environment.repository

        with pytest.raises(ReferenceNotFound) as raised:
            repository.add(self._product(environment, slug="orphan", category_id=environment.missing_category_id))

        assert (raised.value.reference, raised.value.id) == ("category", environment.missing_category_id)
        # Nothing was stored, so the slug is still free and the same transaction can continue.
        assert repository.get(repository.add(self._product(environment, slug="orphan"))) is not None

    def test_unknown_brand_raises_reference_not_found_and_stores_nothing(
        self, environment: RepositoryEnvironment
    ) -> None:
        repository = environment.repository

        with pytest.raises(ReferenceNotFound) as raised:
            repository.add(self._product(environment, slug="orphan", brand_id=environment.missing_brand_id))

        assert (raised.value.reference, raised.value.id) == ("brand", environment.missing_brand_id)
        assert repository.get(repository.add(self._product(environment, slug="orphan"))) is not None


class TaxonomyLookupContract:
    @pytest.fixture
    def environment(self) -> TaxonomyEnvironment:
        raise NotImplementedError("the implementation's test class provides this fixture")

    def test_known_category_exists(self, environment: TaxonomyEnvironment) -> None:
        assert environment.taxonomy.category_exists(environment.category_id) is True

    def test_unknown_category_does_not_exist(self, environment: TaxonomyEnvironment) -> None:
        assert environment.taxonomy.category_exists(environment.missing_category_id) is False

    def test_known_brand_exists(self, environment: TaxonomyEnvironment) -> None:
        assert environment.taxonomy.brand_exists(environment.brand_id) is True

    def test_unknown_brand_does_not_exist(self, environment: TaxonomyEnvironment) -> None:
        assert environment.taxonomy.brand_exists(environment.missing_brand_id) is False
