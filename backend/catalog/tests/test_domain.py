"""Product invariants, factory normalisation and slug policy (SPEC-002). Pure Python, no Django settings."""

import dataclasses
import decimal
from decimal import Decimal

import pytest

from backend.catalog.domain import (
    BrandId,
    CategoryId,
    InvalidProduct,
    Product,
    ProductId,
    slug_candidates,
    slug_from_name,
)
from backend.catalog.tests.builders import a_product

pytestmark = pytest.mark.domain

D = Decimal


def new_product(**overrides: object) -> Product:
    fields: dict[str, object] = {
        "name": "Bicicleta de Estrada",
        "description": "Quadro em alumínio.",
        "category_id": CategoryId(1),
        "brand_id": BrandId(1),
        "price": D("199.90"),
        "promo_price": D("149.90"),
    }
    fields.update(overrides)
    return Product.new(**fields)  # type: ignore[arg-type]


def rejection(call: object) -> tuple[str, str]:
    assert callable(call)
    with pytest.raises(InvalidProduct) as raised:
        call()
    return raised.value.field, raised.value.code


# The three ways to build a Product from already-normalised field values; every invariant must hold on each.
def _construct(**fields: object) -> Product:
    return Product(**{**dataclasses.asdict(a_product()), **fields})  # type: ignore[arg-type]


def _replace(**fields: object) -> Product:
    return dataclasses.replace(a_product(), **fields)  # type: ignore[arg-type]


def _with_slug(**fields: object) -> Product:
    slug = fields.pop("slug", None)
    base = dataclasses.replace(a_product(), **fields) if fields else a_product()  # type: ignore[arg-type]
    return base.with_slug(slug) if slug is not None else base  # type: ignore[arg-type]


PATHS = pytest.mark.parametrize("build", [_construct, _replace, _with_slug], ids=["construct", "replace", "with_slug"])

# --- Prices -----------------------------------------------------------------------------------------------------

VALID_PRICES = ["10", "10.5", "10.50", "10.500", "0.01", "99999999.99", "1E+2", "0.010"]
INVALID_PRICES = [
    ("0", "not_positive"),
    ("-0", "not_positive"),
    ("-1", "not_positive"),
    ("-0.01", "not_positive"),
    ("0.001", "too_precise"),
    ("10.005", "too_precise"),
    ("10.0051", "too_precise"),
    ("100000000.00", "too_large"),
    ("99999999.991", "too_large"),
    ("1E+30", "too_large"),
    ("NaN", "not_finite"),
    ("sNaN", "not_finite"),
    ("Infinity", "not_finite"),
    ("-Infinity", "not_finite"),
]


@PATHS
@pytest.mark.parametrize("text", VALID_PRICES)
def test_constructor_accepts_valid_prices_and_keeps_the_exponent(build: object, text: str) -> None:
    product = build(price=D(text), promo_price=None)  # type: ignore[operator]
    assert product.price == D(text)
    assert product.price.as_tuple() == D(text).as_tuple()  # direct construction does not canonicalise


@PATHS
@pytest.mark.parametrize(("text", "code"), INVALID_PRICES)
def test_constructor_rejects_invalid_prices(build: object, text: str, code: str) -> None:
    assert rejection(lambda: build(price=D(text), promo_price=None)) == ("price", code)  # type: ignore[operator]


@pytest.mark.parametrize("value", [10.5, 10, "10.50", True, object()])
def test_constructor_rejects_non_decimal_prices(value: object) -> None:
    assert rejection(lambda: _construct(price=value)) == ("price", "invalid_type")
    assert rejection(lambda: _construct(promo_price=value)) == ("promo_price", "invalid_type")


@pytest.mark.parametrize("text", VALID_PRICES)
def test_factory_canonicalises_accepted_prices_to_two_places_without_changing_the_value(text: str) -> None:
    product = new_product(price=D(text), promo_price=None)
    assert product.price == D(text)
    assert product.price.as_tuple().exponent == -2


def test_factory_canonicalises_the_promotional_price_too() -> None:
    product = new_product(price=D("10"), promo_price=D("5.5"))
    assert product.price.as_tuple() == D("10.00").as_tuple()
    assert product.promo_price is not None
    assert product.promo_price.as_tuple() == D("5.50").as_tuple()


@pytest.mark.parametrize(("text", "code"), INVALID_PRICES)
def test_factory_rejects_invalid_prices_and_never_rounds_them(text: str, code: str) -> None:
    assert rejection(lambda: new_product(price=D(text), promo_price=None)) == ("price", code)


def test_extreme_exponents_are_domain_errors_not_decimal_exceptions() -> None:
    assert rejection(lambda: new_product(price=D("1E+999999999"), promo_price=None)) == ("price", "too_large")
    assert rejection(lambda: new_product(price=D("1E-999999999"), promo_price=None)) == ("price", "too_precise")
    assert rejection(lambda: new_product(price=D("1E+3"), promo_price=D("1E-999999999"))) == (
        "promo_price",
        "too_precise",
    )


# A numerically valid price may carry thousands of insignificant trailing zeros; nothing may convert such a
# coefficient to int (Python's integer string-conversion limit would raise a raw ValueError).
LONG_ZEROS = D("1." + "0" * 5000)
LONG_ZEROS_OVER_PRECISE = D("1." + "0" * 5000 + "1")


@PATHS
def test_constructor_accepts_a_valid_price_with_thousands_of_trailing_zeros(build: object) -> None:
    product = build(price=LONG_ZEROS, promo_price=None)  # type: ignore[operator]
    assert product.price == D("1")


def test_factory_canonicalises_a_price_with_thousands_of_trailing_zeros_losslessly() -> None:
    product = new_product(price=LONG_ZEROS, promo_price=None)
    assert product.price.as_tuple() == D("1.00").as_tuple()


def test_factory_accepts_the_same_value_as_a_promotional_price() -> None:
    product = new_product(price=D("2"), promo_price=LONG_ZEROS)
    assert product.promo_price is not None
    assert product.promo_price.as_tuple() == D("1.00").as_tuple()
    assert product.price.as_tuple() == D("2.00").as_tuple()


def test_the_long_zero_price_is_not_below_an_equal_price() -> None:
    assert rejection(lambda: new_product(price=D("1"), promo_price=LONG_ZEROS)) == ("promo_price", "not_below_price")


@PATHS
def test_over_precise_price_with_thousands_of_digits_is_still_rejected(build: object) -> None:
    assert rejection(lambda: build(price=LONG_ZEROS_OVER_PRECISE, promo_price=None)) == ("price", "too_precise")  # type: ignore[operator]
    assert rejection(lambda: new_product(price=LONG_ZEROS_OVER_PRECISE, promo_price=None)) == ("price", "too_precise")


def test_long_zero_prices_behave_the_same_in_every_decimal_context(restricted_context: decimal.Context) -> None:
    def outcome() -> object:
        product = new_product(price=D("2"), promo_price=LONG_ZEROS)
        return product.price.as_tuple(), None if product.promo_price is None else product.promo_price.as_tuple()

    expected = outcome()
    with decimal.localcontext(restricted_context):
        assert outcome() == expected
        assert rejection(lambda: new_product(price=LONG_ZEROS_OVER_PRECISE, promo_price=None)) == (
            "price",
            "too_precise",
        )


PROMO_CASES = [
    ("10.00", "10.00", "not_below_price"),
    ("10.00", "10.01", "not_below_price"),
    ("10.00", "20", "not_below_price"),
    ("10.00", "0", "not_positive"),
    ("10.00", "-1", "not_positive"),
    ("10.00", "5.005", "too_precise"),
    ("10.00", "NaN", "not_finite"),
    ("10.00", "100000000", "too_large"),
]


@PATHS
@pytest.mark.parametrize(("price", "promo", "code"), PROMO_CASES)
def test_constructor_rejects_invalid_promotional_prices(build: object, price: str, promo: str, code: str) -> None:
    assert rejection(lambda: build(price=D(price), promo_price=D(promo))) == ("promo_price", code)  # type: ignore[operator]


@PATHS
@pytest.mark.parametrize("promo", ["9.99", "0.01", "9.990", None])
def test_constructor_accepts_none_or_a_lower_promotional_price(build: object, promo: str | None) -> None:
    product = build(price=D("10.00"), promo_price=None if promo is None else D(promo))  # type: ignore[operator]
    assert (product.promo_price is None) == (promo is None)


def test_promotional_price_is_compared_by_value_not_exponent() -> None:
    assert rejection(lambda: new_product(price=D("10.5"), promo_price=D("10.500"))) == (
        "promo_price",
        "not_below_price",
    )


# --- Decimal context independence ------------------------------------------------------------------------------

CONTEXTS = {
    "tiny_precision": decimal.Context(prec=3),
    "round_up": decimal.Context(rounding=decimal.ROUND_UP),
    "round_floor": decimal.Context(rounding=decimal.ROUND_FLOOR),
    "all_traps": decimal.Context(prec=2, traps=[decimal.Inexact, decimal.Rounded, decimal.InvalidOperation]),
    "narrow_exponents": decimal.Context(Emax=5, Emin=-5, traps=[decimal.Overflow, decimal.Underflow]),
}


@pytest.fixture(params=sorted(CONTEXTS))
def restricted_context(request: pytest.FixtureRequest) -> decimal.Context:
    return CONTEXTS[request.param]


def test_price_validation_and_canonicalisation_do_not_depend_on_the_decimal_context(
    restricted_context: decimal.Context,
) -> None:
    prices = [D(text) for text in VALID_PRICES] + [D(text) for text, _ in INVALID_PRICES]

    def outcome(price: Decimal) -> object:
        try:
            product = new_product(price=price, promo_price=None)
        except InvalidProduct as error:
            return (error.field, error.code)
        return product.price.as_tuple()

    expected = [outcome(price) for price in prices]  # default context
    with decimal.localcontext(restricted_context) as context:
        before = context.copy()
        actual = [outcome(price) for price in prices]
        for price in prices:  # the direct constructor too
            try:
                _construct(price=price, promo_price=None)
            except InvalidProduct:
                pass
        assert context.prec == before.prec and context.rounding == before.rounding
        assert context.flags == before.flags  # no signal was raised and recorded
        assert context.traps == before.traps

    assert actual == expected


def test_ten_point_zero_zero_five_stays_rejected_under_every_rounding_mode() -> None:
    for rounding in (
        decimal.ROUND_UP,
        decimal.ROUND_DOWN,
        decimal.ROUND_CEILING,
        decimal.ROUND_FLOOR,
        decimal.ROUND_HALF_UP,
        decimal.ROUND_HALF_DOWN,
        decimal.ROUND_HALF_EVEN,
        decimal.ROUND_05UP,
    ):
        with decimal.localcontext(decimal.Context(rounding=rounding)):
            assert rejection(lambda: new_product(price=D("10.005"), promo_price=None)) == ("price", "too_precise")
            assert rejection(lambda: new_product(price=D("0.001"), promo_price=None)) == ("price", "too_precise")


# --- Name and description -----------------------------------------------------------------------------------------


def test_factory_trims_name_and_description() -> None:
    product = new_product(name="  Bicicleta  ", description="\t texto \n")
    assert (product.name, product.description) == ("Bicicleta", "texto")


def test_description_may_be_empty() -> None:
    assert new_product(description="   ").description == ""
    assert _construct(description="").description == ""


@pytest.mark.parametrize("name", ["", "   ", "\n\t"])
def test_factory_rejects_blank_names(name: str) -> None:
    assert rejection(lambda: new_product(name=name)) == ("name", "required")


def test_name_length_limit_is_200_code_points() -> None:
    assert len(new_product(name="a" * 200).name) == 200
    assert rejection(lambda: new_product(name="a" * 201)) == ("name", "too_long")
    assert len(new_product(name="ç" * 200).name) == 200  # code points, not bytes
    assert rejection(lambda: new_product(name="ç" * 201)) == ("name", "too_long")


def test_name_length_is_measured_after_trimming() -> None:
    assert len(new_product(name=" " + "a" * 200 + " ").name) == 200


@pytest.mark.parametrize("value", [None, 1, b"x", ["a"]])
def test_non_string_name_and_description_are_rejected_by_factory_and_constructor(value: object) -> None:
    assert rejection(lambda: new_product(name=value)) == ("name", "invalid_type")
    assert rejection(lambda: new_product(description=value)) == ("description", "invalid_type")
    assert rejection(lambda: _construct(name=value)) == ("name", "invalid_type")
    assert rejection(lambda: _construct(description=value)) == ("description", "invalid_type")


@PATHS
@pytest.mark.parametrize("name", [" padded", "padded ", "\tpadded"])
def test_constructor_rejects_untrimmed_names(build: object, name: str) -> None:
    assert rejection(lambda: build(name=name)) == ("name", "not_normalized")  # type: ignore[operator]


@PATHS
@pytest.mark.parametrize("name", ["", "a" * 201])
def test_constructor_rejects_empty_and_overlong_names(build: object, name: str) -> None:
    code = "required" if name == "" else "too_long"
    assert rejection(lambda: build(name=name)) == ("name", code)  # type: ignore[operator]


@pytest.mark.parametrize("description", [" x", "x ", "\n"])
def test_constructor_rejects_untrimmed_descriptions(description: str) -> None:
    assert rejection(lambda: _construct(description=description)) == ("description", "not_normalized")


# --- Name and slug derivability -----------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["!!!", "---", "???", "ß", "日本語", "😀", "·"])
def test_factory_rejects_names_without_a_derivable_slug(name: str) -> None:
    assert rejection(lambda: new_product(name=name)) == ("name", "slug_not_derivable")


@PATHS
def test_constructor_rejects_a_non_derivable_name_even_with_a_valid_slug(build: object) -> None:
    assert rejection(lambda: build(name="!!!", slug="valid-slug")) == ("name", "slug_not_derivable")  # type: ignore[operator]


def test_replace_rejects_renaming_to_a_non_derivable_name() -> None:
    with pytest.raises(InvalidProduct) as raised:
        dataclasses.replace(a_product(), name="!!!")
    assert (raised.value.field, raised.value.code) == ("name", "slug_not_derivable")


def test_constructor_accepts_a_slug_that_differs_from_the_derived_one() -> None:
    product = _construct(name="Bicicleta Nova", slug="outro-slug")
    assert (product.name, product.slug) == ("Bicicleta Nova", "outro-slug")


# --- Slugs --------------------------------------------------------------------------------------------------------

SLUG_DERIVATIONS = [
    ("Bicicleta de Estrada", "bicicleta-de-estrada"),
    ("Ação", "acao"),
    ("Capacete Preto nº 3", "capacete-preto-no-3"),  # NFKD turns º into o
    ("Pneu 700x25c (par)", "pneu-700x25c-par"),
    ("  --Câmara-de-ar!!  ", "camara-de-ar"),
    ("a   b---c", "a-b-c"),
    ("12345", "12345"),
    ("ÁÉÍÓÚ àèìòù âêô ãõ ç", "aeiou-aeiou-aeo-ao-c"),
    ("Ⅳ ﬁnal", "iv-final"),  # compatibility decomposition, then lowercase
    ("İstanbul", "istanbul"),
    ("Straße", "stra-e"),  # known limitation: letters without an ASCII decomposition are separators
    ("Søren", "s-ren"),
    ("!!!", ""),
    ("", ""),
]


@pytest.mark.parametrize(("name", "slug"), SLUG_DERIVATIONS)
def test_slug_derivation(name: str, slug: str) -> None:
    assert slug_from_name(name) == slug


def test_slug_is_truncated_to_160_without_a_trailing_hyphen() -> None:
    assert slug_from_name("a" * 200) == "a" * 160
    name = "a" * 159 + " " + "b" * 40  # the cut falls right after the hyphen
    assert slug_from_name(name) == "a" * 159
    assert slug_from_name("x" * 160) == "x" * 160


def test_factory_derives_the_slug_from_the_trimmed_name() -> None:
    assert new_product(name="  Câmara de Ar  ").slug == "camara-de-ar"
    assert len(new_product(name="a" * 200).slug) == 160


def test_slug_candidates_follow_the_collision_sequence() -> None:
    assert list(slug_candidates("x", 3)) == ["x", "x-2", "x-3"]
    assert list(slug_candidates("x", 1)) == ["x"]
    assert list(slug_candidates("x", 0)) == []


def test_slug_candidates_fit_in_160_characters() -> None:
    base = "a" * 160
    candidates = list(slug_candidates(base, 3))
    assert candidates == [base, "a" * 158 + "-2", "a" * 158 + "-3"]
    assert all(len(candidate) <= 160 for candidate in candidates)


def test_truncated_candidates_never_end_a_stem_with_a_hyphen() -> None:
    base = "a" * 157 + "-bc"  # 160 characters; the cut for "-2" leaves a trailing hyphen to strip
    candidates = list(slug_candidates(base, 3))
    assert candidates[1] == "a" * 157 + "-2"
    assert "--" not in "".join(candidates)


@pytest.mark.parametrize("name", [n for n, s in SLUG_DERIVATIONS if s])
def test_every_derived_slug_and_candidate_is_a_valid_slug(name: str) -> None:
    for candidate in slug_candidates(slug_from_name(name), 3):
        assert a_product().with_slug(candidate).slug == candidate


@PATHS
@pytest.mark.parametrize(
    "slug",
    ["", "Upper", "with space", "under_score", "-lead", "trail-", "dou--ble", "acentuação", "a/b", "a.b", "a\n", "x\n"],
)
def test_constructor_rejects_invalid_slugs(build: object, slug: str) -> None:
    assert rejection(lambda: build(slug=slug)) == ("slug", "invalid")  # type: ignore[operator]


def test_constructor_enforces_the_slug_length_limit() -> None:
    assert a_product(slug="a" * 160).slug == "a" * 160
    assert rejection(lambda: a_product(slug="a" * 161)) == ("slug", "too_long")
    assert rejection(lambda: a_product(slug=None)) == ("slug", "invalid")


# --- Reference ids ------------------------------------------------------------------------------------------------

BAD_IDS = [0, -1, True, False, "1", 1.0, 1.5, D(1), b"1", [1]]


@PATHS
@pytest.mark.parametrize("value", BAD_IDS)
def test_constructor_rejects_invalid_category_and_brand_ids(build: object, value: object) -> None:
    assert rejection(lambda: build(category_id=value)) == ("category_id", "invalid")  # type: ignore[operator]
    assert rejection(lambda: build(brand_id=value)) == ("brand_id", "invalid")  # type: ignore[operator]


@PATHS
def test_category_is_required_and_brand_is_optional(build: object) -> None:
    assert rejection(lambda: build(category_id=None)) == ("category_id", "required")  # type: ignore[operator]
    assert build(brand_id=None).brand_id is None  # type: ignore[operator]


@pytest.mark.parametrize("value", BAD_IDS)
def test_factory_rejects_invalid_reference_ids(value: object) -> None:
    assert rejection(lambda: new_product(category_id=value)) == ("category_id", "invalid")
    assert rejection(lambda: new_product(brand_id=value)) == ("brand_id", "invalid")


def test_factory_requires_a_category_and_allows_no_brand() -> None:
    assert rejection(lambda: new_product(category_id=None)) == ("category_id", "required")
    assert new_product(brand_id=None).brand_id is None


@PATHS
@pytest.mark.parametrize("value", [0, -1, True, "1", 1.0])
def test_constructor_rejects_invalid_product_ids(build: object, value: object) -> None:
    assert rejection(lambda: build(id=value)) == ("id", "invalid")  # type: ignore[operator]


def test_product_id_may_be_none_or_a_positive_integer() -> None:
    assert a_product(id=None).id is None
    assert a_product(id=ProductId(7)).id == 7


# --- Entity behaviour ---------------------------------------------------------------------------------------------


def test_product_is_immutable() -> None:
    product = a_product()
    with pytest.raises(dataclasses.FrozenInstanceError):
        product.name = "other"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        product.price = D("1")  # type: ignore[misc]


def test_factory_builds_a_product_without_an_id() -> None:
    assert new_product().id is None


def test_with_slug_returns_a_copy_and_keeps_other_fields() -> None:
    product = a_product()
    copy = product.with_slug("outro")
    assert copy.slug == "outro" and product.slug == "bicicleta-de-estrada"
    assert dataclasses.replace(copy, slug=product.slug) == product


def test_first_violation_is_reported_in_field_declaration_order() -> None:
    assert rejection(lambda: _construct(name="", price=D("-1"))) == ("name", "required")
    assert rejection(lambda: _construct(category_id=0, price=D("-1"))) == ("category_id", "invalid")
