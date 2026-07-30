"""Tests for AuditInputError conversion to AuditFinding."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.audit import reconcile_sources
from bonoai.application.audit_models import AuditInputError
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_record(
    contest_id: str,
    held_on: date,
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
                source_type="official",
                schema_version=2,
            ),
        ),
    )


class AuditInputErrorsTest(TestCase):
    """Test conversion of AuditInputError to AuditFinding."""

    def test_input_errors_converted_to_findings(self) -> None:
        """Input parsing errors are converted to AuditFinding with error severity."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]

        input_error = AuditInputError(
            code="invalid_record",
            message="Row 5: missing numbers field",
            contest_id=None,
            source="csv",
            details={"row": 5},
        )

        audit = reconcile_sources(official, None, None, None, [input_error])

        codes = {finding.code for finding in audit.findings}
        self.assertIn("invalid_record", codes)

        invalid_finding = next(
            f for f in audit.findings if f.code == "invalid_record"
        )
        self.assertEqual(invalid_finding.severity, "error")
        self.assertEqual(invalid_finding.source, "csv")
        self.assertIn("Row 5", invalid_finding.message)

    def test_multiple_input_errors(self) -> None:
        """Multiple input errors are all converted to findings."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]

        error1 = AuditInputError(
            code="invalid_record",
            message="Row 3: missing contest_id",
            contest_id=None,
            source="csv",
        )
        error2 = AuditInputError(
            code="missing_provenance",
            message="Row 7: missing provenance",
            contest_id="loteria:2026-07-27",
            source="csv",
        )

        audit = reconcile_sources(official, None, None, None, [error1, error2])

        codes = {finding.code for finding in audit.findings}
        self.assertIn("invalid_record", codes)
        self.assertIn("missing_provenance", codes)
        self.assertEqual(len(audit.findings), 2)

    def test_input_errors_with_details(self) -> None:
        """Input errors preserve details dict in findings."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]

        input_error = AuditInputError(
            code="unknown_schema",
            message="Unknown schema version 99",
            contest_id="bonoloto:2026-07-27",
            source="source_a",
            details={"schema_version": 99, "expected": [1, 2]},
        )

        audit = reconcile_sources(official, None, None, None, [input_error])

        finding = next(f for f in audit.findings if f.code == "unknown_schema")
        self.assertEqual(finding.details, {"schema_version": 99, "expected": [1, 2]})

    def test_input_errors_all_codes(self) -> None:
        """All four AuditInputError codes are properly handled."""
        official = [make_record("bonoloto:2026-07-27", date(2026, 7, 27))]

        errors = [
            AuditInputError(
                code="invalid_record",
                message="Row 1: invalid",
                contest_id=None,
                source="csv",
            ),
            AuditInputError(
                code="unknown_schema",
                message="Row 2: schema 99",
                contest_id=None,
                source="csv",
            ),
            AuditInputError(
                code="missing_provenance",
                message="Row 3: no provenance",
                contest_id="bonoloto:2026-07-27",
                source="csv",
            ),
            AuditInputError(
                code="invalid_provenance",
                message="Row 4: empty source",
                contest_id="bonoloto:2026-07-27",
                source="csv",
            ),
        ]

        audit = reconcile_sources(official, None, None, None, errors)

        codes = {finding.code for finding in audit.findings}
        self.assertIn("invalid_record", codes)
        self.assertIn("unknown_schema", codes)
        self.assertIn("missing_provenance", codes)
        self.assertIn("invalid_provenance", codes)
