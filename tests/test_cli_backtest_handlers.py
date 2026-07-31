"""Tests for CLI backtest handler functions."""

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


class TestCliBacktestHandlers(TestCase):
    """Test CLI backtest handler functions using business logic."""

    def setUp(self) -> None:
        """Set up test artifacts."""
        self.tmpdir = TemporaryDirectory()
        self.artifacts_dir = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def _create_run(self, run_id: str, avg_hits: float = 2.0) -> None:
        """Create a sample run."""
        import hashlib
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

    def test_list_runs_handler(self) -> None:
        """Test list runs handler."""
        self._create_run("run_001")
        self._create_run("run_002")

        result = list_runs(self.artifacts_dir)
        self.assertEqual(result.count, 2)
        self.assertIn("run_001", result.run_ids)
        self.assertIn("run_002", result.run_ids)

    def test_show_run_handler(self) -> None:
        """Test show run handler."""
        self._create_run("test_run", 2.5)

        result = show_run(self.artifacts_dir, "test_run")
        self.assertEqual(result.run_id, "test_run")
        self.assertIsNotNone(result.config)
        self.assertIsNotNone(result.metrics)
        assert result.config is not None
        assert result.metrics is not None
        self.assertEqual(result.config["strategy_name"], "uniform_random")
        self.assertEqual(result.metrics["average_hits"], 2.5)

    def test_compare_runs_handler(self) -> None:
        """Test compare runs handler."""
        self._create_run("run_a", 1.0)
        self._create_run("run_b", 3.0)

        result = compare_runs(self.artifacts_dir, "run_a", "run_b")
        self.assertEqual(result.run_id_1, "run_a")
        self.assertEqual(result.run_id_2, "run_b")
        self.assertEqual(result.avg_diff, 2.0)
        self.assertIsNone(result.error)

    def test_verify_run_handler(self) -> None:
        """Test verify run handler."""
        self._create_run("test_run", 2.0)

        result = verify_run(self.artifacts_dir, "test_run")
        self.assertEqual(result.run_id, "test_run")
        self.assertTrue(result.valid)
        self.assertIsNone(result.error)

    def test_compare_with_missing_run(self) -> None:
        """Test compare when one run is missing."""
        self._create_run("run_a", 1.0)

        result = compare_runs(self.artifacts_dir, "run_a", "nonexistent")
        self.assertIsNotNone(result.error)

    def test_show_missing_run(self) -> None:
        """Test show with missing run."""
        result = show_run(self.artifacts_dir, "nonexistent")
        self.assertIsNotNone(result.error)

    def test_verify_missing_run(self) -> None:
        """Test verify with missing run."""
        result = verify_run(self.artifacts_dir, "nonexistent")
        self.assertIsNotNone(result.error)
