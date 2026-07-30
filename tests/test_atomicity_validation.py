"""Atomicity tests: validation failures preserve file state."""

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_valid_record(contest_id: str = "bonoloto:2026-07-28") -> CanonicalDrawRecord:
    return CanonicalDrawRecord(
        draw=Draw(
            contest_id=contest_id,
            held_on=date(2026, 7, 28),
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=3,
        ),
        provenances=(
            SourceProvenance(
                source_name="selae",
                source_url="https://www.selae.es/lotobonoloto",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            ),
        ),
    )


class AtomicityValidationTests(TestCase):
    """4 validation failure scenarios: file unchanged."""

    def test_atomicity_1_conflict_no_file_mutation(self) -> None:
        """Scenario 1: Conflict detection - file unchanged."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            original = make_valid_record()
            repository.append_validated((original,))

            content_before = path.read_bytes()
            hash_before = hashlib.sha256(content_before).hexdigest()
            size_before = path.stat().st_size

            conflict = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(10, 20, 30, 40, 45, 49),
                    complementary=15,
                    reintegro=2,
                ),
                provenances=(original.provenances[0],),
            )

            with self.assertRaises(SourceConflictError):
                repository.append_validated((conflict,))

            content_after = path.read_bytes()
            hash_after = hashlib.sha256(content_after).hexdigest()
            size_after = path.stat().st_size

            self.assertEqual(content_before, content_after)
            self.assertEqual(hash_before, hash_after)
            self.assertEqual(size_before, size_after)

    def test_atomicity_2_invalid_csv_no_mutation(self) -> None:
        """Scenario 2: truly invalid CSV - file unchanged on validation."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            valid = make_valid_record()
            repository.append_validated((valid,))

            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()
            size_before = path.stat().st_size

            invalid_csv = Path(directory) / "invalid.csv"
            invalid_csv.write_text(
                "contest_id,held_on,n1,n2,n3,n4,n5,n6,complementary,reintegro,"
                "source_name,source_url,retrieved_at_utc,source_sha256,source_type,schema_version\n"
                "bonoloto:2026-07-28,2026-07-28,1,2,3,4,5,6,,8,"
                "test,https://example.test,2026-07-29T10:00:00+00:00,"
                "c" * 64 + ",official,2\n",
                encoding="utf-8",
            )

            from bonoai.infrastructure.csv_repository import CsvDrawRepository as CsvRepo

            with self.assertRaises(DataContractError):
                CsvRepo(invalid_csv).list_all()

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            size_after = path.stat().st_size

            self.assertEqual(hash_before, hash_after)
            self.assertEqual(size_before, size_after)

    def test_atomicity_3_complementary_missing_no_mutation(self) -> None:
        """Scenario 3: complementary missing - file unchanged on validation."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            valid = make_valid_record()
            repository.append_validated((valid,))

            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()
            size_before = path.stat().st_size

            from bonoai.infrastructure.csv_repository import _rows_to_records

            with self.assertRaises(DataContractError):
                _rows_to_records([{
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "2",
                    "n3": "3",
                    "n4": "4",
                    "n5": "5",
                    "n6": "6",
                    "complementary": "",
                    "reintegro": "8",
                    "source_name": "test",
                    "source_url": "https://example.test",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "source_type": "official",
                    "schema_version": "2",
                }])

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            size_after = path.stat().st_size

            self.assertEqual(hash_before, hash_after)
            self.assertEqual(size_before, size_after)

    def test_atomicity_4_reintegro_missing_no_mutation(self) -> None:
        """Scenario 4: reintegro missing - file unchanged on validation."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            valid = make_valid_record()
            repository.append_validated((valid,))

            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()
            size_before = path.stat().st_size

            from bonoai.infrastructure.csv_repository import _rows_to_records

            with self.assertRaises(DataContractError):
                _rows_to_records([{
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "2",
                    "n3": "3",
                    "n4": "4",
                    "n5": "5",
                    "n6": "6",
                    "complementary": "7",
                    "reintegro": "",
                    "source_name": "test",
                    "source_url": "https://example.test",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "source_type": "official",
                    "schema_version": "2",
                }])

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            size_after = path.stat().st_size

            self.assertEqual(hash_before, hash_after)
            self.assertEqual(size_before, size_after)
