"""Tests for raw payload reader."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.infrastructure.raw_payload_reader import FilesystemRawPayloadReader


class RawPayloadReaderTests(TestCase):
    """Test FilesystemRawPayloadReader."""

    def test_read_by_sha256_found(self) -> None:
        """Test reading payload by SHA-256 when file exists."""
        with TemporaryDirectory() as tmpdir:
            archive_root = Path(tmpdir)

            payload = b"test payload content"
            sha256_hash = hashlib.sha256(payload).hexdigest()

            archive_subdir = archive_root / "test_source" / "2026" / "07" / "29"
            archive_subdir.mkdir(parents=True)
            payload_file = archive_subdir / f"20260729T100000Z_{sha256_hash}.xml"
            payload_file.write_bytes(payload)

            reader = FilesystemRawPayloadReader(archive_root)
            result = reader.read_by_sha256(sha256_hash)

            self.assertEqual(result, payload)

    def test_read_by_sha256_not_found(self) -> None:
        """Test read by SHA-256 when payload doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            archive_root = Path(tmpdir)
            reader = FilesystemRawPayloadReader(archive_root)
            result = reader.read_by_sha256("a" * 64)

            self.assertIsNone(result)

    def test_read_by_sha256_archive_root_not_exists(self) -> None:
        """Test read when archive root directory doesn't exist."""
        archive_root = Path("/nonexistent/path/archive")
        reader = FilesystemRawPayloadReader(archive_root)
        result = reader.read_by_sha256("a" * 64)

        self.assertIsNone(result)
