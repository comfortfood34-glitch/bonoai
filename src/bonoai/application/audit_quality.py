"""Data quality checks: ordering, gaps, and coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bonoai.application.audit_models import AuditFinding, AuditPolicy

if TYPE_CHECKING:
    from bonoai.domain.data import CanonicalDrawRecord


def check_ordering(
    records_before_sort: list[CanonicalDrawRecord],
    findings: list[AuditFinding],
) -> None:
    """Detect if input records were not in chronological order."""
    if len(records_before_sort) < 2:
        return

    for i in range(len(records_before_sort) - 1):
        current_date = records_before_sort[i].draw.held_on
        next_date = records_before_sort[i + 1].draw.held_on
        if current_date > next_date:
            findings.append(
                AuditFinding(
                    code="incorrect_ordering",
                    severity="warning",
                    message="Input records not in chronological order; audit sorted them",
                    details={"out_of_order_pairs": i + 1},
                )
            )
            break


def check_date_gaps(
    sorted_records: tuple[CanonicalDrawRecord, ...],
    policy: AuditPolicy,
    findings: list[AuditFinding],
) -> None:
    """Detect suspicious gaps between consecutive draws."""
    if len(sorted_records) < 2:
        return

    for i in range(len(sorted_records) - 1):
        current_date = sorted_records[i].draw.held_on
        next_date = sorted_records[i + 1].draw.held_on
        gap_days = (next_date - current_date).days

        if gap_days > policy.suspicious_gap_days:
            findings.append(
                AuditFinding(
                    code="suspicious_date_gap",
                    severity="warning",
                    message=f"Suspicious gap of {gap_days} days detected",
                    details={
                        "from_date": current_date.isoformat(),
                        "to_date": next_date.isoformat(),
                        "gap_days": gap_days,
                        "threshold_days": policy.suspicious_gap_days,
                    },
                )
            )


def check_coverage(
    sorted_records: tuple[CanonicalDrawRecord, ...],
    policy: AuditPolicy,
    findings: list[AuditFinding],
) -> None:
    """Detect partial or incomplete historical coverage."""
    if not sorted_records or not policy.expected_start_date or not policy.expected_end_date:
        return

    first_date = sorted_records[0].draw.held_on
    last_date = sorted_records[-1].draw.held_on
    expected_span = (policy.expected_end_date - policy.expected_start_date).days
    actual_span = (last_date - first_date).days

    if first_date > policy.expected_start_date or last_date < policy.expected_end_date:
        findings.append(
            AuditFinding(
                code="partial_historical_coverage",
                severity="warning",
                message="Historical coverage is incomplete compared to expected range",
                details={
                    "expected_start": policy.expected_start_date.isoformat(),
                    "expected_end": policy.expected_end_date.isoformat(),
                    "actual_start": first_date.isoformat(),
                    "actual_end": last_date.isoformat(),
                    "expected_span_days": expected_span,
                    "actual_span_days": actual_span,
                },
            )
        )
