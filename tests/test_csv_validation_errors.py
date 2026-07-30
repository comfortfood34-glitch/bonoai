"""Tests for CSV validation error cases."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import DataContractError
from bonoai.infrastructure.csv_repository import CANONICAL_COLUMNS, CsvDrawRepository


class CsvValidationErrorTests(TestCase):
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

            with self.assertRaisesRegex(DataContractError, "header does not match schema"):
                CsvDrawRepository(path).list_all()
