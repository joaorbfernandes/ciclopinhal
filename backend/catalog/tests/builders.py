"""Plain builder functions for catalog tests (engineering §9)."""

from decimal import Decimal
from typing import Any

from backend.catalog.application import CreateProductCommand
from backend.catalog.domain import BrandId, CategoryId, Product


def a_product(**overrides: Any) -> Product:
    """A valid product without an id, built by direct construction; override any field."""
    fields: dict[str, Any] = {
        "id": None,
        "name": "Bicicleta de Estrada",
        "slug": "bicicleta-de-estrada",
        "description": "Quadro em alumínio.",
        "category_id": CategoryId(1),
        "brand_id": BrandId(1),
        "price": Decimal("199.90"),
        "promo_price": Decimal("149.90"),
    }
    fields.update(overrides)
    return Product(**fields)


def a_command(**overrides: Any) -> CreateProductCommand:
    """A valid CreateProductCommand; override any field."""
    fields: dict[str, Any] = {
        "name": "Bicicleta de Estrada",
        "description": "Quadro em alumínio.",
        "category_id": CategoryId(1),
        "brand_id": BrandId(1),
        "price": Decimal("199.90"),
        "promo_price": Decimal("149.90"),
    }
    fields.update(overrides)
    return CreateProductCommand(**fields)
