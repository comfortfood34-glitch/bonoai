"""Audit findings: SHA-256 mismatch, gaps, and coverage."""

from datetime import UTC, date, datetime
from typing import Literal
from unittest import TestCase

from bonoai.application.audit import reconcile_sources
from bonoai.application.audit_models import AuditPolicy
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_record(
    contest_id: str,
    held_on: date,
    source_type: Literal["official", "auxiliary", "manual"] = "official",
) -> CanonicalDrawRecord:
    return CanonicalDrawRecord(
        draw=Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=8,
        ),
        provenances=(
            SourceProvenance(
                source_name="test_source",
                source_url="https://example.test",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type=source_type,
                schema_version=2,
            ),
        ),
    )


class AuditFindingsTests(TestCase):
    """Tests for detailed audit findings."""

    def test_audit_sha256_mismatch_with_reader(self) -> None:
        """Detect SHA-256 mismatch when payload bytes diverge."""

        class FakeMismatchedReader:
            def read_by_sha256(self, sha256: str) -> bytes | None:
                return b"payload bytes that don't match"

        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]
        reader = FakeMismatchedReader()
        audit = reconcile_sources(official, None, reader)

        sha_mismatch = [f for f in audit.findings if f.code == "raw_payload_sha256_mismatch"]
        self.assertEqual(len(sha_mismatch), 1)
        self.assertEqual(sha_mismatch[0].severity, "error")

    def test_audit_date_gaps(self) -> None:
        """Detect suspicious date gaps."""
        official = [
            make_record("bonoloto:2026-07-01", date(2026, 7, 1)),
            make_record("bonoloto:2026-07-15", date(2026, 7, 15)),
        ]
        policy = AuditPolicy(suspicious_gap_days=7)
        audit = reconcile_sources(official, None, None, policy)

        gap_findings = [f for f in audit.findings if f.code == "suspicious_date_gap"]
        self.assertEqual(len(gap_findings), 1)
        self.assertEqual(gap_findings[0].severity, "warning")

    def test_audit_partial_coverage(self) -> None:
        """Detect partial historical coverage."""
        official = [
            make_record("bonoloto:2026-07-15", date(2026, 7, 15)),
            make_record("bonoloto:2026-07-20", date(2026, 7, 20)),
        ]
        policy = AuditPolicy(
            expected_start_date=date(2026, 7, 1),
            expected_end_date=date(2026, 7, 31),
        )
        audit = reconcile_sources(official, None, None, policy)

        coverage_findings = [f for f in audit.findings if f.code == "partial_historical_coverage"]
        self.assertEqual(len(coverage_findings), 1)
        self.assertEqual(coverage_findings[0].severity, "warning")
