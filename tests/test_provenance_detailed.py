"""Tests for provenance validation and handling."""

from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


class ProvenanceDetailedTests(TestCase):
    """7 discrete provenance validation scenarios."""

    def test_provenance_1_empty_tuple_rejected(self) -> None:
        """Test 1: Empty provenances tuple is rejected."""
        with self.assertRaisesRegex(
            DataContractError, "requires at least one provenance"
        ):
            CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(),
            )

    def test_provenance_2_deterministic_ordering(self) -> None:
        """Test 2: Multiple provenances ordered deterministically by fingerprint."""
        prov1 = SourceProvenance(
            source_name="lotoideas",
            source_url="https://example.test/historical",
            retrieved_at_utc=RETRIEVED_AT,
            source_sha256="b" * 64,
            source_type="auxiliary",
            schema_version=2,
        )
        prov2 = SourceProvenance(
            source_name="selae",
            source_url="https://www.selae.es/lotobonoloto",
            retrieved_at_utc=RETRIEVED_AT,
            source_sha256="a" * 64,
            source_type="official",
            schema_version=2,
        )

        record = CanonicalDrawRecord(
            draw=Draw(
                contest_id="bonoloto:2026-07-28",
                held_on=date(2026, 7, 28),
                numbers=(1, 2, 3, 4, 5, 6),
                complementary=7,
                reintegro=8,
            ),
            provenances=(prov2, prov1),
        )

        fingerprints = [p.fingerprint() for p in record.provenances]
        self.assertEqual(fingerprints[0][0], "auxiliary")
        self.assertEqual(fingerprints[1][0], "official")

    def test_provenance_3_duplicate_within_record_rejected(self) -> None:
        """Test 3: Duplicate provenance by fingerprint within same record rejected."""
        prov = SourceProvenance(
            source_name="selae",
            source_url="https://www.selae.es/lotobonoloto",
            retrieved_at_utc=RETRIEVED_AT,
            source_sha256="a" * 64,
            source_type="official",
            schema_version=2,
        )

        with self.assertRaisesRegex(
            DataContractError, "duplicate provenance"
        ):
            CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(prov, prov),
            )

    def test_provenance_4_mixed_new_and_duplicate_counted(self) -> None:
        """Test 4: Mix of new and duplicate provenances counted individually."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            prov_official = SourceProvenance(
                source_name="selae",
                source_url="https://www.selae.es/lotobonoloto",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            )
            prov_auxiliary = SourceProvenance(
                source_name="lotoideas",
                source_url="https://example.test/historical",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="b" * 64,
                source_type="auxiliary",
                schema_version=2,
            )

            record1 = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(prov_official,),
            )
            repository.append_validated((record1,))

            record2 = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(prov_official, prov_auxiliary),
            )

            result = repository.append_validated((record2,))

            self.assertEqual(result.duplicate_provenances, 1)
            self.assertEqual(result.added_provenances, 1)

    def test_provenance_5_repeated_duplicates_not_added(self) -> None:
        """Test 5: Repeated identical provenances are not re-added."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            prov = SourceProvenance(
                source_name="selae",
                source_url="https://www.selae.es/lotobonoloto",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            )

            record = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(prov,),
            )

            result1 = repository.append_validated((record,))
            self.assertEqual(result1.inserted_draws, 1)

            result2 = repository.append_validated((record,))
            self.assertEqual(result2.duplicate_provenances, 1)
            self.assertEqual(result2.inserted_draws, 0)
            self.assertEqual(result2.added_provenances, 0)

    def test_provenance_6_csv_duplicate_fingerprint_rejected(self) -> None:
        """Test 6: CSV with duplicate fingerprint for same contest rejected."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            sha = "a" * 64
            csv_content = (
                "contest_id,held_on,n1,n2,n3,n4,n5,n6,complementary,reintegro,"
                "source_name,source_url,retrieved_at_utc,source_sha256,source_type,schema_version\n"
                "bonoloto:2026-07-28,2026-07-28,1,2,3,4,5,6,7,8,"
                f"selae,https://www.selae.es/lotobonoloto,2026-07-29T10:00:00+00:00,"
                f"{sha},official,2\n"
                "bonoloto:2026-07-28,2026-07-28,1,2,3,4,5,6,7,8,"
                f"selae,https://www.selae.es/lotobonoloto,2026-07-29T10:00:00+00:00,"
                f"{sha},official,2\n"
            )
            path.write_text(csv_content, encoding="utf-8")

            repository = CsvDrawRepository(path)

            with self.assertRaisesRegex(DataContractError, "duplicate provenance"):
                repository.list_all()

    def test_provenance_7_round_trip_preserves_all(self) -> None:
        """Test 7: Round-trip through CSV preserves all provenances."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            prov1 = SourceProvenance(
                source_name="selae",
                source_url="https://www.selae.es/lotobonoloto",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            )
            prov2 = SourceProvenance(
                source_name="lotoideas",
                source_url="https://example.test/historical",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="b" * 64,
                source_type="auxiliary",
                schema_version=2,
            )

            original = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-28",
                    held_on=date(2026, 7, 28),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(prov1, prov2),
            )

            repository.append_validated((original,))
            loaded = repository.list_all()

            self.assertEqual(len(loaded), 1)
            self.assertEqual(len(loaded[0].provenances), 2)

            loaded_fps = {p.fingerprint() for p in loaded[0].provenances}
            original_fps = {p.fingerprint() for p in original.provenances}
            self.assertEqual(loaded_fps, original_fps)
