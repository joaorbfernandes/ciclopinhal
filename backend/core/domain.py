"""Shared domain errors. Pure Python: no Django, no I/O."""


class DomainError(Exception):
    """Base class of every error raised by domain and application code."""


class ReferenceNotFound(DomainError):
    """A referenced entity (for example a category or a brand) does not exist."""

    def __init__(self, reference: str, id: int) -> None:
        super().__init__(f"{reference} {id} not found")
        self.reference = reference
        self.id = id
