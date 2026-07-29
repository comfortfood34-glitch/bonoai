"""Tests for data-audit CLI command."""

import argparse
import csv
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.cli import _run_data_audit, _run_data_bootstrap
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository


class DataAuditCliTests(TestCase):
    def test_audit_empty_repository(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            args = argparse.Namespace(data_dir=data_dir, as_json=False)

            result = _run_data_audit(args)
            self.assertEqual(result, 0)

    def test_audit_with_json_output(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            repository = CsvDrawRepository(data_dir / "processed" / "draws.csv")
            record = CanonicalDrawRecord(
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
            repository.append_validated((record,))

            args = argparse.Namespace(data_dir=data_dir, as_json=True)

            result = _run_data_audit(args)
            self.assertEqual(result, 0)

    def test_audit_with_text_output_no_conflicts(self) -> None:
        """Verify audit prints summary with text output when no conflicts."""
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            repository = CsvDrawRepository(data_dir / "processed" / "draws.csv")
            record = CanonicalDrawRecord(
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
            repository.append_validated((record,))

            args = argparse.Namespace(data_dir=data_dir, as_json=False)

            result = _run_data_audit(args)
            self.assertEqual(result, 0)

    def test_bootstrap_then_audit_integration(self) -> None:
        """Verify bootstrap and audit work together."""
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

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

            args = argparse.Namespace(
                file=csv_file,
                source_name="lotoideas",
                data_dir=data_dir,
                as_json=False,
            )

            result = _run_data_bootstrap(args)
            self.assertEqual(result, 0)

            audit_args = argparse.Namespace(data_dir=data_dir, as_json=False)
            result = _run_data_audit(audit_args)
            self.assertEqual(result, 0)
