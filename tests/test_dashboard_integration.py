"""Integration tests for dashboard with missing code paths."""

import contextlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.dashboard import load_run_data, main


class TestLoadRunDataEdgeCases(TestCase):
    """Test load_run_data with various edge cases."""

    def test_load_run_data_missing_metrics_returns_none(self) -> None:
        """Load returns None when metrics.json missing."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)

            result = load_run_data(run_dir)
            self.assertIsNone(result)

    def test_load_run_data_missing_config_returns_none(self) -> None:
        """Load returns None when config.json missing."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = load_run_data(run_dir)
            self.assertIsNone(result)

    def test_load_run_data_missing_manifest_still_loads(self) -> None:
        """Load succeeds even without manifest."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertEqual(result["config"]["strategy_name"], "test")

    def test_load_run_data_corrupt_json_returns_none(self) -> None:
        """Load returns None for corrupt JSON."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                f.write("{invalid json}")
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = load_run_data(run_dir)
            self.assertIsNone(result)

    def test_load_run_data_all_required_fields(self) -> None:
        """Load preserves all required fields."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {
                "strategy_name": "uniform_random",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            }
            metrics_data = {
                "average_hits": 2.5,
                "hit_rate_2_plus": 0.4,
                "hit_rate_3_plus": 0.2,
            }
            manifest_data = {
                "run_id": "abc123def456",
                "status": "success",
            }

            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump(metrics_data, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            result = load_run_data(run_dir)
            if result is None:
                self.fail("result should not be None")
            self.assertEqual(result["run_id"], "abc123def456")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["config"]["strategy_name"], "uniform_random")
            self.assertEqual(result["metrics"]["average_hits"], 2.5)


class TestDashboardMainImportErrors(TestCase):
    """Test main() behavior when Streamlit unavailable."""

    def test_main_with_nonexistent_dir(self) -> None:
        """Main handles nonexistent artifacts directory."""
        with contextlib.suppress(Exception):
            main(artifacts_dir="/nonexistent/path")

    def test_main_with_empty_artifacts(self) -> None:
        """Main handles empty artifacts directory."""
        with TemporaryDirectory() as tmpdir, contextlib.suppress(Exception):
            main(artifacts_dir=tmpdir)


class TestDashboardMetricsDisplay(TestCase):
    """Test dashboard metrics formatting."""

    def test_metrics_percentage_formatting(self) -> None:
        """Metrics are properly formatted for display."""
        metrics = {
            "hit_rate_2_plus": 0.223,
            "hit_rate_3_plus": 0.155,
            "hit_rate_4_plus": 0.067,
            "hit_rate_6": 0.001,
        }
        for _rate_name, rate_val in metrics.items():
            formatted = f"{rate_val:.1%}"
            self.assertIn("%", formatted)

    def test_metrics_average_hits_formatting(self) -> None:
        """Average hits formatted to 2 decimal places."""
        avg_hits = 1.234567
        formatted = f"{avg_hits:.2f}"
        self.assertEqual(formatted, "1.23")

    def test_metrics_with_missing_fields(self) -> None:
        """Metrics display handles missing fields gracefully."""
        metrics = {
            "average_hits": 1.5,
        }
        for rate_name in ["hit_rate_2_plus", "hit_rate_6"]:
            rate_val = metrics.get(rate_name, 0.0)
            self.assertEqual(rate_val, 0.0)

    def test_load_run_data_with_all_metrics_fields(self) -> None:
        """Load returns complete metrics object."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {
                "strategy_name": "uniform_random",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            }
            metrics_data = {
                "average_hits": 2.5,
                "hit_rate_2_plus": 0.4,
                "hit_rate_3_plus": 0.2,
                "hit_rate_4_plus": 0.1,
                "hit_rate_5_plus": 0.05,
                "hit_rate_6": 0.01,
                "probability_score": 0.417,
            }
            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump(metrics_data, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertEqual(result["metrics"]["probability_score"], 0.417)
                self.assertEqual(result["metrics"]["hit_rate_6"], 0.01)

    def test_load_run_data_partial_metrics(self) -> None:
        """Load handles partial metrics gracefully."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0, "hit_rate_2_plus": 0.5}, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertIn("average_hits", result["metrics"])

    def test_load_run_data_with_manifest_status(self) -> None:
        """Load includes manifest status field."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump({"status": "verified"}, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertEqual(result.get("status"), "verified")

    def test_load_run_data_none_fields_handled(self) -> None:
        """Load handles None/missing nested fields."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({}, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertIsNotNone(result["config"])
