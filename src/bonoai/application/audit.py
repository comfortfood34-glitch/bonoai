"""Data quality audit and reconciliation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from bonoai.application.audit_integrity import check_provenance_validity
from bonoai.application.audit_models import (
    AuditFinding,
    AuditInputError,
    AuditPolicy,
    ConflictRecord,
    DataAudit,
)
from bonoai.application.audit_quality import check_coverage, check_date_gaps, check_ordering
from bonoai.domain.data import CanonicalDrawRecord
from bonoai.ports.data import RawPayloadReader

__all__ = [
    "AuditFinding",
    "AuditPolicy",
    "ConflictRecord",
    "DataAudit",
    "reconcile_sources",
]


def reconcile_sources(
    official: Iterable[CanonicalDrawRecord],
    auxiliary: Iterable[CanonicalDrawRecord] | None = None,
    raw_payload_reader: RawPayloadReader | None = None,
    audit_policy: AuditPolicy | None = None,
    input_errors: Iterable[AuditInputError] | None = None,
) -> DataAudit:
    """Reconcile official and auxiliary data sources, collecting all findings.

    Returns DataAudit with merged records and comprehensive audit findings.
    Does not raise exceptions for conflicts; instead collects them in findings.

    Args:
        official: Canonical records from official source (SELAE).
        auxiliary: Optional records from auxiliary sources (historical).
        raw_payload_reader: Optional reader to validate SHA-256 checksums.
        audit_policy: Optional policy for audit thresholds and expectations.
        input_errors: Optional input parsing errors to convert to findings.

    Returns:
        DataAudit with reconciliation results and comprehensive audit findings.
    """
    if audit_policy is None:
        audit_policy = AuditPolicy()

    official_records = tuple(official)
    auxiliary_records = tuple(auxiliary) if auxiliary else ()
    input_error_list = tuple(input_errors) if input_errors else ()

    official_by_id: dict[str, CanonicalDrawRecord] = {}
    date_by_contest: dict[str, str] = {}
    source_type_counts: Counter[str] = Counter()
    findings: list[AuditFinding] = []
    conflicts: list[ConflictRecord] = []

    all_records = list(official_records) + list(auxiliary_records)
    all_records_before_sort = all_records.copy()

    for record in official_records:
        contest_id = record.draw.contest_id
        held_on = record.draw.held_on.isoformat()

        if contest_id in official_by_id:
            if official_by_id[contest_id].draw == record.draw:
                findings.append(
                    AuditFinding(
                        code="duplicate_contest_id",
                        severity="warning",
                        message=f"Duplicate contest_id {contest_id} with identical draw",
                        contest_id=contest_id,
                        details={"held_on": held_on},
                    )
                )
            else:
                conflicts.append(
                    ConflictRecord(
                        contest_id=contest_id,
                        official_numbers=official_by_id[contest_id].draw.numbers,
                        auxiliary_numbers=record.draw.numbers,
                        official_source=official_by_id[contest_id].provenance.source_name,
                        auxiliary_source=record.provenance.source_name,
                    )
                )
                findings.append(
                    AuditFinding(
                        code="conflicting_draw",
                        severity="error",
                        message=f"Conflicting results for {contest_id}",
                        contest_id=contest_id,
                        details={
                            "official_numbers": list(official_by_id[contest_id].draw.numbers),
                            "auxiliary_numbers": list(record.draw.numbers),
                        },
                    )
                )
        else:
            if held_on in date_by_contest.values():
                for existing_id, existing_date in date_by_contest.items():
                    if existing_date == held_on and existing_id != contest_id:
                        findings.append(
                            AuditFinding(
                                code="duplicate_draw_date",
                                severity="info",
                                message=f"Multiple contests on same date {held_on}",
                                contest_id=contest_id,
                                details={
                                    "held_on": held_on,
                                    "other_contest": existing_id,
                                },
                            )
                        )
                        break
            date_by_contest[contest_id] = held_on
            official_by_id[contest_id] = record
        for prov in record.provenances:
            source_type_counts[prov.source_type] += 1
            check_provenance_validity(record, prov, findings, raw_payload_reader)

    auxiliary_by_id: dict[str, CanonicalDrawRecord] = {}
    duplicates = 0

    for aux_record in auxiliary_records:
        contest_id = aux_record.draw.contest_id
        for prov in aux_record.provenances:
            source_type_counts[prov.source_type] += 1
            check_provenance_validity(aux_record, prov, findings, raw_payload_reader)

        if contest_id in official_by_id:
            official_record = official_by_id[contest_id]
            if official_record.draw != aux_record.draw:
                conflicts.append(
                    ConflictRecord(
                        contest_id=contest_id,
                        official_numbers=official_record.draw.numbers,
                        auxiliary_numbers=aux_record.draw.numbers,
                        official_source=official_record.provenance.source_name,
                        auxiliary_source=aux_record.provenance.source_name,
                    )
                )
                findings.append(
                    AuditFinding(
                        code="conflicting_draw",
                        severity="error",
                        message=f"Conflicting results for {contest_id}",
                        contest_id=contest_id,
                        details={
                            "official_numbers": list(official_record.draw.numbers),
                            "auxiliary_numbers": list(aux_record.draw.numbers),
                        },
                    )
                )
            else:
                existing_fingerprints = {
                    prov.fingerprint() for prov in official_record.provenances
                }
                all_duplicate = all(
                    prov.fingerprint() in existing_fingerprints
                    for prov in aux_record.provenances
                )
                if all_duplicate:
                    duplicates += 1
                else:
                    for prov in aux_record.provenances:
                        if prov.fingerprint() not in existing_fingerprints:
                            official_by_id[contest_id] = CanonicalDrawRecord(
                                draw=official_record.draw,
                                provenances=tuple(
                                    sorted(
                                        (*official_record.provenances, prov),
                                        key=lambda p: p.fingerprint(),
                                    )
                                ),
                            )
                            official_record = official_by_id[contest_id]
        else:
            if contest_id not in auxiliary_by_id:
                auxiliary_by_id[contest_id] = aux_record
            else:
                existing_aux = auxiliary_by_id[contest_id]
                if existing_aux.draw == aux_record.draw:
                    existing_fp = {
                        prov.fingerprint() for prov in existing_aux.provenances
                    }
                    new_aux_prov = []
                    for prov in aux_record.provenances:
                        if prov.fingerprint() not in existing_fp:
                            new_aux_prov.append(prov)
                        else:
                            duplicates += 1

                    if new_aux_prov:
                        merged_prov_aux = tuple(
                            sorted(
                                (*existing_aux.provenances, *new_aux_prov),
                                key=lambda p: p.fingerprint(),
                            )
                        )
                        auxiliary_by_id[contest_id] = CanonicalDrawRecord(
                            draw=existing_aux.draw,
                            provenances=merged_prov_aux,
                        )
                else:
                    conflicts.append(
                        ConflictRecord(
                            contest_id=contest_id,
                            official_numbers=None,
                            auxiliary_numbers=aux_record.draw.numbers,
                            official_source=None,
                            auxiliary_source=aux_record.provenance.source_name,
                        )
                    )
                    findings.append(
                        AuditFinding(
                            code="conflicting_draw",
                            severity="error",
                            message=f"Conflicting results for {contest_id}",
                            contest_id=contest_id,
                            details={
                                "official_numbers": None,
                                "auxiliary_numbers": list(aux_record.draw.numbers),
                            },
                        )
                    )

    check_ordering(all_records_before_sort, findings)

    merged = list(official_by_id.values())
    merged.extend(auxiliary_by_id.values())
    merged_sorted = tuple(sorted(merged, key=lambda r: r.draw.held_on))

    check_date_gaps(merged_sorted, audit_policy, findings)
    check_coverage(merged_sorted, audit_policy, findings)

    if duplicates > 0:
        findings.append(
            AuditFinding(
                code="duplicate_provenance",
                severity="info",
                message=f"{duplicates} duplicate provenance entries ignored",
            )
        )

    for input_error in input_error_list:
        findings.append(
            AuditFinding(
                code=input_error.code,
                severity="error",
                message=input_error.message,
                contest_id=input_error.contest_id,
                source=input_error.source,
                details=input_error.details,
            )
        )

    first_draw_date = None
    last_draw_date = None
    if merged_sorted:
        first_draw_date = merged_sorted[0].draw.held_on.isoformat()
        last_draw_date = merged_sorted[-1].draw.held_on.isoformat()
    else:
        findings.append(
            AuditFinding(
                code="empty_repository",
                severity="warning",
                message="No records found in any source",
            )
        )

    findings.sort(key=lambda f: (f.severity, f.code))

    return DataAudit(
        total_official=len(official_records),
        total_auxiliary=len(auxiliary_records),
        first_draw_date=first_draw_date,
        last_draw_date=last_draw_date,
        distribution_by_source=dict(source_type_counts),
        conflicts=conflicts,
        duplicates_ignored=duplicates,
        merged_records=merged_sorted,
        findings=findings,
    )
