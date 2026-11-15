"""Public surface of `core`: other modules import only from here (ADR-0002)."""

from backend.core.domain import DomainError, ReferenceNotFound
from backend.core.transactions import Atomic

__all__ = ["Atomic", "DomainError", "ReferenceNotFound"]
