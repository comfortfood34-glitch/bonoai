"""Tests for data-migrate CLI error scenarios."""

import contextlib
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli import main
from bonoai.domain.data import DataContractError


class DataMigrateErrorTests(TestCase):
    def test_data_migrate_with_data_contract_error(self) -> None:
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
                    "source_name": "test",
                    "source_url": "https://example.test/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            with patch("bonoai.infrastructure.migrations.migrate_v1_to_v2") as mock_migrate:
                mock_migrate.side_effect = DataContractError("Invalid data")
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    status = main(["data-migrate", "--data-dir", str(data_dir)])

            self.assertEqual(status, 1)

    def test_data_migrate_with_data_contract_error_json(self) -> None:
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
                    "source_name": "test",
                    "source_url": "https://example.test/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            with patch("bonoai.infrastructure.migrations.migrate_v1_to_v2") as mock_migrate:
                mock_migrate.side_effect = DataContractError("Invalid data")
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    status = main(["data-migrate", "--data-dir", str(data_dir), "--json"])

            payload = json.loads(output.getvalue())
            self.assertEqual(status, 1)
            self.assertEqual(payload["status"], "erro_dados")

    def test_data_migrate_with_operational_error(self) -> None:
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
                    "source_name": "test",
                    "source_url": "https://example.test/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            with patch("bonoai.infrastructure.migrations.migrate_v1_to_v2") as mock_migrate:
                mock_migrate.side_effect = OSError("Permission denied")
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    status = main(["data-migrate", "--data-dir", str(data_dir)])

            self.assertEqual(status, 2)

    def test_data_migrate_with_operational_error_json(self) -> None:
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
                    "source_name": "test",
                    "source_url": "https://example.test/data",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                })

            with patch("bonoai.infrastructure.migrations.migrate_v1_to_v2") as mock_migrate:
                mock_migrate.side_effect = OSError("Permission denied")
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    status = main(["data-migrate", "--data-dir", str(data_dir), "--json"])

            payload = json.loads(output.getvalue())
            self.assertEqual(status, 2)
            self.assertEqual(payload["status"], "erro_operacional")

    def test_data_migrate_with_unknown_schema(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_path = data_dir / "processed" / "draws.csv"
            csv_path.write_text("test", encoding="utf-8")

            with patch("bonoai.infrastructure.migrations.get_migration_info") as mock_info:
                mock_info.return_value = {"schema_version": "99", "backup": None}
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    status = main(["data-migrate", "--data-dir", str(data_dir)])

            self.assertEqual(status, 2)

    def test_data_migrate_with_unknown_schema_json(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_path = data_dir / "processed" / "draws.csv"
            csv_path.write_text("test", encoding="utf-8")

            with patch("bonoai.infrastructure.migrations.get_migration_info") as mock_info:
                mock_info.return_value = {"schema_version": "99", "backup": None}
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    status = main(["data-migrate", "--data-dir", str(data_dir), "--json"])

            payload = json.loads(output.getvalue())
            self.assertEqual(status, 2)
            self.assertEqual(payload["status"], "schema_desconhecido")
