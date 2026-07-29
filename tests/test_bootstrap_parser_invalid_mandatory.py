"""Tests for mandatory field validation in CSV parser."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import DataContractError
from bonoai.infrastructure.csv_bootstrap import CsvHistoricalSource


class CsvHistoricalSourceMandatoryTests(TestCase):
    def test_rejects_missing_contest_id(self) -> None:
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
                    "contest_id": "",
                    "held_on": "2026-07-27",
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
            with self.assertRaisesRegex(DataContractError, "contest_id is mandatory"):
                source.load()

    def test_rejects_empty_complementary(self) -> None:
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
                    "complementary": "",
                    "reintegro": "3",
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "complementary is mandatory"):
                source.load()

    def test_rejects_empty_reintegro(self) -> None:
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
                    "reintegro": "",
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "reintegro is mandatory"):
                source.load()

    def test_rejects_empty_held_on_field(self) -> None:
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
                    "held_on": "",
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
            with self.assertRaisesRegex(DataContractError, "held_on is mandatory"):
                source.load()

    def test_rejects_empty_source_url_field(self) -> None:
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
                    "reintegro": "3",
                    "source_url": "",
                })

            source = CsvHistoricalSource(path)
            with self.assertRaisesRegex(DataContractError, "source_url is mandatory"):
                source.load()
