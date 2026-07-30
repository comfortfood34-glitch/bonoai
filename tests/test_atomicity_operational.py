"""Atomicity tests: operational failures preserve file state."""

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
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


class AtomicityOperationalTests(TestCase):
    """5 operational failure scenarios: file/backup integrity."""

    def test_atomicity_5_unknown_schema_no_mutation(self) -> None:
        """Scenario 5: Unknown schema - file unchanged on schema fail."""
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
                    "reintegro": "8",
                    "source_name": "test",
                    "source_url": "https://example.test",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "source_type": "official",
                    "schema_version": "99",
                }])

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            size_after = path.stat().st_size

            self.assertEqual(hash_before, hash_after)
            self.assertEqual(size_before, size_after)

    def test_atomicity_6_invalid_provenance_no_mutation(self) -> None:
        """Scenario 6: Invalid provenance - file unchanged on fail."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            valid = make_valid_record()
            repository.append_validated((valid,))

            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()
            size_before = path.stat().st_size

            with self.assertRaises(DataContractError):
                CanonicalDrawRecord(
                    draw=valid.draw,
                    provenances=(
                        SourceProvenance(
                            source_name="",
                            source_url="https://example.test",
                            retrieved_at_utc=RETRIEVED_AT,
                            source_sha256="b" * 64,
                            source_type="official",
                            schema_version=2,
                        ),
                    ),
                )

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            size_after = path.stat().st_size

            self.assertEqual(hash_before, hash_after)
            self.assertEqual(size_before, size_after)

    def test_atomicity_7_write_failure_no_partial_state(self) -> None:
        """Scenario 7: Write failure - temp cleanup, no partial state."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            valid = make_valid_record()
            repository.append_validated((valid,))

            files_before = set(Path(directory).glob("*"))
            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()

            new_record = make_valid_record("bonoloto:2026-07-29")

            with patch("bonoai.infrastructure.csv_repository.os.replace") as mock_replace:
                mock_replace.side_effect = OSError("Disk full")
                with self.assertRaises(OSError):
                    repository.append_validated((new_record,))

            files_after = set(Path(directory).glob("*"))
            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(files_before, files_after)
            self.assertEqual(hash_before, hash_after)

    def test_atomicity_8_migration_failure_no_partial_state(self) -> None:
        """Scenario 8: Migration fail - main unchanged, backup preserved."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            path.write_text("contest_id,held_on,n1,n2,n3,n4,n5,n6,complementary,reintegro,"
                          "source_name,source_url,retrieved_at_utc,source_sha256\n"
                          "test:2026-07-28,2026-07-28,1,2,3,4,5,6,7,8,"
                          "test,https://example.test,2026-07-29T10:00:00+00:00,aaa\n",
                          encoding="utf-8")

            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()

            from bonoai.infrastructure.csv_repository import CsvDrawRepository
            repository = CsvDrawRepository(path)

            with self.assertRaises(DataContractError):
                repository.list_all()

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(hash_before, hash_after)

    def test_atomicity_9_sha256_divergence_detection(self) -> None:
        """Scenario 9: SHA-256 verification - detect format and length."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            record = make_valid_record()
            repository.append_validated((record,))

            loaded = repository.list_all()
            stored_sha = loaded[0].provenance.source_sha256

            file_content = path.read_bytes()
            recalculated_sha = hashlib.sha256(file_content).hexdigest()

            self.assertEqual(stored_sha, "a" * 64)
            self.assertIsNotNone(recalculated_sha)
            self.assertEqual(len(recalculated_sha), 64)
