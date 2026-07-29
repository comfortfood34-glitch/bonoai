"""Ports for immutable source documents and canonical draw storage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from bonoai.domain.data import CanonicalDrawRecord


@dataclass(frozen=True, slots=True)
class FetchedDocument:
    """Raw bytes and retrieval metadata before parsing."""

    source_name: str
    source_url: str
    retrieved_at_utc: datetime
    payload: bytes
    media_type: str


@dataclass(frozen=True, slots=True)
class DrawBatch:
    """One immutable external document and every record parsed from it."""

    document: FetchedDocument
    records: tuple[CanonicalDrawRecord, ...]


@dataclass(frozen=True, slots=True)
class AppendResult:
    """Result of one atomic canonical repository update."""

    inserted: int
    duplicates: int
    total: int


class DrawSource(Protocol):
    """External source that returns a fully validated batch."""

    def fetch(self) -> DrawBatch:
        """Fetch and parse one immutable source document."""
        ...


class RawDocumentArchive(Protocol):
    """Append-only archive for exact external payloads."""

    def store(self, document: FetchedDocument) -> Path:
        """Persist exact bytes and a provenance manifest."""
        ...


class DrawRepository(Protocol):
    """Validated canonical draw storage."""

    def list_all(self) -> Sequence[CanonicalDrawRecord]:
        """Return canonical records in chronological order."""
        ...

    def append_validated(self, records: Sequence[CanonicalDrawRecord]) -> AppendResult:
        """Atomically append a conflict-free batch."""
        ...
