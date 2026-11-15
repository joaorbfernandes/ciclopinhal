"""In-memory transaction fake. It records scope boundaries and exceptions; it cannot roll back (proved in M2)."""

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager


class RecordingAtomic:
    """An `Atomic` that appends "begin", "end" or "end:error" to a journal it may share with other fakes."""

    def __init__(self, journal: list[str] | None = None) -> None:
        self.journal: list[str] = journal if journal is not None else []
        self.exceptions: list[BaseException] = []

    def __call__(self) -> AbstractContextManager[None]:
        return self._scope()

    @contextmanager
    def _scope(self) -> Iterator[None]:
        self.journal.append("begin")
        try:
            yield
        except BaseException as exc:
            self.exceptions.append(exc)
            self.journal.append("end:error")
            raise
        self.journal.append("end")
