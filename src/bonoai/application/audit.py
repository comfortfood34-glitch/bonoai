"""Data quality audit and reconciliation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from bonoai.domain.data import CanonicalDrawRecord, SourceConflictError


@dataclass(frozen=True)
class ConflictRecord:
    """Record of a data conflict between sources."""

    contest_id: str
    official_numbers: tuple[int, ...] | None
    auxiliary_numbers: tuple[int, ...] | None
    official_source: str | None
    auxiliary_source: str | None

    def to_dict(self) -> dict[str, object]:
        """Serialize conflict to dictionary."""
        return {
            "contest_id": self.contest_id,
            "official_numbers": list(self.official_numbers) if self.official_numbers else None,
            "auxiliary_numbers": list(self.auxiliary_numbers) if self.auxiliary_numbers else None,
            "official_source": self.official_source,
            "auxiliary_source": self.auxiliary_source,
        }


@dataclass(frozen=True)
class DataAudit:
    """Results of reconciling multiple data sources."""

    total_official: int = 0
    total_auxiliary: int = 0
    total_manual: int = 0
    conflicts: list[ConflictRecord] = field(default_factory=list)
    duplicates_ignored: int = 0
    merged_records: tuple[CanonicalDrawRecord, ...] = ()

    def has_conflicts(self) -> bool:
        """Check if reconciliation found any conflicting records."""
        return len(self.conflicts) > 0

    def to_dict(self) -> dict[str, int | list[dict[str, object]]]:
        """Serialize audit results to dictionary."""
        return {
            "total_official": self.total_official,
            "total_auxiliary": self.total_auxiliary,
            "total_manual": self.total_manual,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "duplicates_ignored": self.duplicates_ignored,
            "merged_count": len(self.merged_records),
        }


def reconcile_sources(
    official: Iterable[CanonicalDrawRecord],
    auxiliary: Iterable[CanonicalDrawRecord] | None = None,
) -> DataAudit:
    """Reconcile official and auxiliary data sources.

    Returns DataAudit with merged records or raises SourceConflictError if
    the same contest_id has different number combinations.

    Args:
        official: Canonical records from official source (SELAE).
        auxiliary: Optional records from auxiliary sources (historical).

    Returns:
        DataAudit with reconciliation results.

    Raises:
        SourceConflictError: If contest_id has conflicting results.
    """
    official_records = tuple(official)
    auxiliary_records = tuple(auxiliary) if auxiliary else ()

    official_by_id: dict[str, CanonicalDrawRecord] = {}
    for record in official_records:
        official_by_id[record.draw.contest_id] = record

    conflicts: list[ConflictRecord] = []
    auxiliary_by_id: dict[str, CanonicalDrawRecord] = {}
    duplicates = 0

    for aux_record in auxiliary_records:
        contest_id = aux_record.draw.contest_id
        if contest_id in official_by_id:
            official_record = official_by_id[contest_id]
            if official_record.draw.numbers != aux_record.draw.numbers:
                conflicts.append(
                    ConflictRecord(
                        contest_id=contest_id,
                        official_numbers=official_record.draw.numbers,
                        auxiliary_numbers=aux_record.draw.numbers,
                        official_source=official_record.provenance.source_name,
                        auxiliary_source=aux_record.provenance.source_name,
                    )
                )
            else:
                duplicates += 1
        else:
            if contest_id not in auxiliary_by_id:
                auxiliary_by_id[contest_id] = aux_record
            else:
                if auxiliary_by_id[contest_id].draw.numbers == aux_record.draw.numbers:
                    duplicates += 1
                else:
                    conflicts.append(
                        ConflictRecord(
                            contest_id=contest_id,
                            official_numbers=None,
                            auxiliary_numbers=aux_record.draw.numbers,
                            official_source=None,
                            auxiliary_source=aux_record.provenance.source_name,
                        )
                    )

    if conflicts:
        conflict_ids = [c.contest_id for c in conflicts]
        raise SourceConflictError(
            f"Found {len(conflicts)} conflicting result(s): {', '.join(conflict_ids)}"
        )

    merged = list(official_records)
    merged.extend(auxiliary_by_id.values())
    merged_sorted = tuple(sorted(merged, key=lambda r: r.draw.held_on))

    return DataAudit(
        total_official=len(official_records),
        total_auxiliary=len(auxiliary_records),
        conflicts=conflicts,
        duplicates_ignored=duplicates,
        merged_records=merged_sorted,
    )
