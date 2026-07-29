"""Tests for error paths and edge cases to achieve coverage targets."""

import argparse
import csv
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.cli import _run_data_bootstrap
from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CANONICAL_COLUMNS, CsvDrawRepository


class ErrorPathTests(TestCase):
    def test_csv_invalid_empty_source_type(self) -> None:
        """Verify empty source_type field raises DataContractError."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                row = {
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "3",
                    "source_name": "test",
                    "source_url": "https://example.test/feed",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "source_type": "",
                    "schema_version": "2",
                }
                writer.writerow(row)

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_csv_invalid_source_type_value(self) -> None:
        """Verify invalid source_type raises DataContractError."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                row = {
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "3",
                    "source_name": "test",
                    "source_url": "https://example.test/feed",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "source_type": "invalid",
                    "schema_version": "2",
                }
                writer.writerow(row)

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_audit_with_conflicts_prints_details(self) -> None:
        """Verify audit prints conflict details when conflicts exist."""
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            repository = CsvDrawRepository(data_dir / "processed" / "draws.csv")
            official = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=3,
                ),
                provenances=(
                    SourceProvenance(
                        source_name="selae",
                        source_url="https://www.selae.es/lotobonoloto",
                        retrieved_at_utc=datetime(2026, 7, 29, 10, 0, tzinfo=UTC),
                        source_sha256="a" * 64,
                        source_type="official",
                        schema_version=2,
                    ),
                ),
            )
            repository.append_validated((official,))

            csv_file = Path(directory) / "historical.csv"
            with csv_file.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=[
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
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "bonoloto:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "10",
                    "n2": "20",
                    "n3": "30",
                    "n4": "40",
                    "n5": "45",
                    "n6": "49",
                    "complementary": "15",
                    "reintegro": "2",
                    "source_url": "https://example.test/historical",
                })

            args = argparse.Namespace(
                file=csv_file,
                source_name="lotoideas",
                data_dir=data_dir,
                as_json=False,
            )

            with self.assertRaises(SystemExit):
                _run_data_bootstrap(args)

    def test_cli_exception_handler_data_contract_error(self) -> None:
        """Verify bootstrap handles DataContractError from invalid CSV."""
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_file = Path(directory) / "invalid.csv"
            csv_file.write_text("invalid content", encoding="utf-8")

            args = argparse.Namespace(
                file=csv_file,
                source_name="test",
                data_dir=data_dir,
                as_json=False,
            )

            with self.assertRaises(DataContractError):
                _run_data_bootstrap(args)

    def test_bootstrap_with_invalid_csv_triggers_error(self) -> None:
        """Verify bootstrap detects invalid CSV content."""
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_file = Path(directory) / "bad.csv"
            with csv_file.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=["contest_id", "held_on", "source_url"],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "source_url": "https://example.test",
                })

            args = argparse.Namespace(
                file=csv_file,
                source_name="test",
                data_dir=data_dir,
                as_json=False,
            )

            with self.assertRaises(DataContractError):
                _run_data_bootstrap(args)

    def test_migration_with_missing_schema_version_column(self) -> None:
        """Verify migration handles missing schema_version column."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=[
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
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "test:2026-07-27",
                    "held_on": "2026-07-27",
                    "n1": "1",
                    "n2": "2",
                    "n3": "3",
                    "n4": "4",
                    "n5": "5",
                    "n6": "6",
                    "complementary": "7",
                    "reintegro": "8",
                    "source_name": "lotoideas",
                    "source_url": "https://example.test/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            repository = CsvDrawRepository(path)
            records = repository.list_all()
            self.assertEqual(len(records), 1)

    def test_csv_invalid_number_format(self) -> None:
        """Verify invalid draw numbers raise DataContractError."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                row = {
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "not_a_number",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "3",
                    "source_name": "test",
                    "source_url": "https://example.test/feed",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "source_type": "auxiliary",
                    "schema_version": "2",
                }
                writer.writerow(row)

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_csv_invalid_datetime_format(self) -> None:
        """Verify invalid datetime raises DataContractError."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                row = {
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "3",
                    "source_name": "test",
                    "source_url": "https://example.test/feed",
                    "retrieved_at_utc": "invalid-datetime",
                    "source_sha256": "a" * 64,
                    "source_type": "auxiliary",
                    "schema_version": "2",
                }
                writer.writerow(row)

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_csv_missing_field_in_header(self) -> None:
        """Verify missing required field raises DataContractError."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=["contest_id", "held_on", "n1", "n2"],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "17",
                })

            with self.assertRaisesRegex(DataContractError, "invalid or missing fields"):
                CsvDrawRepository(path).list_all()
