"""Auditable CSV reader that captures errors without stopping."""

from __future__ import annotations

import csv
from pathlib import Path

from bonoai.application.audit_models import AuditInputError, AuditLoadResult
from bonoai.domain.data import CanonicalDrawRecord, DataContractError, SourceProvenance
from bonoai.domain.models import Draw


def read_csv_auditable(filepath: Path) -> AuditLoadResult:
    """Read CSV and return valid records plus input errors.

    Continues processing after encountering invalid rows.
    Does not relax CanonicalDrawRecord or SourceProvenance contracts.

    Args:
        filepath: Path to CSV file

    Returns:
        AuditLoadResult with valid records and parsing errors
    """
    records: list[CanonicalDrawRecord] = []
    errors: list[AuditInputError] = []

    try:
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise DataContractError("CSV header missing")

            for row_num, row in enumerate(reader, start=2):
                try:
                    contest_id = row.get("contest_id", "").strip()
                    if not contest_id:
                        errors.append(
                            AuditInputError(
                                code="invalid_record",
                                message=f"Row {row_num}: missing contest_id",
                                contest_id=None,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    held_on_str = row.get("held_on", "").strip()
                    if not held_on_str:
                        errors.append(
                            AuditInputError(
                                code="invalid_record",
                                message=f"Row {row_num}: missing held_on",
                                contest_id=contest_id,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    from datetime import date
                    held_on = date.fromisoformat(held_on_str)

                    numbers_str = row.get("numbers", "").strip()
                    if not numbers_str:
                        errors.append(
                            AuditInputError(
                                code="invalid_record",
                                message=f"Row {row_num}: missing numbers",
                                contest_id=contest_id,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    numbers = tuple(int(n) for n in numbers_str.split(";"))

                    complementary_str = row.get("complementary", "").strip()
                    if not complementary_str:
                        errors.append(
                            AuditInputError(
                                code="invalid_record",
                                message=f"Row {row_num}: missing complementary",
                                contest_id=contest_id,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    complementary = int(complementary_str)

                    reintegro_str = row.get("reintegro", "").strip()
                    if not reintegro_str:
                        errors.append(
                            AuditInputError(
                                code="invalid_record",
                                message=f"Row {row_num}: missing reintegro",
                                contest_id=contest_id,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    reintegro = int(reintegro_str)

                    source_name = row.get("source_name", "").strip()
                    if not source_name:
                        errors.append(
                            AuditInputError(
                                code="invalid_provenance",
                                message=f"Row {row_num}: empty source_name",
                                contest_id=contest_id,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    source_url = row.get("source_url", "").strip()
                    if not source_url:
                        errors.append(
                            AuditInputError(
                                code="invalid_record",
                                message=f"Row {row_num}: missing source_url",
                                contest_id=contest_id,
                                source="csv",
                                details={"row": row_num},
                            )
                        )
                        continue

                    source_sha256 = row.get("source_sha256", "a" * 64).strip()
                    source_type_str = row.get("source_type", "official").strip()

                    from datetime import UTC, datetime
                    retrieved_at_utc = datetime.now(UTC)

                    provenance = SourceProvenance(
                        source_name=source_name,
                        source_url=source_url,
                        retrieved_at_utc=retrieved_at_utc,
                        source_sha256=source_sha256,
                        source_type=source_type_str,  # type: ignore[arg-type]
                        schema_version=2,
                    )

                    draw = Draw(
                        contest_id=contest_id,
                        held_on=held_on,
                        numbers=numbers,
                        complementary=complementary,
                        reintegro=reintegro,
                    )

                    record = CanonicalDrawRecord(
                        draw=draw,
                        provenances=(provenance,),
                    )
                    records.append(record)

                except (ValueError, DataContractError) as e:
                    errors.append(
                        AuditInputError(
                            code="invalid_record",
                            message=f"Row {row_num}: {e!s}",
                            contest_id=contest_id if "contest_id" in locals() else None,
                            source="csv",
                            details={"row": row_num, "error": str(type(e).__name__)},
                        )
                    )

    except Exception as e:
        errors.append(
            AuditInputError(
                code="invalid_record",
                message=f"Failed to read CSV: {e!s}",
                contest_id=None,
                source="csv",
                details={"error": str(type(e).__name__)},
            )
        )

    return AuditLoadResult(records=tuple(records), errors=tuple(errors))
