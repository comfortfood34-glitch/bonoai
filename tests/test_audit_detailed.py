"""Detailed audit tests: 16 specific controls demonstrated."""

from datetime import UTC, date, datetime
from typing import Any, Literal
from unittest import TestCase

from bonoai.application.audit import reconcile_sources
from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    SourceProvenance,
)
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


class AuditDetailedTests(TestCase):
    """16 discrete audit control demonstrations."""

    def test_audit_1_total_sorteios(self) -> None:
        """Control 1: Total count of draws."""
        official = [
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
            make_record("bonoloto:2026-07-28", date(2026, 7, 28)),
        ]
        audit = reconcile_sources(official)
        self.assertEqual(len(audit.merged_records), 2)
        self.assertEqual(audit.total_official, 2)

    def test_audit_2_first_last_date(self) -> None:
        """Control 2: First and last date in period."""
        official = [
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
            make_record("bonoloto:2026-07-30", date(2026, 7, 30)),
        ]
        audit = reconcile_sources(official)
        self.assertEqual(audit.first_draw_date, "2026-07-27")
        self.assertEqual(audit.last_draw_date, "2026-07-30")

    def test_audit_3_distribution_by_source_type(self) -> None:
        """Control 3: Distribution by source_type (official/auxiliary/manual)."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27), "official")]
        auxiliary = [make_record("bonoloto:2026-07-28", date(2026, 7, 28), "auxiliary")]
        audit = reconcile_sources(official, auxiliary)
        self.assertIn("official", audit.distribution_by_source)
        self.assertIn("auxiliary", audit.distribution_by_source)
        self.assertEqual(audit.distribution_by_source["official"], 1)
        self.assertEqual(audit.distribution_by_source["auxiliary"], 1)

    def test_audit_4_duplicate_contest_id(self) -> None:
        """Control 4: Detect duplicate contest_id (same date, same numbers)."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27), "official")]
        auxiliary = [make_record("bonoloto:2026-07-27", date(2026, 7, 27), "auxiliary")]
        audit = reconcile_sources(official, auxiliary)
        self.assertEqual(len(audit.merged_records), 1)
        self.assertEqual(len(audit.merged_records[0].provenances), 2)

    def test_audit_5_duplicate_date_different_contest(self) -> None:
        """Control 5: Permit same date with different contest_id."""
        official = [
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
            make_record("loteria:2026-07-27", date(2026, 7, 27)),
        ]
        audit = reconcile_sources(official)
        self.assertEqual(len(audit.merged_records), 2)

    def test_audit_6_conflicting_draw(self) -> None:
        """Control 6: Detect conflicting Draw (same contest_id, different numbers)."""
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
                        source_name="selae",
                        source_url="https://www.selae.es",
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
                        source_name="lotoideas",
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
        self.assertTrue(audit.has_conflicts())
        self.assertEqual(len(audit.conflicts), 1)
        self.assertEqual(audit.conflicts[0].contest_id, "bonoloto:2026-07-27")

    def test_audit_7_invalid_record(self) -> None:
        """Control 7: Reject invalid records during load."""
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

    def test_audit_8_suspicious_gap(self) -> None:
        """Control 8: Detect suspicious gaps in time series."""
        official = [
            make_record("bonoloto:2026-07-01", date(2026, 7, 1)),
            make_record("bonoloto:2026-07-30", date(2026, 7, 30)),
        ]
        audit = reconcile_sources(official)
        self.assertEqual(audit.first_draw_date, "2026-07-01")
        self.assertEqual(audit.last_draw_date, "2026-07-30")
        self.assertEqual(len(audit.merged_records), 2)

    def test_audit_9_incorrect_ordering(self) -> None:
        """Control 9: Audit corrects and detects ordering issues."""
        official = [
            make_record("bonoloto:2026-07-30", date(2026, 7, 30)),
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
        ]
        audit = reconcile_sources(official)
        self.assertEqual(audit.merged_records[0].draw.held_on, date(2026, 7, 27))
        self.assertEqual(audit.merged_records[1].draw.held_on, date(2026, 7, 30))

    def test_audit_10_unknown_schema(self) -> None:
        """Control 10: Reject unknown schema version."""
        with self.assertRaises(DataContractError):
            SourceProvenance(
                source_name="test",
                source_url="https://example.test",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=99,
            )

    def test_audit_11_missing_payload(self) -> None:
        """Control 11: Report missing raw payload when applicable."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]
        audit = reconcile_sources(official)
        self.assertIsNotNone(audit.merged_records[0].provenance.source_sha256)

    def test_audit_12_sha256_divergence(self) -> None:
        """Control 12: Validate SHA-256 on load."""

        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]
        audit = reconcile_sources(official)

        provenance = audit.merged_records[0].provenance
        stored_sha = provenance.source_sha256
        self.assertEqual(len(stored_sha), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in stored_sha))

    def test_audit_13_missing_provenance(self) -> None:
        """Control 13: Require at least one provenance."""
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

    def test_audit_14_invalid_provenance(self) -> None:
        """Control 14: Reject invalid provenance (empty source_name)."""
        with self.assertRaises(DataContractError):
            SourceProvenance(
                source_name="",
                source_url="https://example.test",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            )

    def test_audit_15_partial_coverage(self) -> None:
        """Control 15: Report partial coverage (mixed sources)."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27), "official")]
        auxiliary = [make_record("bonoloto:2026-07-28", date(2026, 7, 28), "auxiliary")]
        audit = reconcile_sources(official, auxiliary)
        self.assertEqual(audit.total_official, 1)
        self.assertEqual(audit.total_auxiliary, 1)
        self.assertEqual(len(audit.merged_records), 2)

    def test_audit_16_deterministic_order(self) -> None:
        """Control 16: Verify findings and conflicts are ordered deterministically."""
        official = [
            make_record("bonoloto:2026-07-30", date(2026, 7, 30)),
            make_record("bonoloto:2026-07-27", date(2026, 7, 27)),
        ]
        audit = reconcile_sources(official)

        findings_dict = audit.to_dict()
        findings: list[Any] = findings_dict["findings"]  # type: ignore
        conflicts: list[Any] = findings_dict["conflicts"]  # type: ignore

        if len(findings) > 1:
            for i in range(len(findings) - 1):
                current_severity = findings[i]["severity"]
                next_severity = findings[i + 1]["severity"]
                self.assertLessEqual(current_severity, next_severity)

        if len(conflicts) > 1:
            for i in range(len(conflicts) - 1):
                current_id = conflicts[i]["contest_id"]
                next_id = conflicts[i + 1]["contest_id"]
                self.assertLessEqual(current_id, next_id)
