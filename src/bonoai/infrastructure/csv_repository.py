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
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
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
    "schema_version",
)


def _record_to_row(record: CanonicalDrawRecord) -> dict[str, str]:
    draw = record.draw
    provenance = record.provenance
    row = {
        "contest_id": draw.contest_id,
        "held_on": draw.held_on.isoformat(),
        "complementary": str(draw.complementary),
        "reintegro": str(draw.reintegro),
        "source_name": provenance.source_name,
        "source_url": provenance.source_url,
        "retrieved_at_utc": provenance.retrieved_at_utc.isoformat(),
        "source_sha256": provenance.source_sha256,
        "schema_version": str(provenance.schema_version),
    }
    row.update({f"n{index}": str(number) for index, number in enumerate(draw.numbers, start=1)})
    return row


def _row_to_record(row: dict[str, str], line_number: int) -> CanonicalDrawRecord:
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
        provenance = SourceProvenance(
            source_name=row["source_name"],
            source_url=row["source_url"],
            retrieved_at_utc=datetime.fromisoformat(row["retrieved_at_utc"]),
            source_sha256=row["source_sha256"],
            schema_version=int(row["schema_version"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise DataContractError(f"invalid canonical CSV row at line {line_number}") from error
    return CanonicalDrawRecord(draw=draw, provenance=provenance)


def reconcile_records(
    existing: Iterable[CanonicalDrawRecord],
    incoming: Iterable[CanonicalDrawRecord],
) -> tuple[tuple[CanonicalDrawRecord, ...], int, int]:
    """Return a sorted union or raise before any storage mutation."""
    by_contest: dict[str, CanonicalDrawRecord] = {}
    for record in existing:
        previous = by_contest.get(record.draw.contest_id)
        if previous is not None and previous.draw != record.draw:
            raise SourceConflictError(
                f"canonical storage already conflicts for {record.draw.contest_id}"
            )
        by_contest[record.draw.contest_id] = record

    inserted = 0
    duplicates = 0
    for record in incoming:
        previous = by_contest.get(record.draw.contest_id)
        if previous is None:
            by_contest[record.draw.contest_id] = record
            inserted += 1
        elif previous.draw == record.draw:
            duplicates += 1
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
    return ordered, inserted, duplicates


class CsvDrawRepository:
    """Canonical CSV with validate-first and atomic-replace writes."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def list_all(self) -> tuple[CanonicalDrawRecord, ...]:
        if not self._path.exists():
            return ()
        with self._path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != CANONICAL_COLUMNS:
                raise DataContractError("canonical CSV header does not match schema version 1")
            records = tuple(
                _row_to_record(dict(row), line_number)
                for line_number, row in enumerate(reader, start=2)
            )
        merged, inserted, duplicates = reconcile_records((), records)
        if inserted != len(records) or duplicates:
            raise DataContractError("canonical CSV contains duplicate contest identifiers")
        return merged

    def append_validated(
        self,
        records: Sequence[CanonicalDrawRecord],
    ) -> AppendResult:
        current = self.list_all()
        merged, inserted, duplicates = reconcile_records(current, records)
        if inserted == 0:
            return AppendResult(inserted=0, duplicates=duplicates, total=len(merged))

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
                writer.writerows(_record_to_row(record) for record in merged)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self._path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return AppendResult(inserted=inserted, duplicates=duplicates, total=len(merged))
