"""Tests for audit_integrity missing branches."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.audit_integrity import check_provenance_validity
from bonoai.application.audit_models import AuditFinding
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw


class TestAuditIntegrityMissing(TestCase):
    """Test audit_integrity error paths."""

    def _make_record(self, contest_id: str = "1") -> CanonicalDrawRecord:
        """Create a test record."""
        draw = Draw(
            contest_id=contest_id,
            held_on=date(2025, 1, 1),
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=0,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            
        )
        return CanonicalDrawRecord(draw=draw, provenance=provenance,))

    def test_unknown_schema_version(self) -> None:
        """Check provenance with unknown schema version."""
        record = self._make_record()
        prov = type('Provenance', (), {
            'schema_version': 99,  # Unknown version
            'source_name': 'test',
            'source_url': 'https://test.com',
            'source_sha256': 'a' * 64,
        })()

        findings: list[AuditFinding] = []
        check_provenance_validity(record, prov, findings)

        unknown_schema_findings = [f for f in findings if f.code == "unknown_schema"]
        self.assertEqual(len(unknown_schema_findings), 1)
        self.assertIn("Unknown schema version", unknown_schema_findings[0].message)

    def test_empty_source_name(self) -> None:
        """Check provenance with empty source_name."""
        record = self._make_record()
        prov = type('Provenance', (), {
            'schema_version': 1,
            'source_name': '',  # Empty
            'source_url': 'https://test.com',
            'source_sha256': 'a' * 64,
        })()

        findings: list[AuditFinding] = []
        check_provenance_validity(record, prov, findings)

        invalid_prov_findings = [f for f in findings if f.code == "invalid_provenance"]
        self.assertEqual(len(invalid_prov_findings), 1)
        self.assertIn("empty source_name", invalid_prov_findings[0].message)

    def test_whitespace_only_source_name(self) -> None:
        """Check provenance with whitespace-only source_name."""
        record = self._make_record()
        prov = type('Provenance', (), {
            'schema_version': 1,
            'source_name': '   ',  # Whitespace only
            'source_url': 'https://test.com',
            'source_sha256': 'a' * 64,
        })()

        findings: list[AuditFinding] = []
        check_provenance_validity(record, prov, findings)

        invalid_prov_findings = [f for f in findings if f.code == "invalid_provenance"]
        self.assertEqual(len(invalid_prov_findings), 1)
