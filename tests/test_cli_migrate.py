"""Tests for data-migrate CLI command."""

import contextlib
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.cli import main
from bonoai.infrastructure.csv_repository import CANONICAL_COLUMNS


class DataMigrateCLITests(TestCase):
    def test_data_migrate_file_not_found(self) -> None:
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-migrate", "--data-dir", directory])

        self.assertEqual(status, 0)
        self.assertIn("Arquivo não encontrado", output.getvalue())

    def test_data_migrate_file_not_found_json(self) -> None:
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-migrate", "--data-dir", directory, "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["status"], "nao_encontrado")

    def test_data_migrate_already_v2(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_path = data_dir / "processed" / "draws.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                writer.writerow({
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "2",
                    "n3": "3",
                    "n4": "4",
                    "n5": "5",
                    "n6": "6",
                    "complementary": "7",
                    "reintegro": "8",
                    "source_name": "test",
                    "source_url": "https://example.test",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "source_type": "official",
                    "schema_version": "2",
                })

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-migrate", "--data-dir", str(data_dir)])

        self.assertEqual(status, 0)
        self.assertIn("Schema já é v2", output.getvalue())

    def test_data_migrate_already_v2_json(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_path = data_dir / "processed" / "draws.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                writer.writerow({
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "2",
                    "n3": "3",
                    "n4": "4",
                    "n5": "5",
                    "n6": "6",
                    "complementary": "7",
                    "reintegro": "8",
                    "source_name": "test",
                    "source_url": "https://example.test",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "a" * 64,
                    "source_type": "official",
                    "schema_version": "2",
                })

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-migrate", "--data-dir", str(data_dir), "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["status"], "ja_v2")

    def test_data_migrate_v1_to_v2(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_path = data_dir / "processed" / "draws.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
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
                    "source_url": "https://lotoideas.com/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-migrate", "--data-dir", str(data_dir)])

        self.assertEqual(status, 0)
        self.assertIn("Migração concluída", output.getvalue())

    def test_data_migrate_v1_to_v2_json(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_path = data_dir / "processed" / "draws.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
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
                    "source_url": "https://lotoideas.com/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-migrate", "--data-dir", str(data_dir), "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["status"], "migrado")
        self.assertEqual(payload["schema_version"], "2")
