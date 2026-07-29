"""Ports for historical data sources."""

from __future__ import annotations

from typing import Protocol

from bonoai.domain.data import CanonicalDrawRecord


class HistoricalSource(Protocol):
    """Contract for loading historical Bonoloto data."""

    def load(self) -> tuple[CanonicalDrawRecord, ...]:
        """Load and validate historical records.

        Returns tuple of validated draw records sorted by held_on date.
        Raises DataContractError if records are invalid or incomplete.
        """
        ...
