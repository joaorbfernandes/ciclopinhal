"""CreateProduct against in-memory fakes (SPEC-002). No Django settings, no database."""

from dataclasses import replace
from decimal import Decimal

import pytest

from backend.catalog.application import CreateProduct, DuplicateSlug, SlugUnavailable
from backend.catalog.domain import BrandId, CategoryId, InvalidProduct, Product, ProductId
from backend.catalog.tests.builders import a_command
from backend.core.api import ReferenceNotFound
from tests.fakes.catalog import InMemoryProductRepository, InMemoryTaxonomy
from tests.fakes.core import RecordingAtomic

pytestmark = pytest.mark.app


class World:
    """One journal shared by the transaction, the taxonomy and the repository fakes."""

    def __init__(self) -> None:
        self.journal: list[str] = []
        self.atomic = RecordingAtomic(self.journal)
        self.taxonomy = InMemoryTaxonomy(categories={1}, brands={1}, journal=self.journal)
        self.products = InMemoryProductRepository(taxonomy=None, journal=self.journal)
        self.use_case = CreateProduct(products=self.products, taxonomy=self.taxonomy, atomic=self.atomic)

    def seed(self, *slugs: str) -> None:
        for slug in slugs:
            self.products.add(
                Product(
                    id=None,
                    name="Seed",
                    slug=slug,
                    description="",
                    category_id=CategoryId(1),
                    brand_id=None,
                    price=Decimal("1.00"),
                    promo_price=None,
                )
            )
        self.journal.clear()
        self.products.add_calls.clear()


@pytest.fixture
def world() -> World:
    return World()


def test_creates_a_product_and_returns_its_id(world: World) -> None:
    product_id = world.use_case.execute(a_command())

    assert world.products.get(product_id) == Product(
        id=product_id,
        name="Bicicleta de Estrada",
        slug="bicicleta-de-estrada",
        description="Quadro em alumínio.",
        category_id=CategoryId(1),
        brand_id=BrandId(1),
        price=Decimal("199.90"),
        promo_price=Decimal("149.90"),
    )


def test_stores_the_normalised_entity(world: World) -> None:
    product_id = world.use_case.execute(
        a_command(name="  Câmara de Ar  ", description="  útil ", price=Decimal("10.5"), promo_price=Decimal("5"))
    )

    stored = world.products.get(product_id)
    assert stored is not None
    assert (stored.name, stored.slug, stored.description) == ("Câmara de Ar", "camara-de-ar", "útil")
    assert stored.price.as_tuple() == Decimal("10.50").as_tuple()
    assert stored.promo_price is not None and stored.promo_price.as_tuple() == Decimal("5.00").as_tuple()


def test_works_without_brand_and_without_promotional_price(world: World) -> None:
    product_id = world.use_case.execute(a_command(brand_id=None, promo_price=None))

    stored = world.products.get(product_id)
    assert stored is not None and stored.brand_id is None and stored.promo_price is None
    assert "brand_exists:1" not in world.journal  # a missing brand is not looked up


def test_checks_the_category_and_the_brand_inside_one_transaction(world: World) -> None:
    world.use_case.execute(a_command())

    assert world.journal == ["begin", "category_exists:1", "brand_exists:1", "add:bicicleta-de-estrada", "end"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "   "},
        {"name": "!!!"},
        {"name": "a" * 201},
        {"price": Decimal("0")},
        {"price": Decimal("10.005")},
        {"price": 10.5},
        {"promo_price": Decimal("199.90")},
        {"category_id": 0},
        {"brand_id": True},
    ],
    ids=lambda overrides: str(sorted(overrides)),
)
def test_invalid_input_raises_before_any_io_and_opens_no_transaction(
    world: World, overrides: dict[str, object]
) -> None:
    with pytest.raises(InvalidProduct):
        world.use_case.execute(a_command(**overrides))

    assert world.journal == []
    assert world.products.stored == []
    assert world.products.add_calls == []


def test_unknown_category_raises_reference_not_found_and_stores_nothing(world: World) -> None:
    with pytest.raises(ReferenceNotFound) as raised:
        world.use_case.execute(a_command(category_id=CategoryId(99)))

    assert (raised.value.reference, raised.value.id) == ("category", 99)
    assert world.products.add_calls == [] and world.products.stored == []
    assert world.atomic.exceptions == [raised.value]


def test_unknown_brand_raises_reference_not_found_and_stores_nothing(world: World) -> None:
    with pytest.raises(ReferenceNotFound) as raised:
        world.use_case.execute(a_command(brand_id=BrandId(99)))

    assert (raised.value.reference, raised.value.id) == ("brand", 99)
    assert world.products.add_calls == [] and world.products.stored == []
    assert world.atomic.exceptions == [raised.value]


# --- Slug collisions and attempt counts ---------------------------------------------------------------------------


def test_one_add_call_when_the_first_succeeds(world: World) -> None:
    world.use_case.execute(a_command())

    assert world.products.add_calls == ["bicicleta-de-estrada"]


def test_a_taken_slug_gets_the_second_candidate(world: World) -> None:
    world.seed("bicicleta-de-estrada")

    product_id = world.use_case.execute(a_command())

    assert world.products.add_calls == ["bicicleta-de-estrada", "bicicleta-de-estrada-2"]
    stored = world.products.get(product_id)
    assert stored is not None and stored.slug == "bicicleta-de-estrada-2"


def test_two_taken_slugs_give_the_third_candidate_with_exactly_three_calls(world: World) -> None:
    world.seed("bicicleta-de-estrada", "bicicleta-de-estrada-2")

    product_id = world.use_case.execute(a_command())

    assert world.products.add_calls == ["bicicleta-de-estrada", "bicicleta-de-estrada-2", "bicicleta-de-estrada-3"]
    stored = world.products.get(product_id)
    assert stored is not None and stored.slug == "bicicleta-de-estrada-3"
    assert "SlugUnavailable" not in repr(world.atomic.exceptions)
    assert world.journal[-1] == "end"


def test_three_taken_slugs_raise_slug_unavailable_after_exactly_three_calls(world: World) -> None:
    world.seed("bicicleta-de-estrada", "bicicleta-de-estrada-2", "bicicleta-de-estrada-3")
    before = len(world.products.stored)

    with pytest.raises(SlugUnavailable):
        world.use_case.execute(a_command())

    assert len(world.products.add_calls) == 3
    assert len(world.products.stored) == before
    assert isinstance(world.atomic.exceptions[0], SlugUnavailable)


def test_never_makes_a_fourth_call(world: World) -> None:
    world.products.script.extend([DuplicateSlug("a"), DuplicateSlug("b"), DuplicateSlug("c"), None])

    with pytest.raises(SlugUnavailable):
        world.use_case.execute(a_command())

    assert len(world.products.add_calls) == 3


# --- ReferenceNotFound and unexpected errors are never retried ------------------------------------------------------


def test_reference_removed_after_the_lookup_stops_after_exactly_one_call(world: World) -> None:
    world.products.script.append(ReferenceNotFound("category", 1))

    with pytest.raises(ReferenceNotFound) as raised:
        world.use_case.execute(a_command())

    assert (raised.value.reference, raised.value.id) == ("category", 1)
    assert world.products.add_calls == ["bicicleta-de-estrada"]
    assert world.products.stored == []
    assert world.atomic.exceptions == [raised.value]
    assert world.journal[-1] == "end:error"


def test_brand_removed_after_the_lookup_is_reported_for_the_brand(world: World) -> None:
    world.products.script.append(ReferenceNotFound("brand", 1))

    with pytest.raises(ReferenceNotFound) as raised:
        world.use_case.execute(a_command())

    assert raised.value.reference == "brand"
    assert len(world.products.add_calls) == 1


def test_reference_removed_after_a_collision_stops_after_exactly_two_calls(world: World) -> None:
    world.products.script.extend([DuplicateSlug("taken"), ReferenceNotFound("category", 1)])

    with pytest.raises(ReferenceNotFound) as raised:
        world.use_case.execute(a_command())

    assert raised.value.reference == "category"
    assert world.products.add_calls == ["bicicleta-de-estrada", "bicicleta-de-estrada-2"]
    assert world.products.stored == []
    assert world.atomic.exceptions == [raised.value]


def test_duplicate_slug_then_success_makes_exactly_two_calls(world: World) -> None:
    world.products.script.append(DuplicateSlug("taken"))

    world.use_case.execute(a_command())

    assert len(world.products.add_calls) == 2
    assert len(world.products.stored) == 1


def test_an_unexpected_repository_error_propagates_after_one_call(world: World) -> None:
    boom = RuntimeError("database is down")
    world.products.script.append(boom)

    with pytest.raises(RuntimeError) as raised:
        world.use_case.execute(a_command())

    assert raised.value is boom
    assert len(world.products.add_calls) == 1
    assert world.atomic.exceptions == [boom]


def test_an_unexpected_error_after_a_collision_is_not_retried(world: World) -> None:
    boom = RuntimeError("database is down")
    world.products.script.extend([DuplicateSlug("taken"), boom])

    with pytest.raises(RuntimeError):
        world.use_case.execute(a_command())

    assert len(world.products.add_calls) == 2


# --- One transaction ----------------------------------------------------------------------------------------------


def test_every_repository_call_happens_inside_a_single_atomic_block(world: World) -> None:
    world.seed("bicicleta-de-estrada")

    world.use_case.execute(a_command())

    assert world.journal.count("begin") == 1
    assert world.journal[0] == "begin" and world.journal[-1] == "end"
    assert all(entry.startswith(("add:", "category_exists", "brand_exists")) for entry in world.journal[1:-1])


def test_the_atomic_block_sees_the_exception_on_failure(world: World) -> None:
    world.seed("bicicleta-de-estrada", "bicicleta-de-estrada-2", "bicicleta-de-estrada-3")

    with pytest.raises(SlugUnavailable) as raised:
        world.use_case.execute(a_command())

    assert world.atomic.exceptions == [raised.value]
    assert world.journal[0] == "begin" and world.journal[-1] == "end:error"


def test_the_command_is_not_modified(world: World) -> None:
    command = a_command(name="  x  ")
    snapshot = replace(command)

    world.use_case.execute(command)

    assert command == snapshot


def test_product_id_type_is_returned(world: World) -> None:
    assert isinstance(world.use_case.execute(a_command()), int)
    assert world.use_case.execute(a_command(name="Outro")) == ProductId(2)
