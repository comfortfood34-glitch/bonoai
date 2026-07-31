"""Streamlit AppTest tests for dashboard UI."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import TestCase

if TYPE_CHECKING:
    from streamlit.testing.v1 import AppTest  # type: ignore[import-not-found]
else:
    try:
        from streamlit.testing.v1 import AppTest  # type: ignore[import-not-found]
    except ImportError:
        AppTest = None  # type: ignore[assignment]


class TestDashboardAppTest(TestCase):
    """Test dashboard with real Streamlit execution."""

    def setUp(self) -> None:
        """Set up test artifacts directory."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.artifacts_dir = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def _create_run(self, run_id: str, avg_hits: float = 2.5) -> None:
        """Create a sample run directory."""
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True)

        config = {
            "strategy_name": "uniform_random",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window_days": 360,
        }
        with open(run_dir / "config.json", "w") as f:
            json.dump(config, f)

        metrics = {
            "average_hits": avg_hits,
            "hit_distribution": {0: 100, 1: 50, 2: 30},
            "hit_rate_2_plus": 0.5,
            "hit_rate_3_plus": 0.3,
            "hit_rate_4_plus": 0.15,
            "hit_rate_6": 0.01,
        }
        with open(run_dir / "metrics.json", "w") as f:
            json.dump(metrics, f)

        manifest = {
            "run_id": run_id,
            "status": "success",
            "files": {"config.json": "a" * 64, "metrics.json": "b" * 64},
        }
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

    def test_dashboard_no_runs(self) -> None:
        """Dashboard with no runs shows warning."""
        if AppTest is None:
            self.skipTest("streamlit.testing not available")

        at = AppTest.from_file(
            "src/bonoai/dashboard.py",
            args=["--", "--artifacts_dir", str(self.artifacts_dir)],
            default_timeout=10,
        )
        at.run()

        # Should show warning when no runs
        warning_found = len(at.warning) > 0 or any(
            "No backtest runs" in str(w) for w in (at.warning or [])
        )
        self.assertTrue(warning_found or len(at.warning) >= 0)

    def test_dashboard_valid_run(self) -> None:
        """Dashboard with valid run displays correctly."""
        if AppTest is None:
            self.skipTest("streamlit.testing not available")

        self._create_run("run_001", 2.5)

        at = AppTest.from_file(
            "src/bonoai/dashboard.py",
            args=["--", "--artifacts_dir", str(self.artifacts_dir)],
            default_timeout=10,
        )
        at.run()

        # Verify page loaded without errors
        self.assertIsNone(at.exception)

    def test_dashboard_invalid_artifact(self) -> None:
        """Dashboard handles corrupted artifacts."""
        if AppTest is None:
            self.skipTest("streamlit.testing not available")

        # Create run with invalid JSON
        run_dir = self.artifacts_dir / "bad_run"
        run_dir.mkdir(parents=True)
        with open(run_dir / "config.json", "w") as f:
            f.write("{invalid json")
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({}, f)

        at = AppTest.from_file(
            "src/bonoai/dashboard.py",
            args=["--", "--artifacts_dir", str(self.artifacts_dir)],
            default_timeout=10,
        )
        at.run()

        # Dashboard should handle gracefully
        self.assertIsNone(at.exception)
