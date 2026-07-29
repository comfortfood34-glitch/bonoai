"""Canonical data contracts and ingestion errors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import urlparse

from bonoai.domain.models import Draw

CANONICAL_SCHEMA_VERSION: Final = 1
SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")


class DataContractError(ValueError):
    """Base error for invalid external or canonical data."""


class SourceConflictError(DataContractError):
    """Raised when the same contest identity has different results."""


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Minimum audit trail for one external payload."""

    source_name: str
    source_url: str
    retrieved_at_utc: datetime
    source_sha256: str
    schema_version: int = CANONICAL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.source_name.strip():
            raise DataContractError("source_name must not be empty")

        parsed_url = urlparse(self.source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise DataContractError("source_url must be an absolute HTTP(S) URL")

        if self.retrieved_at_utc.tzinfo is None:
            raise DataContractError("retrieved_at_utc must be timezone-aware")
        if self.retrieved_at_utc.utcoffset() != UTC.utcoffset(self.retrieved_at_utc):
            raise DataContractError("retrieved_at_utc must use UTC")

        if not SHA256_PATTERN.fullmatch(self.source_sha256):
            raise DataContractError("source_sha256 must be 64 lowercase hexadecimal characters")
        if self.schema_version != CANONICAL_SCHEMA_VERSION:
            raise DataContractError(
                f"unsupported schema version {self.schema_version}; "
                f"expected {CANONICAL_SCHEMA_VERSION}"
            )


@dataclass(frozen=True, slots=True)
class CanonicalDrawRecord:
    """A validated draw bound to its source provenance."""

    draw: Draw
    provenance: SourceProvenance
