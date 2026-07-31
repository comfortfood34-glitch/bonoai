"""Tests for backtest query operations - pure business logic."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.backtest_queries import (
    compare_runs,
    list_runs,
    show_run,
    verify_run,
)


class TestListRuns(TestCase):
    """Test list_runs functionality."""

    def test_list_empty_directory(self) -> None:
        """Return empty list for nonexistent directory."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            result = list_runs(artifacts)
            self.assertEqual(result.count, 0)
            self.assertEqual(result.run_ids, [])

    def test_list_nonexistent_path(self) -> None:
        """Return empty list when path doesn't exist."""
        nonexistent = Path("/tmp/nonexistent_path_xyz_abc_123")
        result = list_runs(nonexistent)
        self.assertEqual(result.count, 0)
        self.assertEqual(result.run_ids, [])

    def test_list_single_run(self) -> None:
        """List single run."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "run1"
            run_dir.mkdir()
            with open(run_dir / "manifest.json", "w") as f:
                json.dump({"run_id": "run1"}, f)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 1)
            self.assertEqual(result.run_ids, ["run1"])

    def test_list_multiple_runs(self) -> None:
        """List multiple runs, sorted."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for i in range(5):
                run_dir = artifacts / f"run{i}"
                run_dir.mkdir()
                with open(run_dir / "manifest.json", "w") as f:
                    json.dump({"run_id": f"run{i}"}, f)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 5)
            self.assertEqual(len(result.run_ids), 5)
            self.assertIn("run0", result.run_ids)
            self.assertIn("run4", result.run_ids)

    def test_list_more_than_ten_runs(self) -> None:
        """List respects 10-run limit in run_ids."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for i in range(15):
                run_dir = artifacts / f"run{i:02d}"
                run_dir.mkdir()
                with open(run_dir / "manifest.json", "w") as f:
                    json.dump({"run_id": f"run{i:02d}"}, f)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 15)
            self.assertEqual(len(result.run_ids), 10)

    def test_list_ignores_non_manifest_files(self) -> None:
        """Only count directories with manifest.json."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "run1"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)

            other_dir = artifacts / "other"
            other_dir.mkdir()

            result = list_runs(artifacts)
            self.assertEqual(result.count, 0)
            self.assertEqual(result.run_ids, [])


class TestShowRun(TestCase):
    """Test show_run functionality."""

    def test_show_valid_run(self) -> None:
        """Show run with config and metrics."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "uniform_random"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 2.5}, f)

            result = show_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            assert result.config is not None
            assert result.metrics is not None
            self.assertEqual(result.config["strategy_name"], "uniform_random")
            self.assertEqual(result.metrics["average_hits"], 2.5)
            self.assertIsNone(result.error)

    def test_show_run_missing_config(self) -> None:
        """Return error when config missing."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = show_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertIsNone(result.config)
            self.assertIsNone(result.metrics)
            self.assertIsNotNone(result.error)
            assert result.error is not None
            self.assertIn("config not found", result.error)

    def test_show_run_missing_metrics_tolerant(self) -> None:
        """Metrics optional if config exists."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)

            result = show_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            assert result.config is not None
            self.assertEqual(result.config["strategy_name"], "test")
            self.assertIsNone(result.metrics)
            self.assertIsNone(result.error)

    def test_show_run_corrupt_config_json(self) -> None:
        """Return error for corrupt config JSON."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                f.write("{invalid json}")
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = show_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertIsNone(result.config)
            self.assertIsNone(result.metrics)
            self.assertIsNotNone(result.error)

    def test_show_run_corrupt_metrics_json(self) -> None:
        """Return error for corrupt metrics JSON."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                f.write("{invalid}")

            result = show_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertIsNone(result.config)
            self.assertIsNone(result.metrics)
            self.assertIsNotNone(result.error)

    def test_show_nonexistent_run(self) -> None:
        """Return error for nonexistent run."""
        with TemporaryDirectory() as tmpdir:
            result = show_run(Path(tmpdir), "nonexistent")
            self.assertEqual(result.run_id, "nonexistent")
            self.assertIsNone(result.config)
            self.assertIsNone(result.metrics)
            self.assertIsNotNone(result.error)


class TestCompareRuns(TestCase):
    """Test compare_runs functionality."""

    def test_compare_both_runs_exist(self) -> None:
        """Compare two valid runs."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for run_id in ["run1", "run2"]:
                run_dir = artifacts / run_id
                run_dir.mkdir()
                with open(run_dir / "metrics.json", "w") as f:
                    json.dump({"average_hits": 1.5 if run_id == "run1" else 2.5}, f)

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.run_id_1, "run1")
            self.assertEqual(result.run_id_2, "run2")
            self.assertEqual(result.avg_diff, 1.0)
            self.assertIsNone(result.error)

    def test_compare_run1_missing(self) -> None:
        """Return error when run1 missing."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "run2"
            run_dir.mkdir()
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 2.5}, f)

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.run_id_1, "run1")
            self.assertEqual(result.run_id_2, "run2")
            self.assertEqual(result.avg_diff, 0.0)
            self.assertIsNotNone(result.error)
            assert result.error is not None
            self.assertIn("run 1 not found", result.error)

    def test_compare_run2_missing(self) -> None:
        """Return error when run2 missing."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "run1"
            run_dir.mkdir()
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.5}, f)

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.run_id_1, "run1")
            self.assertEqual(result.run_id_2, "run2")
            self.assertEqual(result.avg_diff, 0.0)
            self.assertIsNotNone(result.error)
            assert result.error is not None
            self.assertIn("run 2 not found", result.error)

    def test_compare_both_missing(self) -> None:
        """Return error when both runs missing."""
        with TemporaryDirectory() as tmpdir:
            result = compare_runs(Path(tmpdir), "run1", "run2")
            self.assertEqual(result.run_id_1, "run1")
            self.assertEqual(result.run_id_2, "run2")
            self.assertEqual(result.avg_diff, 0.0)
            self.assertIsNotNone(result.error)

    def test_compare_with_missing_average_hits(self) -> None:
        """Handle missing average_hits field (default to 0.0)."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for i, run_id in enumerate(["run1", "run2"]):
                run_dir = artifacts / run_id
                run_dir.mkdir()
                with open(run_dir / "metrics.json", "w") as f:
                    if i == 0:
                        json.dump({"average_hits": 2.0}, f)
                    else:
                        json.dump({"some_other_metric": 1.0}, f)

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.avg_diff, -2.0)
            self.assertIsNone(result.error)

    def test_compare_both_missing_average_hits(self) -> None:
        """Both runs missing average_hits defaults to 0.0 diff."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for run_id in ["run1", "run2"]:
                run_dir = artifacts / run_id
                run_dir.mkdir()
                with open(run_dir / "metrics.json", "w") as f:
                    json.dump({"other_field": 1.0}, f)

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.avg_diff, 0.0)
            self.assertIsNone(result.error)

    def test_compare_corrupt_metrics_file(self) -> None:
        """Return error for corrupt metrics file."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for run_id in ["run1", "run2"]:
                run_dir = artifacts / run_id
                run_dir.mkdir()
                with open(run_dir / "metrics.json", "w") as f:
                    if run_id == "run1":
                        json.dump({"average_hits": 1.5}, f)
                    else:
                        f.write("{corrupt}")

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.avg_diff, 0.0)
            self.assertIsNotNone(result.error)

    def test_compare_negative_difference(self) -> None:
        """Calculate negative difference correctly."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for run_id, hits in [("run1", 3.5), ("run2", 1.5)]:
                run_dir = artifacts / run_id
                run_dir.mkdir()
                with open(run_dir / "metrics.json", "w") as f:
                    json.dump({"average_hits": hits}, f)

            result = compare_runs(artifacts, "run1", "run2")
            self.assertEqual(result.avg_diff, -2.0)
            self.assertIsNone(result.error)


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
