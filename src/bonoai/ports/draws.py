"""Ports for draw acquisition and persistence."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from bonoai.domain.models import Draw


class DrawSource(Protocol):
    """External source capable of returning newly available draws."""

    def fetch_after(self, held_after: date | None) -> Sequence[Draw]:
        """Fetch draws after the supplied date without mutating storage."""
        ...


class DrawRepository(Protocol):
    """Validated canonical draw storage."""

    def list_all(self) -> Sequence[Draw]:
        """Return canonical draws in chronological order."""
        ...

    def append_validated(self, draws: Sequence[Draw]) -> None:
        """Atomically append a conflict-free batch."""
        ...
