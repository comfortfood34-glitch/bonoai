"""Tests for backtest query verify operation."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.backtest_queries import verify_run


class TestVerifyRun(TestCase):
    """Test verify_run integrity checking."""

    def test_verify_valid_run(self) -> None:
        """Verify run with matching hashes."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            config_data = {"strategy_name": "test"}
            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)

            config_hash = hashlib.sha256(
                json.dumps(config_data, sort_keys=True).encode()
            ).hexdigest()

            manifest = {
                "run_id": "test_run",
                "files": {
                    "config.json": config_hash,
                },
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertTrue(result.valid)
            self.assertEqual(result.files_checked, 1)
            self.assertEqual(result.failed_files, [])
            self.assertIsNone(result.error)

    def test_verify_manifest_missing(self) -> None:
        """Return error when manifest missing."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertFalse(result.valid)
            self.assertEqual(result.files_checked, 0)
            self.assertEqual(result.failed_files, [])
            self.assertIsNotNone(result.error)
            assert result.error is not None
            self.assertIn("manifest not found", result.error)

    def test_verify_file_missing(self) -> None:
        """Mark file as missing in verification."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            manifest = {
                "run_id": "test_run",
                "files": {
                    "config.json": "abc123",
                },
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertFalse(result.valid)
            self.assertEqual(result.files_checked, 1)
            self.assertEqual(len(result.failed_files), 1)
            self.assertIn("missing", result.failed_files[0])
            self.assertIsNone(result.error)

    def test_verify_hash_mismatch(self) -> None:
        """Detect hash mismatch."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)

            manifest = {
                "run_id": "test_run",
                "files": {
                    "config.json": "wronghash",
                },
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertFalse(result.valid)
            self.assertEqual(result.files_checked, 1)
            self.assertEqual(len(result.failed_files), 1)
            self.assertIn("hash mismatch", result.failed_files[0])

    def test_verify_multiple_files_mixed_results(self) -> None:
        """Verify multiple files with mixed results."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            config_data = {"strategy_name": "test"}
            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)

            config_hash = hashlib.sha256(
                json.dumps(config_data, sort_keys=True).encode()
            ).hexdigest()

            manifest = {
                "run_id": "test_run",
                "files": {
                    "config.json": config_hash,
                    "metrics.json": "expected_hash",
                    "missing_file.json": "some_hash",
                },
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertFalse(result.valid)
            self.assertEqual(result.files_checked, 3)
            self.assertEqual(len(result.failed_files), 2)

    def test_verify_empty_files_dict(self) -> None:
        """Handle empty files dict in manifest."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            manifest = {
                "run_id": "test_run",
                "files": {},
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertTrue(result.valid)
            self.assertEqual(result.files_checked, 0)
            self.assertEqual(result.failed_files, [])

    def test_verify_corrupt_manifest_json(self) -> None:
        """Return error for corrupt manifest JSON."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            with open(run_dir / "manifest.json", "w") as f:
                f.write("{invalid json")

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertFalse(result.valid)
            self.assertEqual(result.files_checked, 0)
            self.assertEqual(result.failed_files, [])
            self.assertIsNotNone(result.error)

    def test_verify_manifest_missing_files_key(self) -> None:
        """Handle manifest without files key."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()

            manifest = {
                "run_id": "test_run",
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertTrue(result.valid)
            self.assertEqual(result.files_checked, 0)
            self.assertEqual(result.failed_files, [])
