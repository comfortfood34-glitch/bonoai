"""Tests for CLI backtest subcommands with error paths."""

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


class TestCliBacktestCommands(TestCase):
    """Test CLI backtest commands error handling."""

    def setUp(self) -> None:
        """Set up test artifacts."""
        self.tmpdir = TemporaryDirectory()
        self.artifacts_dir = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def _create_run_with_hashes(self, run_id: str, avg_hits: float = 2.0) -> None:
        """Create run with valid SHA-256 hashes."""
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True)

        config = {"strategy_name": "uniform_random", "start_date": "2025-01-01"}
        config_bytes = json.dumps(config, sort_keys=True).encode("utf-8")
        config_hash = hashlib.sha256(config_bytes).hexdigest()
        with open(run_dir / "config.json", "wb") as f:
            f.write(config_bytes)

        metrics = {"average_hits": avg_hits, "hit_distribution": {0: 100}}
        metrics_bytes = json.dumps(metrics, sort_keys=True).encode("utf-8")
        metrics_hash = hashlib.sha256(metrics_bytes).hexdigest()
        with open(run_dir / "metrics.json", "wb") as f:
            f.write(metrics_bytes)

        manifest = {
            "run_id": run_id,
            "status": "success",
            "files": {"config.json": config_hash, "metrics.json": metrics_hash},
        }
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

    def test_list_runs_success(self) -> None:
        """List runs returns success."""
        self._create_run_with_hashes("run_001")
        self._create_run_with_hashes("run_002")

        result = list_runs(self.artifacts_dir)
        self.assertEqual(result.count, 2)
        self.assertEqual(len(result.run_ids), 2)

    def test_list_runs_empty(self) -> None:
        """List runs with no runs."""
        result = list_runs(self.artifacts_dir)
        self.assertEqual(result.count, 0)
        self.assertEqual(len(result.run_ids), 0)

    def test_show_run_success(self) -> None:
        """Show run returns complete data."""
        self._create_run_with_hashes("test_run", 3.0)

        result = show_run(self.artifacts_dir, "test_run")
        self.assertEqual(result.run_id, "test_run")
        self.assertIsNotNone(result.config)
        self.assertIsNotNone(result.metrics)
        self.assertIsNone(result.error)
        assert result.config is not None
        assert result.metrics is not None
        self.assertEqual(result.config["strategy_name"], "uniform_random")
        self.assertEqual(result.metrics["average_hits"], 3.0)

    def test_show_run_missing_config(self) -> None:
        """Show run when config missing returns error."""
        run_dir = self.artifacts_dir / "bad_run"
        run_dir.mkdir(parents=True)
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"average_hits": 1.0}, f)

        result = show_run(self.artifacts_dir, "bad_run")
        self.assertIsNotNone(result.error)

    def test_show_run_nonexistent(self) -> None:
        """Show run when run doesn't exist returns error."""
        result = show_run(self.artifacts_dir, "nonexistent")
        self.assertIsNotNone(result.error)

    def test_compare_runs_success(self) -> None:
        """Compare runs returns diff."""
        self._create_run_with_hashes("run_a", 1.0)
        self._create_run_with_hashes("run_b", 3.0)

        result = compare_runs(self.artifacts_dir, "run_a", "run_b")
        self.assertEqual(result.run_id_1, "run_a")
        self.assertEqual(result.run_id_2, "run_b")
        self.assertEqual(result.avg_diff, 2.0)
        self.assertIsNone(result.error)

    def test_compare_runs_first_missing(self) -> None:
        """Compare when first run missing returns error."""
        self._create_run_with_hashes("run_b", 3.0)

        result = compare_runs(self.artifacts_dir, "nonexistent", "run_b")
        self.assertIsNotNone(result.error)

    def test_compare_runs_second_missing(self) -> None:
        """Compare when second run missing returns error."""
        self._create_run_with_hashes("run_a", 1.0)

        result = compare_runs(self.artifacts_dir, "run_a", "nonexistent")
        self.assertIsNotNone(result.error)

    def test_verify_run_success(self) -> None:
        """Verify run with valid hashes succeeds."""
        self._create_run_with_hashes("test_run", 2.0)

        result = verify_run(self.artifacts_dir, "test_run")
        self.assertEqual(result.run_id, "test_run")
        self.assertTrue(result.valid)
        self.assertEqual(result.files_checked, 2)
        self.assertIsNone(result.error)

    def test_verify_run_missing_manifest(self) -> None:
        """Verify run without manifest returns error."""
        run_dir = self.artifacts_dir / "no_manifest"
        run_dir.mkdir(parents=True)
        with open(run_dir / "config.json", "w") as f:
            json.dump({"strategy_name": "test"}, f)
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"average_hits": 1.0}, f)

        result = verify_run(self.artifacts_dir, "no_manifest")
        self.assertIsNotNone(result.error)

    def test_verify_run_hash_mismatch(self) -> None:
        """Verify run with mismatched hash fails."""
        run_dir = self.artifacts_dir / "bad_hash"
        run_dir.mkdir(parents=True)

        config_content = b'{"strategy_name": "test"}'
        with open(run_dir / "config.json", "wb") as f:
            f.write(config_content)

        metrics_content = b'{"average_hits": 1.0}'
        with open(run_dir / "metrics.json", "wb") as f:
            f.write(metrics_content)

        # Manifest with wrong hashes
        manifest = {
            "run_id": "bad_hash",
            "status": "success",
            "files": {
                "config.json": "0" * 64,  # Wrong hash
                "metrics.json": "1" * 64,  # Wrong hash
            },
        }
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        result = verify_run(self.artifacts_dir, "bad_hash")
        self.assertFalse(result.valid)
        self.assertIsNone(result.error)

    def test_verify_run_nonexistent(self) -> None:
        """Verify run that doesn't exist returns error."""
        result = verify_run(self.artifacts_dir, "nonexistent")
        self.assertIsNotNone(result.error)
