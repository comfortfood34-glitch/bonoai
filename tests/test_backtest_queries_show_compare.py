"""Tests for backtest query show and compare operations."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.backtest_queries import compare_runs, show_run


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
