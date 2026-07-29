"""Append-only filesystem archive for exact source payloads."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC
from pathlib import Path

from bonoai.domain.data import DataContractError
from bonoai.ports.data import FetchedDocument


class FilesystemRawArchive:
    """Store source bytes and metadata under deterministic retrieval paths."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def store(self, document: FetchedDocument) -> Path:
        digest = hashlib.sha256(document.payload).hexdigest()
        retrieved = document.retrieved_at_utc
        if retrieved.tzinfo is None or retrieved.utcoffset() != UTC.utcoffset(retrieved):
            raise DataContractError("raw document retrieval time must use UTC")

        directory = self._root / document.source_name / retrieved.strftime("%Y/%m/%d")
        stamp = retrieved.strftime("%Y%m%dT%H%M%S%fZ")
        payload_path = directory / f"{stamp}_{digest}.xml"
        manifest_path = payload_path.with_suffix(".json")
        directory.mkdir(parents=True, exist_ok=True)

        manifest = {
            "media_type": document.media_type,
            "retrieved_at_utc": retrieved.isoformat(),
            "size_bytes": len(document.payload),
            "source_name": document.source_name,
            "source_sha256": digest,
            "source_url": document.source_url,
        }
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode()

        self._write_once(payload_path, document.payload)
        self._write_once(manifest_path, manifest_bytes)
        return payload_path

    @staticmethod
    def _write_once(path: Path, content: bytes) -> None:
        try:
            with path.open("xb") as stream:
                stream.write(content)
                stream.flush()
        except FileExistsError:
            if path.read_bytes() != content:
                raise DataContractError(f"immutable raw archive collision at {path}") from None
