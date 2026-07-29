"""Tests for valid CSV historical data parsing."""

import csv
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.infrastructure.csv_bootstrap import CsvHistoricalSource

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


class CsvHistoricalSourceValidTests(TestCase):
    def test_loads_valid_csv_file(self) -> None:
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
                    "source_url": "https://example.test/historical",
                })

            source = CsvHistoricalSource(path, source_name="lotoideas")
            records = source.load()

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].draw.contest_id, "bonoloto:2026-07-27")
            self.assertEqual(records[0].provenance.source_type, "auxiliary")

    def test_sorts_records_by_held_on_date(self) -> None:
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
                    "contest_id": "bonoloto:2026-07-29",
                    "held_on": "2026-07-29",
                    "n1": "1",
                    "n2": "2",
                    "n3": "3",
                    "n4": "4",
                    "n5": "5",
                    "n6": "6",
                    "complementary": "7",
                    "reintegro": "1",
                    "source_url": "https://example.test/historical",
                })
                writer.writerow({
                    "contest_id": "bonoloto:2026-07-27",
                    "held_on": "2026-07-27",
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

            source = CsvHistoricalSource(path, source_name="lotoideas")
            records = source.load()

            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].draw.held_on, date(2026, 7, 27))
            self.assertEqual(records[1].draw.held_on, date(2026, 7, 29))
