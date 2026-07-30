"""Adapter to read raw evidence bytes from filesystem archive."""

from __future__ import annotations

import re
from pathlib import Path

from bonoai.ports.data import RawPayloadReader


class FilesystemRawPayloadReader(RawPayloadReader):
    """Read raw payloads from FilesystemRawArchive by SHA-256 digest."""

    def __init__(self, archive_root: Path) -> None:
        """Initialize reader pointing to raw archive root directory.

        Args:
            archive_root: Root directory of FilesystemRawArchive.
        """
        self._archive_root = archive_root

    def read_by_sha256(self, sha256: str) -> bytes | None:
        """Read raw bytes by SHA-256 digest.

        Validates SHA-256 format (64 lowercase hex chars).
        Searches archive_root for files matching FilesystemRawArchive contract:
        source_name/YYYY/MM/DD/TIMESTAMP_<sha256>.<extension>

        Filename contract: TIMESTAMP is ISO8601Z format, SHA-256 is extracted
        from position after underscore and before dot extension.

        Args:
            sha256: SHA-256 digest (lowercase hex, 64 chars).

        Returns:
            bytes if exactly one matching file found, None if not found.

        Raises:
            RuntimeError: if multiple matching files, SHA format invalid,
                         or file read error.
        """
        if not sha256 or len(sha256) != 64 or not all(c in "0123456789abcdef" for c in sha256):
            raise RuntimeError(f"invalid SHA-256 format: {sha256}")

        if not self._archive_root.exists():
            return None

        candidates = []

        for payload_path in self._archive_root.rglob("*"):
            if not payload_path.is_file() or payload_path.suffix == ".json":
                continue

            match = re.match(r".*_([a-f0-9]{64})(\..+)?$", payload_path.name)
            if match:
                extracted_sha = match.group(1)
                if extracted_sha == sha256:
                    candidates.append(payload_path)

        if len(candidates) == 0:
            return None

        candidates.sort(key=lambda p: p.name)

        if len(candidates) == 1:
            return candidates[0].read_bytes()

        raise RuntimeError(
            f"multiple files match SHA-256 {sha256}: {[str(p) for p in candidates]}"
        )
