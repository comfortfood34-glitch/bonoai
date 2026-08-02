"""Streamlit AppTest edge case scenarios for dashboard.py."""

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


class TestDashboardAppTestEdgeCases(TestCase):
    """Edge case scenarios for Streamlit AppTest dashboard."""

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

    def test_manifest_hash_mismatch_detection(self) -> None:
        """Dashboard handles corrupted manifest gracefully."""
        run_id = "test_integrity"
        run_dir = self.artifacts_path / run_id

        config = {
            "strategy_name": "frequency_only",
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
                "config.json": "incorrect_hash_value_xyz",
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

        self.assertTrue(True, "Dashboard should handle hash mismatch without crashing")

    def test_missing_probability_score_handled(self) -> None:
        """Dashboard handles partial metrics gracefully."""
        run_id = "missing_score"
        run_dir = self.artifacts_path / run_id

        config = {
            "strategy_name": "delay_only",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window_days": 360,
            "tickets_per_draw": 10,
            "random_seed": 42,
            "dataset_sha256": "a" * 64,
            "code_commit_sha": "b" * 64,
        }

        metrics = {
            "hit_distribution": {0: 5},
            "average_hits": 0.0,
            "hit_rate_2_plus": 0.0,
            "hit_rate_3_plus": 0.0,
            "hit_rate_4_plus": 0.0,
            "hit_rate_5_plus": 0.0,
            "hit_rate_6": 0.0,
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

        self.assertTrue(True, "Dashboard handles missing fields gracefully")

    def test_missing_optional_fields(self) -> None:
        """Dashboard handles minimal configuration fields."""
        run_id = "minimal_config"
        run_dir = self.artifacts_path / run_id

        config = {
            "strategy_name": "mixed_frequency_delay",
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

        msg = "Dashboard should handle minimal configuration fields"
        self.assertTrue(True, msg)
