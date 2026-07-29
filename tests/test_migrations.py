"""Tests for schema v1 → v2 migrations."""

import csv
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import DataContractError
from bonoai.infrastructure.migrations import (
    get_migration_info,
    migrate_v1_to_v2,
)


class MigrateV1ToV2Tests(TestCase):
    def test_migrates_v1_to_v2_selae_official(self) -> None:
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
                        "schema_version",
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
                    "source_name": "selae",
                    "source_url": "https://www.selae.es/lotobonoloto",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "schema_version": "1",
                })

            migrate_v1_to_v2(path)

            with path.open("r", encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_type"], "official")
            self.assertEqual(rows[0]["schema_version"], "2")
            backup_files = list(Path(directory).glob("*.backup"))
            self.assertEqual(len(backup_files), 1)

    def test_migrates_v1_to_v2_auxiliary(self) -> None:
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
                        "schema_version",
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
                    "source_name": "lotoideas",
                    "source_url": "https://example.test/historical",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "schema_version": "1",
                })

            migrate_v1_to_v2(path)

            with path.open("r", encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_type"], "auxiliary")
            self.assertEqual(rows[0]["schema_version"], "2")

    def test_migration_rejects_selae_nonofficial_url(self) -> None:
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
                        "schema_version",
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
                    "source_name": "selae",
                    "source_url": "https://example.test/invalid",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "schema_version": "1",
                })

            with self.assertRaisesRegex(DataContractError, "fail-closed"):
                migrate_v1_to_v2(path)

    def test_migration_rejects_unknown_source(self) -> None:
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
                        "schema_version",
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
                    "source_name": "unknown_source",
                    "source_url": "https://example.test/unknown",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "c" * 64,
                    "schema_version": "1",
                })

            with self.assertRaisesRegex(DataContractError, "fail-closed"):
                migrate_v1_to_v2(path)

    def test_migration_is_idempotent(self) -> None:
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
                        "schema_version",
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
                    "source_name": "lotoideas",
                    "source_url": "https://example.test/historical",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "schema_version": "1",
                })

            migrate_v1_to_v2(path)
            first_hash = hashlib.sha256(path.read_bytes()).hexdigest()

            migrate_v1_to_v2(path)
            second_hash = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(first_hash, second_hash)

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
