"""Data models for audit results and configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal


@dataclass(frozen=True)
class AuditInputError:
    """Captured input parsing error during audit."""

    code: Literal[
        "invalid_record",
        "unknown_schema",
        "missing_provenance",
        "invalid_provenance",
    ]
    message: str
    contest_id: str | None = None
    source: str | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class AuditLoadResult:
    """Result of loading and validating records from input."""

    records: tuple[Any, ...] = ()
    errors: tuple[AuditInputError, ...] = ()


@dataclass(frozen=True)
class AuditFinding:
    """A single audit finding with structured info."""

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    contest_id: str | None = None
    source: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize finding to dictionary."""
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "contest_id": self.contest_id,
            "source": self.source,
            "details": self.details,
        }


@dataclass(frozen=True)
class AuditPolicy:
    """Configuration for audit behavior."""

    suspicious_gap_days: int = 7
    expected_start_date: date | None = None
    expected_end_date: date | None = None


@dataclass(frozen=True)
class ConflictRecord:
    """Record of a data conflict between sources."""

    contest_id: str
    official_numbers: tuple[int, ...] | None
    auxiliary_numbers: tuple[int, ...] | None
    official_source: str | None
    auxiliary_source: str | None

    def to_dict(self) -> dict[str, object]:
        """Serialize conflict to dictionary."""
        return {
            "contest_id": self.contest_id,
            "official_numbers": list(self.official_numbers) if self.official_numbers else None,
            "auxiliary_numbers": list(self.auxiliary_numbers) if self.auxiliary_numbers else None,
            "official_source": self.official_source,
            "auxiliary_source": self.auxiliary_source,
        }


@dataclass(frozen=True)
class DataAudit:
    """Results of reconciling multiple data sources with findings."""

    total_official: int = 0
    total_auxiliary: int = 0
    total_manual: int = 0
    first_draw_date: str | None = None
    last_draw_date: str | None = None
    distribution_by_source: dict[str, int] = field(default_factory=dict)
    conflicts: list[ConflictRecord] = field(default_factory=list)
    duplicates_ignored: int = 0
    merged_records: tuple[Any, ...] = ()
    findings: list[AuditFinding] = field(default_factory=list)

    def has_conflicts(self) -> bool:
        """Check if reconciliation found any conflicting records."""
        return len(self.conflicts) > 0

    def exit_code(self) -> int:
        """Return CLI exit code: 0=ok (with warnings), 1=data error, 2=operational error."""
        for finding in self.findings:
            if finding.severity == "error":
                return 1
        if self.has_conflicts():
            return 1
        return 0

    def to_dict(self) -> dict[str, object]:
        """Serialize audit results to dictionary."""
        sorted_conflicts = sorted(self.conflicts, key=lambda c: c.contest_id)
        sorted_findings = sorted(self.findings, key=lambda f: (f.severity, f.code))
        return {
            "total_official": self.total_official,
            "total_auxiliary": self.total_auxiliary,
            "total_manual": self.total_manual,
            "first_draw_date": self.first_draw_date,
            "last_draw_date": self.last_draw_date,
            "distribution_by_source": self.distribution_by_source,
            "conflicts": [c.to_dict() for c in sorted_conflicts],
            "duplicates_ignored": self.duplicates_ignored,
            "merged_count": len(self.merged_records),
            "findings": [f.to_dict() for f in sorted_findings],
            "exit_code": self.exit_code(),
        }
