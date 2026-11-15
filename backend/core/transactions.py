"""Transaction port: the use case owns the transaction (ADR-0004)."""

from contextlib import AbstractContextManager
from typing import Protocol


class Atomic(Protocol):
    """Opens one transaction scope; leaving it with an exception rolls it back.

    Django's `transaction.atomic` satisfies this structurally, so no adapter and no Django import is needed here.
    """

    def __call__(self) -> AbstractContextManager[object]: ...
