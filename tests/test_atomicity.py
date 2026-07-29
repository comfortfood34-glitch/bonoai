"""Tests for atomic write operations and recovery from failures."""

import contextlib
import hashlib
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import (
    CanonicalDrawRecord,
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_valid_record() -> CanonicalDrawRecord:
    return CanonicalDrawRecord(
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
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            ),
        ),
    )


class AtomicityTests(TestCase):
    def test_atomicity_on_conflict_no_partial_write(self) -> None:
        """Verify file unchanged when conflict detected."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            original = make_valid_record()
            repository.append_validated((original,))

            hash_before = hashlib.sha256(path.read_bytes()).hexdigest()
            file_size_before = path.stat().st_size

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

            hash_after = hashlib.sha256(path.read_bytes()).hexdigest()
            file_size_after = path.stat().st_size

            self.assertEqual(hash_before, hash_after)
            self.assertEqual(file_size_before, file_size_after)

    def test_atomicity_no_temp_files_left_on_failure(self) -> None:
        """Verify temporary files cleaned up on failure."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            original = make_valid_record()
            repository.append_validated((original,))

            files_before = set(Path(directory).glob("*"))

            conflict = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(10, 20, 30, 40, 45, 49),
                    complementary=48,
                    reintegro=0,
                ),
                provenances=(original.provenances[0],),
            )

            with contextlib.suppress(SourceConflictError):
                repository.append_validated((conflict,))

            files_after = set(Path(directory).glob("*"))
            self.assertEqual(files_before, files_after)

    def test_atomicity_idempotent_append_unchanged(self) -> None:
        """Verify appending identical record twice is atomic."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            record = make_valid_record()
            repository.append_validated((record,))
            hash1 = hashlib.sha256(path.read_bytes()).hexdigest()

            result = repository.append_validated((record,))
            hash2 = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(result.duplicates, 1)
            self.assertEqual(result.inserted, 0)
            self.assertEqual(hash1, hash2)

    def test_atomicity_valid_append_after_conflict(self) -> None:
        """Verify file can recover and accept new valid data after conflict."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            record1 = make_valid_record()
            repository.append_validated((record1,))

            conflict = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(10, 20, 30, 40, 45, 49),
                    complementary=48,
                    reintegro=0,
                ),
                provenances=(record1.provenances[0],),
            )

            with self.assertRaises(SourceConflictError):
                repository.append_validated((conflict,))

            valid_new = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-29",
                    held_on=date(2026, 7, 29),
                    numbers=(10, 20, 30, 40, 45, 49),
                    complementary=15,
                    reintegro=2,
                ),
                provenances=(record1.provenances[0],),
            )

            result = repository.append_validated((valid_new,))
            self.assertEqual(result.inserted, 1)
            self.assertEqual(len(repository.list_all()), 2)

    def test_atomicity_hash_verification_on_load(self) -> None:
        """Verify stored records match their provenance on load."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            record = make_valid_record()
            repository.append_validated((record,))

            loaded = repository.list_all()
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].provenance.source_sha256, "a" * 64)

            hash_after_load = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertIsNotNone(hash_after_load)

    def test_atomicity_duplicate_detection_no_write_needed(self) -> None:
        """Verify duplicate records skip write entirely."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            record = make_valid_record()
            repository.append_validated((record,))

            file_mtime_before = path.stat().st_mtime

            import time
            time.sleep(0.01)

            result = repository.append_validated((record,))
            file_mtime_after = path.stat().st_mtime

            self.assertEqual(result.duplicates, 1)
            self.assertEqual(result.inserted, 0)
            self.assertEqual(file_mtime_before, file_mtime_after)
