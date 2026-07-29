"""CSV-based historical data loader for auxiliary sources."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bonoai.domain.data import (
    CANONICAL_SCHEMA_VERSION,
    CanonicalDrawRecord,
    DataContractError,
    SourceProvenance,
)
from bonoai.domain.models import Draw


class CsvHistoricalSource:
    """Load and validate historical records from a local CSV file."""

    def __init__(self, path: Path, source_name: str = "auxiliary") -> None:
        """Initialize loader for CSV file at path.

        Args:
            path: Path to CSV file with historical records.
            source_name: Identifier for this historical source (e.g., "lotoideas").

        Raises:
            DataContractError: If path does not exist.
        """
        if not path.exists():
            raise DataContractError(f"Historical data file not found: {path}")
        self.path = path
        self.source_name = source_name

    def load(self) -> tuple[CanonicalDrawRecord, ...]:
        """Load and validate records from CSV file.

        Expected columns match canonical schema:
        contest_id, held_on, n1, n2, n3, n4, n5, n6,
        complementary, reintegro, source_url

        Returns tuple of validated records sorted by held_on date.
        Raises DataContractError if any record is invalid or incomplete.
        """
        records: list[CanonicalDrawRecord] = []
        required_columns = {
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
            "source_url",
        }

        try:
            with self.path.open("r", encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames is None:
                    raise DataContractError(f"{self.path}: empty CSV file")

                actual_columns = set(reader.fieldnames)
                if not required_columns.issubset(actual_columns):
                    missing = required_columns - actual_columns
                    raise DataContractError(
                        f"{self.path}: missing columns {sorted(missing)}"
                    )

                for line_num, row in enumerate(reader, start=2):
                    try:
                        record = self._parse_row(row)
                        records.append(record)
                    except DataContractError as e:
                        raise DataContractError(
                            f"{self.path}:line {line_num}: {e!s}"
                        ) from e
        except DataContractError:
            raise
        except Exception as e:
            raise DataContractError(f"Failed to read {self.path}: {e}") from e

        if not records:
            raise DataContractError(f"No valid records found in {self.path}")

        sorted_records = tuple(sorted(records, key=lambda r: r.draw.held_on))
        return sorted_records

    def _parse_row(self, row: dict[str, Any]) -> CanonicalDrawRecord:
        """Parse and validate one CSV row.

        Raises DataContractError if any field is invalid or mandatory fields are empty.
        """
        contest_id = row.get("contest_id", "").strip()
        held_on_str = row.get("held_on", "").strip()
        source_url = row.get("source_url", "").strip()

        if not contest_id:
            raise DataContractError("contest_id is mandatory and cannot be empty")
        if not held_on_str:
            raise DataContractError("held_on is mandatory and cannot be empty")
        if not source_url:
            raise DataContractError("source_url is mandatory and cannot be empty")

        try:
            held_on = datetime.strptime(held_on_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise DataContractError(
                f"held_on must be YYYY-MM-DD format, got '{held_on_str}'"
            ) from e

        try:
            numbers = tuple(
                int(row.get(f"n{i}", "").strip()) for i in range(1, 7)
            )
        except ValueError as e:
            raise DataContractError("n1-n6 must all be integers") from e

        complementary_str = row.get("complementary", "").strip()
        if not complementary_str:
            raise DataContractError(
                "complementary is mandatory and cannot be empty"
            )
        try:
            complementary = int(complementary_str)
        except ValueError as e:
            raise DataContractError(
                f"complementary must be an integer, got '{complementary_str}'"
            ) from e

        reintegro_str = row.get("reintegro", "").strip()
        if not reintegro_str:
            raise DataContractError(
                "reintegro is mandatory and cannot be empty"
            )
        try:
            reintegro = int(reintegro_str)
        except ValueError as e:
            raise DataContractError(
                f"reintegro must be an integer, got '{reintegro_str}'"
            ) from e

        draw = Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=numbers,
            complementary=complementary,
            reintegro=reintegro,
        )

        provenance = SourceProvenance(
            source_name=self.source_name,
            source_url=source_url,
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="0" * 64,
            source_type="auxiliary",
            schema_version=CANONICAL_SCHEMA_VERSION,
        )

        return CanonicalDrawRecord(draw=draw, provenances=(provenance,))
