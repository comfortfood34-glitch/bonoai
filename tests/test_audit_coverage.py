"""Tests for audit module coverage."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.audit import AuditFinding, DataAudit, reconcile_sources
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_record(
    contest_id: str,
    source_name: str,
    source_type: str,
    held_on: date,
    numbers: tuple[int, ...],
) -> CanonicalDrawRecord:
    return CanonicalDrawRecord(
        draw=Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=numbers,
            complementary=49 if 49 not in numbers else 48,
            reintegro=3,
        ),
        provenances=(
            SourceProvenance(
                source_name=source_name,
                source_url="https://example.test/feed",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type=source_type,  # type: ignore
                schema_version=2,
            ),
        ),
    )


class AuditExitCodeTests(TestCase):
    def test_exit_code_0_with_no_findings_no_conflicts(self) -> None:
        """Verify exit code is 0 when no findings and no conflicts."""
        audit = DataAudit(
            total_official=1,
            total_auxiliary=0,
            conflicts=[],
            duplicates_ignored=0,
            merged_records=(),
            findings=[],
        )
        self.assertEqual(audit.exit_code(), 0)

    def test_exit_code_0_with_only_warnings(self) -> None:
        """Verify exit code is 0 when only warnings present (allowed)."""
        audit = DataAudit(
            total_official=1,
            total_auxiliary=0,
            conflicts=[],
            duplicates_ignored=0,
            merged_records=(),
            findings=[
                AuditFinding(
                    code="test_warning",
                    severity="warning",
                    message="Warning message",
                ),
            ],
        )
        self.assertEqual(audit.exit_code(), 0)

    def test_exit_code_1_with_error_finding(self) -> None:
        """Verify exit code is 1 when error finding present (data error)."""
        audit = DataAudit(
            total_official=1,
            total_auxiliary=0,
            conflicts=[],
            duplicates_ignored=0,
            merged_records=(),
            findings=[
                AuditFinding(
                    code="test_error",
                    severity="error",
                    message="Error message",
                ),
            ],
        )
        self.assertEqual(audit.exit_code(), 1)

    def test_exit_code_1_with_conflicts(self) -> None:
        """Verify exit code is 1 when conflicts present (data error)."""
        from bonoai.application.audit import ConflictRecord
        audit = DataAudit(
            total_official=1,
            total_auxiliary=1,
            conflicts=[
                ConflictRecord(
                    contest_id="test:2026-07-28",
                    official_numbers=(1, 2, 3, 4, 5, 6),
                    auxiliary_numbers=(7, 8, 9, 10, 11, 12),
                    official_source="official",
                    auxiliary_source="auxiliary",
                ),
            ],
            duplicates_ignored=0,
            merged_records=(),
            findings=[],
        )
        self.assertEqual(audit.exit_code(), 1)

    def test_exit_code_1_with_error_and_warning(self) -> None:
        """Verify error returns 1 even with warning also present."""
        audit = DataAudit(
            total_official=1,
            total_auxiliary=0,
            conflicts=[],
            duplicates_ignored=0,
            merged_records=(),
            findings=[
                AuditFinding(
                    code="warning_first",
                    severity="warning",
                    message="Warning",
                ),
                AuditFinding(
                    code="error_second",
                    severity="error",
                    message="Error",
                ),
            ],
        )
        self.assertEqual(audit.exit_code(), 1)


class AuditFindingsTests(TestCase):
    def test_audit_finding_to_dict(self) -> None:
        """Verify AuditFinding serialization."""
        finding = AuditFinding(
            code="test_code",
            severity="warning",
            message="Test message",
            contest_id="test:2026-07-28",
            source="test_source",
            details={"key": "value"},
        )
        result = finding.to_dict()
        self.assertEqual(result["code"], "test_code")
        self.assertEqual(result["severity"], "warning")
        self.assertEqual(result["message"], "Test message")
        self.assertEqual(result["contest_id"], "test:2026-07-28")
        self.assertEqual(result["source"], "test_source")
        self.assertEqual(result["details"], {"key": "value"})

    def test_audit_to_dict_with_findings(self) -> None:
        """Verify DataAudit serialization includes findings."""
        audit = DataAudit(
            total_official=1,
            total_auxiliary=0,
            conflicts=[],
            duplicates_ignored=0,
            merged_records=(),
            findings=[
                AuditFinding(
                    code="empty",
                    severity="warning",
                    message="No records",
                ),
            ],
        )
        result = audit.to_dict()
        self.assertIsInstance(result["findings"], list)
        findings = result["findings"]
        assert isinstance(findings, list)
        self.assertEqual(len(findings), 1)
        self.assertEqual(result["exit_code"], 0)


class AuditReconcileSourcesCoverageTests(TestCase):
    def test_reconcile_sources_with_duplicate_provenances_single_record(self) -> None:
        """Test provenances are not counted as duplicates when different."""
        numbers = (1, 2, 3, 4, 5, 6)
        held_on = date(2026, 7, 28)
        official = [
            make_record("test:2026-07-28", "official", "official", held_on, numbers)
        ]
        auxiliary = [
            make_record("test:2026-07-28", "auxiliary", "auxiliary", held_on, numbers)
        ]
        audit = reconcile_sources(official, auxiliary)
        self.assertEqual(len(audit.merged_records), 1)
        self.assertEqual(len(audit.merged_records[0].provenances), 2)
        self.assertEqual(audit.duplicates_ignored, 0)

    def test_reconcile_sources_multiple_auxiliary_sources_same_contest(self) -> None:
        """Test multiple auxiliary sources for same contest_id."""
        official: list[CanonicalDrawRecord] = []
        numbers = (1, 2, 3, 4, 5, 6)
        held_on = date(2026, 7, 27)
        aux1 = make_record("test:2026-07-27", "aux1", "auxiliary", held_on, numbers)
        aux2 = CanonicalDrawRecord(
            draw=aux1.draw,
            provenances=(
                SourceProvenance(
                    source_name="aux2",
                    source_url="https://example.test/other",
                    retrieved_at_utc=RETRIEVED_AT,
                    source_sha256="b" * 64,
                    source_type="auxiliary",
                    schema_version=2,
                ),
            ),
        )
        audit = reconcile_sources(official, [aux1, aux2])
        self.assertEqual(len(audit.merged_records), 1)
        self.assertEqual(len(audit.merged_records[0].provenances), 2)

    def test_reconcile_sources_truly_identical_provenances_counts_duplicate(self) -> None:
        """Test same provenance fingerprint is counted as duplicate."""
        numbers = (1, 2, 3, 4, 5, 6)
        held_on = date(2026, 7, 28)
        official = [
            make_record("test:2026-07-28", "selae", "official", held_on, numbers)
        ]
        auxiliary = [
            make_record("test:2026-07-28", "selae", "official", held_on, numbers)
        ]
        audit = reconcile_sources(official, auxiliary)
        self.assertEqual(audit.duplicates_ignored, 1)
        self.assertEqual(len(audit.merged_records[0].provenances), 1)

    def test_reconcile_sources_auxiliary_duplicate_only_same_provenance(self) -> None:
        """Test auxiliary records with duplicate provenance but new ones united."""
        numbers = (1, 2, 3, 4, 5, 6)
        held_on = date(2026, 7, 27)
        aux1 = make_record("test:2026-07-27", "aux1", "auxiliary", held_on, numbers)
        aux2 = CanonicalDrawRecord(
            draw=aux1.draw,
            provenances=(
                aux1.provenances[0],
                SourceProvenance(
                    source_name="aux2",
                    source_url="https://example.test/aux2",
                    retrieved_at_utc=RETRIEVED_AT,
                    source_sha256="c" * 64,
                    source_type="auxiliary",
                    schema_version=2,
                ),
            ),
        )
        audit = reconcile_sources([], [aux1, aux2])
        self.assertEqual(len(audit.merged_records), 1)
        self.assertEqual(len(audit.merged_records[0].provenances), 2)
        self.assertEqual(audit.duplicates_ignored, 1)
