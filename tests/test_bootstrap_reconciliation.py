"""Tests for data reconciliation and audit logic."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.audit import ConflictRecord, reconcile_sources
from bonoai.domain.data import (
    CanonicalDrawRecord,
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_official(
    contest_id: str,
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
                source_name="selae",
                source_url="https://www.selae.es/lotobonoloto",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="a" * 64,
                source_type="official",
                schema_version=2,
            ),
        ),
    )


def make_auxiliary(
    contest_id: str,
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
                source_name="lotoideas",
                source_url="https://example.test/historical",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="b" * 64,
                source_type="auxiliary",
                schema_version=2,
            ),
        ),
    )


class ReconcilationTests(TestCase):
    def test_merges_official_and_auxiliary_with_no_overlap(self) -> None:
        official = [make_official(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]
        auxiliary = [make_auxiliary(
            "bonoloto:2026-07-27", date(2026, 7, 27), (10, 20, 30, 40, 45, 49)
        )]

        audit = reconcile_sources(official, auxiliary)

        self.assertEqual(len(audit.merged_records), 2)
        self.assertEqual(audit.total_official, 1)
        self.assertEqual(audit.total_auxiliary, 1)
        self.assertFalse(audit.has_conflicts())

    def test_detects_conflict_when_same_contest_has_different_numbers(self) -> None:
        official = [make_official(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]
        auxiliary = [make_auxiliary(
            "bonoloto:2026-07-28", date(2026, 7, 28), (7, 8, 9, 10, 11, 12)
        )]

        with self.assertRaisesRegex(SourceConflictError, "conflicting result"):
            reconcile_sources(official, auxiliary)

    def test_ignores_identical_duplicates(self) -> None:
        official = [make_official(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]
        auxiliary = [make_auxiliary(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]

        audit = reconcile_sources(official, auxiliary)

        self.assertEqual(len(audit.merged_records), 1)
        self.assertEqual(audit.duplicates_ignored, 1)
        self.assertFalse(audit.has_conflicts())

    def test_reconcile_with_none_auxiliary(self) -> None:
        official = [make_official(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]

        audit = reconcile_sources(official, None)

        self.assertEqual(len(audit.merged_records), 1)
        self.assertEqual(audit.total_official, 1)
        self.assertEqual(audit.total_auxiliary, 0)

    def test_conflict_record_serialization(self) -> None:
        conflict = ConflictRecord(
            contest_id="bonoloto:2026-07-28",
            official_numbers=(1, 2, 3, 4, 5, 6),
            auxiliary_numbers=(7, 8, 9, 10, 11, 12),
            official_source="selae",
            auxiliary_source="lotoideas",
        )

        result = conflict.to_dict()

        self.assertEqual(result["contest_id"], "bonoloto:2026-07-28")
        self.assertEqual(result["official_numbers"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result["auxiliary_numbers"], [7, 8, 9, 10, 11, 12])

    def test_audit_serialization(self) -> None:
        official = [make_official(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]
        audit = reconcile_sources(official, None)

        result = audit.to_dict()

        self.assertEqual(result["total_official"], 1)
        self.assertEqual(result["total_auxiliary"], 0)
        self.assertEqual(result["merged_count"], 1)
        self.assertFalse(result["conflicts"])

    def test_detects_conflict_between_two_auxiliary_sources(self) -> None:
        official: list[CanonicalDrawRecord] = []
        aux1 = make_auxiliary(
            "bonoloto:2026-07-27", date(2026, 7, 27), (1, 2, 3, 4, 5, 6)
        )
        aux2 = CanonicalDrawRecord(
            draw=Draw(
                contest_id="bonoloto:2026-07-27",
                held_on=date(2026, 7, 27),
                numbers=(7, 8, 9, 10, 11, 12),
                complementary=13,
                reintegro=1,
            ),
            provenances=(
                SourceProvenance(
                    source_name="other_source",
                    source_url="https://example.test/other",
                    retrieved_at_utc=RETRIEVED_AT,
                    source_sha256="c" * 64,
                    source_type="auxiliary",
                    schema_version=2,
                ),
            ),
        )

        with self.assertRaisesRegex(SourceConflictError, "conflicting result"):
            reconcile_sources(official, [aux1, aux2])

    def test_audit_tracks_all_findings(self) -> None:
        official = [make_official(
            "bonoloto:2026-07-28", date(2026, 7, 28), (1, 2, 3, 4, 5, 6)
        )]
        auxiliary = [make_auxiliary(
            "bonoloto:2026-07-27", date(2026, 7, 27), (10, 20, 30, 40, 45, 49)
        )]

        audit = reconcile_sources(official, auxiliary)

        self.assertEqual(audit.total_official, 1)
        self.assertEqual(audit.total_auxiliary, 1)
        self.assertEqual(len(audit.merged_records), 2)
        self.assertFalse(audit.has_conflicts())
