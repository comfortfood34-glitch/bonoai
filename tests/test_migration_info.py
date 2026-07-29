"""Tests for schema migration info detection."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.infrastructure.migrations import get_migration_info


class MigrationInfoTests(TestCase):
    def test_migration_info_detects_v1(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=[
                        "contest_id",
                        "held_on",
                        "source_name",
                    ],
                )
                writer.writeheader()

            info = get_migration_info(path)
            self.assertEqual(info["schema_version"], "1")

    def test_migration_info_detects_v2(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=[
                        "contest_id",
                        "held_on",
                        "source_type",
                        "schema_version",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "contest_id": "test",
                    "held_on": "2026-07-27",
                    "source_type": "official",
                    "schema_version": "2",
                })

            info = get_migration_info(path)
            self.assertEqual(info["schema_version"], "2")

    def test_migration_info_missing_file(self) -> None:
        path = Path("/nonexistent/path/draws.csv")
        info = get_migration_info(path)
        self.assertIsNone(info["schema_version"])
