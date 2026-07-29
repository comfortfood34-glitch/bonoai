"""Tests for type and format validation in CSV parser."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import DataContractError
from bonoai.infrastructure.csv_bootstrap import CsvHistoricalSource


class CsvHistoricalSourceFormatTests(TestCase):
    def test_rejects_missing_file(self) -> None:
        path = Path("/nonexistent/path/file.csv")
        with self.assertRaisesRegex(DataContractError, "not found"):
            CsvHistoricalSource(path)

    def test_rejects_empty_csv_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "empty.csv"
            path.write_text("", encoding="utf-8")

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "empty CSV file"):
                source.load()

    def test_rejects_missing_required_columns(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing_cols.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["contest_id", "held_on"])
                writer.writeheader()
                writer.writerow({"contest_id": "test", "held_on": "2026-07-27"})

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "missing columns"):
                source.load()

    def test_rejects_invalid_date_format(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "historical.csv"
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
                        "source_url",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "bonoloto:2026-07-27",
                    "held_on": "27/07/2026",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "3",
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "YYYY-MM-DD"):
                source.load()

    def test_rejects_non_integer_numbers(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "historical.csv"
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
                        "source_url",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "bonoloto:2026-07-27",
                    "held_on": "2026-07-27",
                    "n1": "invalid",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "3",
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "n1-n6 must all be integers"):
                source.load()

    def test_rejects_invalid_complementary(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "historical.csv"
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
                        "source_url",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "bonoloto:2026-07-27",
                    "held_on": "2026-07-27",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "not_a_number",
                    "reintegro": "3",
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "complementary must be an integer"):
                source.load()

    def test_rejects_invalid_reintegro(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "historical.csv"
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
                        "source_url",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "bonoloto:2026-07-27",
                    "held_on": "2026-07-27",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "not_a_number",
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "reintegro must be an integer"):
                source.load()
