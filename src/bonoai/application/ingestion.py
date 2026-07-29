"""Atomic draw-ingestion use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from bonoai.ports.data import DrawRepository, DrawSource, RawDocumentArchive


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """Observable result of one source update."""

    fetched: int
    inserted: int
    duplicates: int
    total: int
    latest_draw: date | None
    raw_archive_path: Path

    def as_dict(self) -> dict[str, object]:
        return {
            "fetched": self.fetched,
            "inserted": self.inserted,
            "duplicates": self.duplicates,
            "total": self.total,
            "latest_draw": self.latest_draw.isoformat() if self.latest_draw else None,
            "raw_archive_path": str(self.raw_archive_path),
        }


def ingest_draws(
    *,
    source: DrawSource,
    repository: DrawRepository,
    raw_archive: RawDocumentArchive,
) -> IngestionReport:
    """Archive one source payload, then atomically reconcile canonical records."""
    batch = source.fetch()
    raw_path = raw_archive.store(batch.document)
    result = repository.append_validated(batch.records)
    records = repository.list_all()
    latest = records[-1].draw.held_on if records else None
    return IngestionReport(
        fetched=len(batch.records),
        inserted=result.inserted,
        duplicates=result.duplicates,
        total=result.total,
        latest_draw=latest,
        raw_archive_path=raw_path,
    )
