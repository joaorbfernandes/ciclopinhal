"""Catalog domain: the Product entity, its invariants, the factory and the slug policy (SPEC-002).

Pure Python: no Django, no I/O. Every rule lives in `Product.__post_init__`, so it holds on every construction path
(the factory, direct construction, `dataclasses.replace`, repository storage and rehydration, ADR-0016). The factory
only normalises input before constructing.

Price checks use exact Decimal inspection (`as_tuple`, comparisons, tuple construction) and never arithmetic, so the
result does not depend on the caller's decimal context (precision, rounding mode, traps).
"""

import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import NewType

from backend.core.api import DomainError

ProductId = NewType("ProductId", int)
CategoryId = NewType("CategoryId", int)
BrandId = NewType("BrandId", int)

NAME_MAX = 200
SLUG_MAX = 160
PRICE_PLACES = 2
PRICE_MAX = Decimal("99999999.99")

_SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


class InvalidProduct(DomainError):
    """An invariant is broken. `field` and `code` are stable identifiers, not user-facing text."""

    def __init__(self, field: str, code: str) -> None:
        super().__init__(f"{field}: {code}")
        self.field = field
        self.code = code


# --- Slug policy (D12) ------------------------------------------------------------------------------------------


def slug_from_name(name: str) -> str:
    """Derive a slug: NFKD, drop accents, lowercase, runs of other characters become one hyphen. `""` if none."""
    decomposed = unicodedata.normalize("NFKD", name)
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char)).lower()
    slug = _NON_SLUG_RUN.sub("-", unaccented).strip("-")
    return slug[:SLUG_MAX].rstrip("-")


def slug_candidates(base: str, attempts: int) -> Iterator[str]:
    """`base`, then `base-2`, `base-3`, ...; every candidate fits in SLUG_MAX characters."""
    if attempts < 1:
        return
    yield base
    for number in range(2, attempts + 1):
        suffix = f"-{number}"
        yield base[: SLUG_MAX - len(suffix)].rstrip("-") + suffix


# --- Field checks (shared by the constructor and the factory) ---------------------------------------------------


def _check_id(value: object, field: str, *, required: bool) -> None:
    if value is None:
        if required:
            raise InvalidProduct(field, "required")
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidProduct(field, "invalid")


def _check_name(name: object) -> None:
    if not isinstance(name, str):
        raise InvalidProduct("name", "invalid_type")
    if name != name.strip():
        raise InvalidProduct("name", "not_normalized")
    if not name:
        raise InvalidProduct("name", "required")
    if len(name) > NAME_MAX:
        raise InvalidProduct("name", "too_long")
    if not slug_from_name(name):
        raise InvalidProduct("name", "slug_not_derivable")


def _check_slug(slug: object) -> None:
    if not isinstance(slug, str):
        raise InvalidProduct("slug", "invalid")
    if len(slug) > SLUG_MAX:
        raise InvalidProduct("slug", "too_long")
    if _SLUG_PATTERN.fullmatch(slug) is None:
        raise InvalidProduct("slug", "invalid")


def _check_description(description: object) -> None:
    if not isinstance(description, str):
        raise InvalidProduct("description", "invalid_type")
    if description != description.strip():
        raise InvalidProduct("description", "not_normalized")


def _price_problem(value: object) -> str | None:
    """The code of the first rule `value` breaks as a price, or None. Exact and context-independent."""
    if not isinstance(value, Decimal):
        return "invalid_type"
    if not value.is_finite():
        return "not_finite"
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):  # unreachable for a finite value; narrows the type
        return "not_finite"
    if sign or value.is_zero():
        return "not_positive"
    if value > PRICE_MAX:
        return "too_large"
    if exponent < 0:
        text = "".join(map(str, digits))
        trailing_zeros = len(text) - len(text.rstrip("0"))
        if exponent + trailing_zeros < -PRICE_PLACES:
            return "too_precise"
    return None


def _check_price(value: object, field: str) -> None:
    problem = _price_problem(value)
    if problem is not None:
        raise InvalidProduct(field, problem)


def _canonical_price(value: Decimal) -> Decimal:
    """The same numeric value with exponent -2. Only called for a value that passed `_price_problem`."""
    _, digits, exponent = value.as_tuple()
    assert isinstance(exponent, int)
    # Work on the digit tuple, never on an int: a valid price may carry thousands of trailing zeros, and Python limits
    # integer-string conversion. Dropping digits is exact because `_price_problem` guarantees they are zeros.
    shift = exponent + PRICE_PLACES
    return Decimal((0, digits + (0,) * shift if shift >= 0 else digits[:shift], -PRICE_PLACES))


def _normalised_price(value: Decimal) -> Decimal:
    """Lossless canonicalisation; a value that is not a valid price is returned untouched, for the constructor."""
    if _price_problem(value) is None:
        return _canonical_price(value)
    return value


# --- Entity -----------------------------------------------------------------------------------------------------


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

    def __post_init__(self) -> None:
        _check_id(self.id, "id", required=False)
        _check_name(self.name)
        _check_slug(self.slug)
        _check_description(self.description)
        _check_id(self.category_id, "category_id", required=True)
        _check_id(self.brand_id, "brand_id", required=False)
        _check_price(self.price, "price")
        if self.promo_price is not None:
            _check_price(self.promo_price, "promo_price")
            if self.promo_price >= self.price:
                raise InvalidProduct("promo_price", "not_below_price")

    @classmethod
    def new(
        cls,
        *,
        name: str,
        description: str,
        category_id: CategoryId,
        brand_id: BrandId | None,
        price: Decimal,
        promo_price: Decimal | None,
    ) -> "Product":
        """Normalise input (trim, derive the slug, canonicalise prices losslessly) and construct a new product."""
        if not isinstance(name, str):
            raise InvalidProduct("name", "invalid_type")
        if not isinstance(description, str):
            raise InvalidProduct("description", "invalid_type")
        name = name.strip()
        description = description.strip()
        _check_name(name)  # required, too_long, slug_not_derivable, before deriving the slug
        return cls(
            id=None,
            name=name,
            slug=slug_from_name(name),
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            price=_normalised_price(price),
            promo_price=None if promo_price is None else _normalised_price(promo_price),
        )

    def with_slug(self, slug: str) -> "Product":
        """A copy with another slug; the constructor runs again."""
        return replace(self, slug=slug)
