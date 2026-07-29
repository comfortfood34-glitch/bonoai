from datetime import UTC, date, datetime, timedelta, timezone
from unittest import TestCase

from bonoai.domain.data import DataContractError, SourceProvenance
from bonoai.domain.models import Draw

SHA256 = "a" * 64


class SourceProvenanceTests(TestCase):
    def test_accepts_complete_provenance(self) -> None:
        provenance = SourceProvenance(
            source_name="selae",
            source_url="https://www.loteriasyapuestas.es/feed",
            retrieved_at_utc=datetime(2026, 7, 29, 10, 0, tzinfo=UTC),
            source_sha256=SHA256,
        )

        self.assertEqual(provenance.schema_version, 1)

    def test_rejects_empty_source_name(self) -> None:
        with self.assertRaisesRegex(DataContractError, "source_name"):
            SourceProvenance(
                source_name=" ",
                source_url="https://example.test/feed",
                retrieved_at_utc=datetime(2026, 7, 29, tzinfo=UTC),
                source_sha256=SHA256,
            )

    def test_rejects_relative_source_url(self) -> None:
        with self.assertRaisesRegex(DataContractError, "absolute"):
            SourceProvenance(
                source_name="selae",
                source_url="/feed",
                retrieved_at_utc=datetime(2026, 7, 29, tzinfo=UTC),
                source_sha256=SHA256,
            )

    def test_rejects_naive_retrieval_time(self) -> None:
        with self.assertRaisesRegex(DataContractError, "timezone-aware"):
            SourceProvenance(
                source_name="selae",
                source_url="https://example.test/feed",
                retrieved_at_utc=datetime(2026, 7, 29),
                source_sha256=SHA256,
            )

    def test_rejects_non_utc_retrieval_time(self) -> None:
        madrid_offset = timezone(timedelta(hours=2))
        with self.assertRaisesRegex(DataContractError, "must use UTC"):
            SourceProvenance(
                source_name="selae",
                source_url="https://example.test/feed",
                retrieved_at_utc=datetime(2026, 7, 29, tzinfo=madrid_offset),
                source_sha256=SHA256,
            )

    def test_rejects_invalid_hash(self) -> None:
        with self.assertRaisesRegex(DataContractError, "64 lowercase"):
            SourceProvenance(
                source_name="selae",
                source_url="https://example.test/feed",
                retrieved_at_utc=datetime(2026, 7, 29, tzinfo=UTC),
                source_sha256="not-a-hash",
            )

    def test_rejects_unknown_schema_version(self) -> None:
        with self.assertRaisesRegex(DataContractError, "unsupported schema"):
            SourceProvenance(
                source_name="selae",
                source_url="https://example.test/feed",
                retrieved_at_utc=datetime(2026, 7, 29, tzinfo=UTC),
                source_sha256=SHA256,
                schema_version=2,
            )


class DrawContractTests(TestCase):
    def test_requires_complementary_as_mandatory_int(self) -> None:
        draw = Draw(
            contest_id="bonoloto:2026-07-28",
            held_on=date(2026, 7, 28),
            numbers=(1, 17, 35, 36, 44, 49),
            complementary=14,
            reintegro=3,
        )
        self.assertEqual(draw.complementary, 14)

    def test_requires_reintegro_as_mandatory_int(self) -> None:
        draw = Draw(
            contest_id="bonoloto:2026-07-28",
            held_on=date(2026, 7, 28),
            numbers=(1, 17, 35, 36, 44, 49),
            complementary=14,
            reintegro=6,
        )
        self.assertEqual(draw.reintegro, 6)

    def test_rejects_complementary_below_minimum(self) -> None:
        with self.assertRaisesRegex(ValueError, "complementary must be between 1 and 49"):
            Draw(
                contest_id="bonoloto:2026-07-28",
                held_on=date(2026, 7, 28),
                numbers=(1, 17, 35, 36, 44, 49),
                complementary=0,
                reintegro=3,
            )

    def test_rejects_complementary_above_maximum(self) -> None:
        with self.assertRaisesRegex(ValueError, "complementary must be between 1 and 49"):
            Draw(
                contest_id="bonoloto:2026-07-28",
                held_on=date(2026, 7, 28),
                numbers=(1, 17, 35, 36, 44, 49),
                complementary=50,
                reintegro=3,
            )

    def test_rejects_complementary_duplicating_main_number(self) -> None:
        with self.assertRaisesRegex(ValueError, "complementary must not repeat"):
            Draw(
                contest_id="bonoloto:2026-07-28",
                held_on=date(2026, 7, 28),
                numbers=(1, 17, 35, 36, 44, 49),
                complementary=17,
                reintegro=3,
            )

    def test_rejects_reintegro_below_minimum(self) -> None:
        with self.assertRaisesRegex(ValueError, "reintegro must be between 0 and 9"):
            Draw(
                contest_id="bonoloto:2026-07-28",
                held_on=date(2026, 7, 28),
                numbers=(1, 17, 35, 36, 44, 49),
                complementary=14,
                reintegro=-1,
            )

    def test_rejects_reintegro_above_maximum(self) -> None:
        with self.assertRaisesRegex(ValueError, "reintegro must be between 0 and 9"):
            Draw(
                contest_id="bonoloto:2026-07-28",
                held_on=date(2026, 7, 28),
                numbers=(1, 17, 35, 36, 44, 49),
                complementary=14,
                reintegro=10,
            )
