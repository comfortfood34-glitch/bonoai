"""Parametrized tests verifying all 12 AuditFinding codes are generated."""

from datetime import UTC, date, datetime
from typing import Literal
from unittest import TestCase

from bonoai.application.audit import reconcile_sources
from bonoai.application.audit_models import AuditPolicy
from bonoai.domain.data import (
    CanonicalDrawRecord,
    SourceProvenance,
)
from bonoai.domain.models import Draw

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_record(
    contest_id: str,
    held_on: date,
    numbers: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    source_type: Literal["official", "auxiliary", "manual"] = "official",
    source_name: str = "test_source",
    schema_version: int = 2,
) -> CanonicalDrawRecord:
    return CanonicalDrawRecord(
        draw=Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=numbers,
            complementary=7,
            reintegro=8,
        ),
        provenances=(
            SourceProvenance(
                source_name=source_name,
                source_url="https://example.test",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type=source_type,
                schema_version=schema_version,
            ),
        ),
    )


class AuditCodesTest(TestCase):
    """Verify all 12 AuditFinding codes are produced."""

    def test_duplicate_contest_id(self) -> None:
        """Code: duplicate_contest_id."""
        official = [
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
        ]
        audit = reconcile_sources(official)
        codes = {finding.code for finding in audit.findings}
        self.assertIn("duplicate_contest_id", codes)

    def test_duplicate_draw_date(self) -> None:
        """Code: duplicate_draw_date."""
        official = [
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
            make_record("loteria:2026-07-27", date(2026, 7, 27)),
        ]
        audit = reconcile_sources(official)
        codes = {finding.code for finding in audit.findings}
        self.assertIn("duplicate_draw_date", codes)

    def test_conflicting_draw(self) -> None:
        """Code: conflicting_draw."""
        official = [
            CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-27",
                    held_on=date(2026, 7, 27),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(
                    SourceProvenance(
                        source_name="source_a",
                        source_url="https://example.test",
                        retrieved_at_utc=RETRIEVED_AT,
                        source_sha256="a" * 64,
                        source_type="official",
                        schema_version=2,
                    ),
                ),
            ),
        ]
        auxiliary = [
            CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-27",
                    held_on=date(2026, 7, 27),
                    numbers=(10, 20, 30, 40, 45, 49),
                    complementary=15,
                    reintegro=2,
                ),
                provenances=(
                    SourceProvenance(
                        source_name="source_b",
                        source_url="https://example.test",
                        retrieved_at_utc=RETRIEVED_AT,
                        source_sha256="b" * 64,
                        source_type="auxiliary",
                        schema_version=2,
                    ),
                ),
            ),
        ]
        audit = reconcile_sources(official, auxiliary)
        codes = {finding.code for finding in audit.findings}
        self.assertIn("conflicting_draw", codes)

    def test_invalid_record(self) -> None:
        """Code: invalid_record (empty provenances caught at construction)."""
        from bonoai.domain.data import DataContractError
        with self.assertRaises(DataContractError):
            CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-27",
                    held_on=date(2026, 7, 27),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(),
            )

    def test_suspicious_date_gap(self) -> None:
        """Code: suspicious_date_gap."""
        official = [
            make_record("bonoloto:2026-07-01", date(2026, 7, 1)),
            make_record("bonoloto:2026-07-15", date(2026, 7, 15)),
        ]
        policy = AuditPolicy(suspicious_gap_days=7)
        audit = reconcile_sources(official, None, None, policy)
        codes = {finding.code for finding in audit.findings}
        self.assertIn("suspicious_date_gap", codes)

    def test_incorrect_ordering(self) -> None:
        """Code: incorrect_ordering."""
        official = [
            make_record("bonoloto:2026-07-30", date(2026, 7, 30)),
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
        ]
        audit = reconcile_sources(official)
        codes = {finding.code for finding in audit.findings}
        self.assertIn("incorrect_ordering", codes)

    def test_unknown_schema(self) -> None:
        """Code: unknown_schema."""
        from bonoai.domain.data import DataContractError
        with self.assertRaises(DataContractError):
            SourceProvenance(
                source_name="test",
                source_url="https://example.test",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=99,
            )

    def test_raw_payload_missing(self) -> None:
        """Code: raw_payload_missing."""
        class FakeNoPayloadReader:
            def read_by_sha256(self, sha256: str) -> bytes | None:
                return None

        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]
        reader = FakeNoPayloadReader()
        audit = reconcile_sources(official, None, reader)

        codes = {finding.code for finding in audit.findings}
        self.assertIn("raw_payload_missing", codes)

    def test_raw_payload_sha256_mismatch(self) -> None:
        """Code: raw_payload_sha256_mismatch."""
        class FakeMismatchedReader:
            def read_by_sha256(self, sha256: str) -> bytes | None:
                return b"payload bytes that don't match"

        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]
        reader = FakeMismatchedReader()
        audit = reconcile_sources(official, None, reader)

        codes = {finding.code for finding in audit.findings}
        self.assertIn("raw_payload_sha256_mismatch", codes)

    def test_missing_provenance(self) -> None:
        """Code: missing_provenance (caught at construction)."""
        from bonoai.domain.data import DataContractError
        with self.assertRaises(DataContractError):
            CanonicalDrawRecord(
                draw=Draw(
                    contest_id="bonoloto:2026-07-27",
                    held_on=date(2026, 7, 27),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(),
            )

    def test_invalid_provenance(self) -> None:
        """Code: invalid_provenance."""
        from bonoai.domain.data import DataContractError
        with self.assertRaises(DataContractError):
            SourceProvenance(
                source_name="",
                source_url="https://example.test",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            )

    def test_partial_historical_coverage(self) -> None:
        """Code: partial_historical_coverage."""
        official = [
            make_record("bonoloto:2026-07-15", date(2026, 7, 15)),
            make_record("bonoloto:2026-07-20", date(2026, 7, 20)),
        ]
        policy = AuditPolicy(
            expected_start_date=date(2026, 7, 1),
            expected_end_date=date(2026, 7, 31),
        )
        audit = reconcile_sources(official, None, None, policy)
        codes = {finding.code for finding in audit.findings}
        self.assertIn("partial_historical_coverage", codes)
