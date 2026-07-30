"""Strict tests for raw payload reader validation."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.infrastructure.raw_payload_reader import FilesystemRawPayloadReader


class RawPayloadReaderStrictTests(TestCase):
    """Test FilesystemRawPayloadReader error handling."""

    def test_reject_invalid_sha256_format_too_short(self) -> None:
        """Reject SHA-256 with invalid length."""
        reader = FilesystemRawPayloadReader(Path("/tmp"))
        with self.assertRaises(RuntimeError) as ctx:
            reader.read_by_sha256("abc123")
        self.assertIn("invalid SHA-256 format", str(ctx.exception))

    def test_reject_invalid_sha256_format_non_hex(self) -> None:
        """Reject SHA-256 with non-hex characters."""
        reader = FilesystemRawPayloadReader(Path("/tmp"))
        with self.assertRaises(RuntimeError) as ctx:
            reader.read_by_sha256("z" * 64)
        self.assertIn("invalid SHA-256 format", str(ctx.exception))

    def test_reject_invalid_sha256_uppercase(self) -> None:
        """Reject SHA-256 with uppercase hex characters."""
        reader = FilesystemRawPayloadReader(Path("/tmp"))
        with self.assertRaises(RuntimeError) as ctx:
            reader.read_by_sha256("A" * 64)
        self.assertIn("invalid SHA-256 format", str(ctx.exception))

    def test_reject_empty_sha256(self) -> None:
        """Reject empty SHA-256."""
        reader = FilesystemRawPayloadReader(Path("/tmp"))
        with self.assertRaises(RuntimeError) as ctx:
            reader.read_by_sha256("")
        self.assertIn("invalid SHA-256 format", str(ctx.exception))

    def test_reject_multiple_matching_files(self) -> None:
        """Reject when multiple files match SHA-256."""
        with TemporaryDirectory() as tmpdir:
            archive_root = Path(tmpdir)

            payload = b"test payload content"
            sha256_hash = hashlib.sha256(payload).hexdigest()

            archive_subdir1 = archive_root / "source1" / "2026" / "07" / "29"
            archive_subdir1.mkdir(parents=True)
            payload_file1 = archive_subdir1 / f"20260729T100000Z_{sha256_hash}.xml"
            payload_file1.write_bytes(payload)

            archive_subdir2 = archive_root / "source2" / "2026" / "07" / "29"
            archive_subdir2.mkdir(parents=True)
            payload_file2 = archive_subdir2 / f"20260729T100001Z_{sha256_hash}.xml"
            payload_file2.write_bytes(payload)

            reader = FilesystemRawPayloadReader(archive_root)
            with self.assertRaises(RuntimeError) as ctx:
                reader.read_by_sha256(sha256_hash)
            self.assertIn("multiple files", str(ctx.exception))

    def test_reject_filename_with_extra_chars_after_hash(self) -> None:
        """Reject file like TIMESTAMP_<hash>extra.xml."""
        with TemporaryDirectory() as tmpdir:
            archive_root = Path(tmpdir)

            payload = b"test payload content"
            sha256_hash = hashlib.sha256(payload).hexdigest()

            archive_subdir = archive_root / "test_source" / "2026" / "07" / "29"
            archive_subdir.mkdir(parents=True)

            payload_file = archive_subdir / f"20260729T100000Z_{sha256_hash}extra.xml"
            payload_file.write_bytes(payload)

            reader = FilesystemRawPayloadReader(archive_root)
            result = reader.read_by_sha256(sha256_hash)

            self.assertIsNone(result)
