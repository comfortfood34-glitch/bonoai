"""Provenance and payload integrity checks."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from bonoai.application.audit_models import AuditFinding
from bonoai.ports.data import RawPayloadReader

if TYPE_CHECKING:
    from bonoai.domain.data import CanonicalDrawRecord


def check_provenance_validity(
    record: CanonicalDrawRecord,
    prov: Any,
    findings: list[AuditFinding],
    raw_payload_reader: RawPayloadReader | None = None,
) -> None:
    """Check a single provenance for validity and payload integrity."""
    if prov.schema_version not in (1, 2):
        findings.append(
            AuditFinding(
                code="unknown_schema",
                severity="error",
                message=f"Unknown schema version: {prov.schema_version}",
                contest_id=record.draw.contest_id,
                source=prov.source_name,
                details={"schema_version": prov.schema_version},
            )
        )

    if not prov.source_name or not prov.source_name.strip():
        findings.append(
            AuditFinding(
                code="invalid_provenance",
                severity="error",
                message="Provenance has empty source_name",
                contest_id=record.draw.contest_id,
                source=prov.source_name or "unknown",
            )
        )

    if raw_payload_reader and prov.source_sha256:
        payload_bytes = raw_payload_reader.read_by_sha256(prov.source_sha256)
        if payload_bytes is None:
            findings.append(
                AuditFinding(
                    code="raw_payload_missing",
                    severity="warning",
                    message=f"Raw payload not found for SHA-256 {prov.source_sha256}",
                    contest_id=record.draw.contest_id,
                    source=prov.source_name,
                    details={"expected_sha256": prov.source_sha256},
                )
            )
        else:
            recalculated_sha = hashlib.sha256(payload_bytes).hexdigest()
            if recalculated_sha != prov.source_sha256:
                findings.append(
                    AuditFinding(
                        code="raw_payload_sha256_mismatch",
                        severity="error",
                        message="SHA-256 mismatch for payload",
                        contest_id=record.draw.contest_id,
                        source=prov.source_name,
                        details={
                            "expected": prov.source_sha256,
                            "calculated": recalculated_sha,
                        },
                    )
                )
