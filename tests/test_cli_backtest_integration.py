"""Integration tests for CLI backtest commands with real artifacts."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.backtest_queries import compare_runs, list_runs, show_run, verify_run


class TestBacktestQueriesIntegration(TestCase):
    """Integration tests for backtest query operations using real artifacts."""

    def _create_sample_run(
        self,
        artifacts_dir: Path,
        run_id: str,
        avg_hits: float = 2.5,
    ) -> None:
        """Create a sample run directory with real artifacts."""
        run_dir = artifacts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        config_data = {
            "strategy_name": "uniform_random",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window_days": 360,
            "tickets_per_draw": 10,
            "random_seed": 42,
            "dataset_sha256": "a" * 64,
            "code_commit_sha": "b" * 64,
        }
        with open(run_dir / "config.json", "w") as f:
            json.dump(config_data, f)

        metrics_data = {
            "hit_distribution": {0: 100, 1: 50, 2: 30, 3: 15, 4: 5},
            "average_hits": avg_hits,
            "hit_rate_2_plus": 0.5,
            "hit_rate_3_plus": 0.3,
            "hit_rate_4_plus": 0.15,
            "hit_rate_5_plus": 0.05,
            "hit_rate_6": 0.01,
            "probability_score": 0.42,
            "baseline_comparison": {"uniform_random": 0.0},
            "confidence_intervals": {},
        }
        with open(run_dir / "metrics.json", "w") as f:
            json.dump(metrics_data, f)

        manifest_data = {
            "run_id": run_id,
            "status": "success",
            "files": {
                "config.json": "a" * 64,
                "metrics.json": "b" * 64,
            },
        }
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest_data, f)

    def test_list_runs_integration(self) -> None:
        """List runs from real artifact directory."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            self._create_sample_run(artifacts, "run_001", 1.5)
            self._create_sample_run(artifacts, "run_002", 2.5)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 2)
            self.assertEqual(len(result.run_ids), 2)
            self.assertIn("run_001", result.run_ids)
            self.assertIn("run_002", result.run_ids)

    def test_show_run_integration(self) -> None:
        """Show run details from real artifacts."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            self._create_sample_run(artifacts, "test_run", 2.3)

            result = show_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertIsNotNone(result.config)
            self.assertIsNotNone(result.metrics)
            assert result.config is not None
            assert result.metrics is not None
            self.assertIsNone(result.error)
            self.assertEqual(result.config["strategy_name"], "uniform_random")
            self.assertEqual(result.metrics["average_hits"], 2.3)

    def test_compare_runs_integration(self) -> None:
        """Compare two runs from real artifacts."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            self._create_sample_run(artifacts, "run_a", 1.0)
            self._create_sample_run(artifacts, "run_b", 3.0)

            result = compare_runs(artifacts, "run_a", "run_b")
            self.assertEqual(result.run_id_1, "run_a")
            self.assertEqual(result.run_id_2, "run_b")
            self.assertEqual(result.avg_diff, 2.0)
            self.assertIsNone(result.error)

    def test_verify_run_integration(self) -> None:
        """Verify run integrity from real artifacts."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            self._create_sample_run(artifacts, "test_run", 2.5)
            run_dir = artifacts / "test_run"

            # Calculate real hashes
            import hashlib

            with open(run_dir / "config.json", "rb") as f:
                config_hash = hashlib.sha256(f.read()).hexdigest()
            with open(run_dir / "metrics.json", "rb") as f:
                metrics_hash = hashlib.sha256(f.read()).hexdigest()

            # Update manifest with real hashes
            manifest = {
                "run_id": "test_run",
                "status": "success",
                "files": {
                    "config.json": config_hash,
                    "metrics.json": metrics_hash,
                },
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = verify_run(artifacts, "test_run")
            self.assertEqual(result.run_id, "test_run")
            self.assertTrue(result.valid)
            self.assertEqual(result.files_checked, 2)
            self.assertIsNone(result.error)

    def test_workflow_list_show_compare(self) -> None:
        """Complete workflow: list → show → compare."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for i in range(3):
                self._create_sample_run(artifacts, f"run_{i:03d}", 1.0 + i)

            # List
            list_result = list_runs(artifacts)
            self.assertEqual(list_result.count, 3)

            # Show first
            show_result = show_run(artifacts, "run_000")
            self.assertIsNotNone(show_result.config)
            self.assertIsNotNone(show_result.metrics)
            assert show_result.metrics is not None
            self.assertEqual(show_result.metrics["average_hits"], 1.0)

            # Compare
            compare_result = compare_runs(artifacts, "run_000", "run_002")
            self.assertEqual(compare_result.avg_diff, 2.0)
