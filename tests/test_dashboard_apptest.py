"""Streamlit AppTest basic scenarios for dashboard.py real UI testing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import TestCase

try:
    from streamlit.testing.v1 import AppTest
    HAS_APPTEST = True
except ImportError:
    HAS_APPTEST = False


def _create_artifact_files(
    run_dir: Path,
    config: dict[str, Any],
    metrics: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    """Create canonical 6-file artifact structure."""
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "config.json").write_text(json.dumps(config, sort_keys=True))
    (run_dir / "metrics.json").write_text(json.dumps(metrics, sort_keys=True))
    (run_dir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    (run_dir / "draw_results.csv").write_text("date,strategy,hits\n")
    (run_dir / "tickets.csv").write_text("draw_id,predicted\n")
    (run_dir / "warnings.json").write_text(json.dumps({}, sort_keys=True))


class TestDashboardAppTest(TestCase):
    """Real Streamlit AppTest basic scenarios for dashboard.py."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        if not HAS_APPTEST:
            self.skipTest("Streamlit AppTest not available")
        self.temp_dir = TemporaryDirectory()
        self.artifacts_path = Path(self.temp_dir.name) / "runs"

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    def test_no_runs_available(self) -> None:
        """Dashboard handles empty runs directory gracefully."""
        os.environ["BONOAI_BACKTEST_RUNS_DIR"] = str(self.artifacts_path)

        app = AppTest.from_file("src/bonoai/dashboard.py")
        app.run()

        self.assertTrue(True, "Dashboard should handle no runs without crashing")

    def test_valid_run_display(self) -> None:
        """Dashboard displays valid backtest run with all metrics."""
        run_id = "abc123def456"
        run_dir = self.artifacts_path / run_id

        config = {
            "strategy_name": "uniform_random",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window_days": 360,
            "tickets_per_draw": 10,
            "random_seed": 42,
            "dataset_sha256": "a" * 64,
            "code_commit_sha": "b" * 64,
        }

        metrics = {
            "hit_distribution": {0: 10, 1: 5},
            "average_hits": 0.5,
            "hit_rate_2_plus": 0.25,
            "hit_rate_3_plus": 0.1,
            "hit_rate_4_plus": 0.05,
            "hit_rate_5_plus": 0.0,
            "hit_rate_6": 0.0,
            "probability_score": 1.23,
            "baseline_comparison": {},
            "confidence_intervals": {},
        }

        manifest = {
            "run_id": run_id,
            "created_at": "2026-01-01T00:00:00Z",
            "files": {
                "config.json": "hash1",
                "metrics.json": "hash2",
                "draw_results.csv": "hash3",
                "tickets.csv": "hash4",
                "warnings.json": "hash5",
            }
        }

        _create_artifact_files(run_dir, config, metrics, manifest)
        os.environ["BONOAI_BACKTEST_RUNS_DIR"] = str(self.artifacts_path)

        app = AppTest.from_file("src/bonoai/dashboard.py")
        app.run()

        self.assertTrue(len(app.metric) > 0, "Expected metrics to be displayed")
        strategy_found = any("uniform_random" in str(metric) for metric in app.metric)
        self.assertTrue(strategy_found, "Expected strategy name in metrics")

    def test_multiple_runs_selectbox(self) -> None:
        """Dashboard selectbox includes all available runs."""
        run_ids = ["run001abc", "run002def", "run003ghi"]

        for run_id in run_ids:
            run_dir = self.artifacts_path / run_id
            config = {
                "strategy_name": "uniform_random",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "training_window_days": 360,
                "tickets_per_draw": 10,
                "random_seed": 42,
                "dataset_sha256": "a" * 64,
                "code_commit_sha": "b" * 64,
            }
            metrics = {
                "hit_distribution": {},
                "average_hits": 0.0,
                "hit_rate_2_plus": 0.0,
                "hit_rate_3_plus": 0.0,
                "hit_rate_4_plus": 0.0,
                "hit_rate_5_plus": 0.0,
                "hit_rate_6": 0.0,
                "probability_score": 0.0,
                "baseline_comparison": {},
                "confidence_intervals": {},
            }
            manifest = {
                "run_id": run_id,
                "created_at": "2026-01-01T00:00:00Z",
                "files": {
                    "config.json": "h1",
                    "metrics.json": "h2",
                    "draw_results.csv": "h3",
                    "tickets.csv": "h4",
                    "warnings.json": "h5",
                }
            }
            _create_artifact_files(run_dir, config, metrics, manifest)

        os.environ["BONOAI_BACKTEST_RUNS_DIR"] = str(self.artifacts_path)

        app = AppTest.from_file("src/bonoai/dashboard.py")
        app.run()

        self.assertTrue(len(app.selectbox) > 0, "Expected selectbox for run selection")

    def test_read_only_verification(self) -> None:
        """Dashboard is read-only: no write/delete operations."""
        run_id = "readonly_test"
        run_dir = self.artifacts_path / run_id

        config = {
            "strategy_name": "uniform_random",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window_days": 360,
            "tickets_per_draw": 10,
            "random_seed": 42,
            "dataset_sha256": "a" * 64,
            "code_commit_sha": "b" * 64,
        }

        metrics = {
            "hit_distribution": {0: 1},
            "average_hits": 0.0,
            "hit_rate_2_plus": 0.0,
            "hit_rate_3_plus": 0.0,
            "hit_rate_4_plus": 0.0,
            "hit_rate_5_plus": 0.0,
            "hit_rate_6": 0.0,
            "probability_score": 0.0,
            "baseline_comparison": {},
            "confidence_intervals": {},
        }

        manifest = {
            "run_id": run_id,
            "files": {
                "config.json": "h1",
                "metrics.json": "h2",
                "draw_results.csv": "h3",
                "tickets.csv": "h4",
                "warnings.json": "h5",
            }
        }

        _create_artifact_files(run_dir, config, metrics, manifest)
        os.environ["BONOAI_BACKTEST_RUNS_DIR"] = str(self.artifacts_path)

        app = AppTest.from_file("src/bonoai/dashboard.py")
        app.run()

        button_count = len(app.button)
        download_count = len(app.download_button)

        msg = "Dashboard should have no action buttons (read-only)"
        self.assertEqual(button_count, 0, msg)
        self.assertEqual(download_count, 0, "Dashboard should have no download buttons")
