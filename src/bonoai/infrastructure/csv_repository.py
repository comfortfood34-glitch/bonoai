"""Atomic CSV implementation of the canonical draw repository."""

from __future__ import annotations

import csv
import os
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Final

from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    ReconciliationResult,
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.infrastructure.migrations import migrate_v1_to_v2
from bonoai.ports.data import AppendResult

CANONICAL_COLUMNS: Final = (
    "contest_id",
    "held_on",
    "n1",
    "n2",
    "n3",
    "n4",
    "n5",
    "n6",
    "complementary",
    "reintegro",
    "source_name",
    "source_url",
    "retrieved_at_utc",
    "source_sha256",
    "source_type",
    "schema_version",
)


def _record_to_rows(record: CanonicalDrawRecord) -> list[dict[str, str]]:
    """Expand record into multiple CSV rows (one per provenance)."""
    draw = record.draw
    rows = []
    for provenance in record.provenances:
        row = {
            "contest_id": draw.contest_id,
            "held_on": draw.held_on.isoformat(),
            "complementary": str(draw.complementary),
            "reintegro": str(draw.reintegro),
            "source_name": provenance.source_name,
            "source_url": provenance.source_url,
            "retrieved_at_utc": provenance.retrieved_at_utc.isoformat(),
            "source_sha256": provenance.source_sha256,
            "source_type": provenance.source_type,
            "schema_version": str(provenance.schema_version),
        }
        row.update({f"n{index}": str(number) for index, number in enumerate(draw.numbers, start=1)})
        rows.append(row)
    return rows


def _row_to_draw_and_provenance(
    row: dict[str, str], line_number: int
) -> tuple[Draw, SourceProvenance]:
    """Parse CSV row into Draw and SourceProvenance.

    Fail-closed: source_type is mandatory, no defaults.
    """
    try:
        complementary_str = row["complementary"].strip()
        reintegro_str = row["reintegro"].strip()
        if not complementary_str or not reintegro_str:
            raise ValueError("complementary and reintegro must not be empty")
        draw = Draw(
            contest_id=row["contest_id"],
            held_on=datetime.strptime(row["held_on"], "%Y-%m-%d").date(),
            numbers=tuple(int(row[f"n{index}"]) for index in range(1, 7)),
            complementary=int(complementary_str),
            reintegro=int(reintegro_str),
        )
        source_type_str = row["source_type"].strip()
        if not source_type_str:
            raise ValueError("source_type must not be empty")
        if source_type_str not in {"official", "auxiliary", "manual"}:
            raise ValueError(f"invalid source_type: {source_type_str}")
        provenance = SourceProvenance(
            source_name=row["source_name"],
            source_url=row["source_url"],
            retrieved_at_utc=datetime.fromisoformat(row["retrieved_at_utc"]),
            source_sha256=row["source_sha256"],
            source_type=source_type_str,  # type: ignore
            schema_version=int(row["schema_version"]),
        )
    except KeyError as error:
        raise DataContractError(
            f"invalid canonical CSV row at line {line_number}: missing field {error}"
        ) from error
    except (TypeError, ValueError) as error:
        raise DataContractError(f"invalid canonical CSV row at line {line_number}") from error
    return draw, provenance


def _rows_to_records(rows: list[dict[str, str]]) -> tuple[CanonicalDrawRecord, ...]:
    """Group rows by contest_id into CanonicalDrawRecord with multiple provenances.

    Ensures all rows for same contest_id have identical Draw data.
    Rejects duplicate provenances for the same contest.
    """
    by_contest: dict[str, tuple[Draw, list[SourceProvenance], set[tuple[str, str, str, str]]]] = {}

    for line_number, row in enumerate(rows, start=2):
        draw, provenance = _row_to_draw_and_provenance(row, line_number)
        contest_id = draw.contest_id

        if contest_id not in by_contest:
            by_contest[contest_id] = (draw, [provenance], {provenance.fingerprint()})
        else:
            existing_draw, provenances, fingerprints = by_contest[contest_id]
            if existing_draw != draw:
                raise DataContractError(
                    f"canonical CSV has conflicting draws for {contest_id}: "
                    f"line {line_number} differs from earlier row"
                )
            fp = provenance.fingerprint()
            if fp in fingerprints:
                raise DataContractError(
                    f"canonical CSV has duplicate provenance for {contest_id} at line {line_number}"
                )
            provenances.append(provenance)
            fingerprints.add(fp)

    records = tuple(
        CanonicalDrawRecord(
            draw=draw,
            provenances=tuple(
                sorted(provenances, key=lambda p: p.fingerprint())
            ),
        )
        for draw, provenances, _ in by_contest.values()
    )
    return records


def reconcile_records(
    existing: Iterable[CanonicalDrawRecord],
    incoming: Iterable[CanonicalDrawRecord],
) -> ReconciliationResult:
    """Return sorted union with metrics."""
    by_contest: dict[str, CanonicalDrawRecord] = {}
    for record in existing:
        previous = by_contest.get(record.draw.contest_id)
        if previous is not None and previous.draw != record.draw:
            raise SourceConflictError(
                f"canonical storage already conflicts for {record.draw.contest_id}"
            )
        by_contest[record.draw.contest_id] = record

    inserted_draws = 0
    duplicate_provenances = 0
    added_provenances = 0

    for record in incoming:
        previous = by_contest.get(record.draw.contest_id)
        if previous is None:
            by_contest[record.draw.contest_id] = record
            inserted_draws += 1
        elif previous.draw == record.draw:
            existing_fingerprints = {prov.fingerprint() for prov in previous.provenances}
            new_provenances = []
            for prov in record.provenances:
                if prov.fingerprint() not in existing_fingerprints:
                    new_provenances.append(prov)
                    added_provenances += 1
                else:
                    duplicate_provenances += 1

            if new_provenances:
                merged_provenances = tuple(
                    sorted(
                        (*previous.provenances, *new_provenances),
                        key=lambda p: p.fingerprint(),
                    )
                )
                by_contest[record.draw.contest_id] = CanonicalDrawRecord(
                    draw=previous.draw,
                    provenances=merged_provenances,
                )
        else:
            raise SourceConflictError(
                f"conflicting result for {record.draw.contest_id}: "
                f"existing={previous.draw.numbers}, incoming={record.draw.numbers}"
            )

    ordered = tuple(
        sorted(
            by_contest.values(),
            key=lambda record: (record.draw.held_on, record.draw.contest_id),
        )
    )
    return ReconciliationResult(
        records=ordered,
        inserted_draws=inserted_draws,
        added_provenances=added_provenances,
        duplicate_provenances=duplicate_provenances,
    )


class CsvDrawRepository:
    """Canonical CSV with validate-first and atomic-replace writes."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def migrate_schema(self) -> None:
        """Explicitly migrate v1 CSV schema to v2. Atomic, idempotent, deterministic."""
        migrate_v1_to_v2(self._path)

    def list_all(self) -> tuple[CanonicalDrawRecord, ...]:
        if not self._path.exists():
            return ()

        with self._path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fieldnames = tuple(reader.fieldnames or ())
            if fieldnames != CANONICAL_COLUMNS:
                raise DataContractError("canonical CSV header does not match schema v2")
            rows = list(reader)

        records = _rows_to_records([dict(row) for row in rows])
        result = reconcile_records((), records)
        if result.inserted_draws != len(records) or result.duplicate_provenances:
            raise DataContractError("canonical CSV contains duplicate contest identifiers")
        return result.records

    def append_validated(
        self,
        records: Sequence[CanonicalDrawRecord],
    ) -> AppendResult:
        current = self.list_all()
        result = reconcile_records(current, records)
        if result.inserted_draws == 0 and result.added_provenances == 0:
            return AppendResult(
                inserted_draws=0,
                added_provenances=0,
                duplicate_provenances=result.duplicate_provenances,
                total=len(result.records),
            )

        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                all_rows = []
                for record in result.records:
                    all_rows.extend(_record_to_rows(record))
                writer.writerows(all_rows)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self._path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return AppendResult(
            inserted_draws=result.inserted_draws,
            added_provenances=result.added_provenances,
            duplicate_provenances=result.duplicate_provenances,
            total=len(result.records),
        )
