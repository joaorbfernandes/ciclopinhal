"""The shared contract suite run against the in-memory fakes (the Django half arrives in M2)."""

import pytest

from backend.catalog.application import ProductRepository, TaxonomyLookup
from backend.catalog.domain import BrandId, CategoryId
from backend.catalog.tests.contracts import (
    ProductRepositoryContract,
    RepositoryEnvironment,
    TaxonomyEnvironment,
    TaxonomyLookupContract,
)
from tests.fakes.catalog import InMemoryProductRepository, InMemoryTaxonomy

pytestmark = pytest.mark.app


class TestInMemoryProductRepository(ProductRepositoryContract):
    @pytest.fixture
    def environment(self) -> RepositoryEnvironment:
        taxonomy = InMemoryTaxonomy(categories={1}, brands={1})
        repository: ProductRepository = InMemoryProductRepository(taxonomy=taxonomy)  # typing: conforms to the protocol
        return RepositoryEnvironment(
            repository=repository,
            category_id=CategoryId(1),
            brand_id=BrandId(1),
            missing_category_id=CategoryId(2),
            missing_brand_id=BrandId(2),
        )


class TestInMemoryTaxonomy(TaxonomyLookupContract):
    @pytest.fixture
    def environment(self) -> TaxonomyEnvironment:
        taxonomy: TaxonomyLookup = InMemoryTaxonomy(categories={1}, brands={1})  # typing: conforms to the protocol
        return TaxonomyEnvironment(
            taxonomy=taxonomy,
            category_id=CategoryId(1),
            brand_id=BrandId(1),
            missing_category_id=CategoryId(2),
            missing_brand_id=BrandId(2),
        )
