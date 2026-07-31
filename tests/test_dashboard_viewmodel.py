"""Tests for dashboard viewmodel - pure business logic."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.dashboard_viewmodel import (
    compare_runs,
    format_status_label,
    get_run_info,
    list_runs,
    load_run_data,
    prepare_config_display,
    prepare_metrics_display,
    validate_run_data,
)


class TestLoadRunData(TestCase):
    """Test load_run_data functionality."""

    def test_load_valid_run(self) -> None:
        """Load valid run with all files."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {"strategy_name": "uniform_random", "start_date": "2025-01-01"}
            metrics_data = {"average_hits": 2.5, "hit_rate_2_plus": 0.4}
            manifest_data = {"run_id": "abc123", "status": "success"}

            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump(metrics_data, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            result = load_run_data(run_dir)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result["run_id"], "abc123")
            self.assertEqual(result["status"], "success")

    def test_load_missing_manifest(self) -> None:
        """Load run without manifest (tolerant)."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = load_run_data(run_dir)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result["status"], "unknown")
            self.assertEqual(result["run_id"], "")

    def test_load_missing_config(self) -> None:
        """Return None when config missing."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = load_run_data(run_dir)
            self.assertIsNone(result)

    def test_load_corrupt_json(self) -> None:
        """Return None for corrupt JSON."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                f.write("{invalid}")
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            result = load_run_data(run_dir)
            self.assertIsNone(result)


class TestListRuns(TestCase):
    """Test list_runs functionality."""

    def test_list_no_runs(self) -> None:
        """Return empty list when no runs."""
        with TemporaryDirectory() as tmpdir:
            result = list_runs(Path(tmpdir))
            self.assertEqual(result, [])

    def test_list_nonexistent_directory(self) -> None:
        """Return empty list when directory doesn't exist."""
        nonexistent = Path("/tmp/nonexistent_directory_xyz_abc_123")
        result = list_runs(nonexistent)
        self.assertEqual(result, [])

    def test_list_multiple_runs(self) -> None:
        """Return list of run IDs."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for run_id in ["run1", "run2", "run3"]:
                run_dir = artifacts / run_id
                run_dir.mkdir()
                with open(run_dir / "manifest.json", "w") as f:
                    json.dump({"run_id": run_id}, f)

            result = list_runs(artifacts)
            self.assertEqual(len(result), 3)
            self.assertIn("run1", result)
            self.assertIn("run2", result)


class TestGetRunInfo(TestCase):
    """Test get_run_info functionality."""

    def test_get_existing_run(self) -> None:
        """Get info for existing run."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "test_run"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.5}, f)

            result = get_run_info(artifacts, "test_run")
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result["config"]["strategy_name"], "test")

    def test_get_missing_run(self) -> None:
        """Return None for missing run."""
        with TemporaryDirectory() as tmpdir:
            result = get_run_info(Path(tmpdir), "nonexistent")
            self.assertIsNone(result)


class TestFormatStatusLabel(TestCase):
    """Test status formatting."""

    def test_format_success(self) -> None:
        """Format success status."""
        result = format_status_label("success")
        self.assertIn("✅", result)
        self.assertIn("Success", result)

    def test_format_failed(self) -> None:
        """Format failed status."""
        result = format_status_label("failed")
        self.assertIn("❌", result)
        self.assertIn("Failed", result)

    def test_format_unknown(self) -> None:
        """Format unknown status."""
        result = format_status_label("unknown")
        self.assertIn("unknown", result)


class TestPrepareMetricsDisplay(TestCase):
    """Test metrics display preparation."""

    def test_prepare_full_metrics(self) -> None:
        """Prepare all metric fields."""
        metrics = {
            "average_hits": 2.5,
            "hit_rate_2_plus": 0.4,
            "hit_rate_3_plus": 0.3,
            "hit_rate_4_plus": 0.2,
            "hit_rate_6": 0.05,
            "hit_distribution": {0: 10, 1: 20, 2: 30},
        }
        result = prepare_metrics_display(metrics)
        self.assertEqual(result["average_hits"], 2.5)
        self.assertEqual(result["hit_rate_2_plus"], 0.4)
        self.assertEqual(result["hit_distribution"], {0: 10, 1: 20, 2: 30})

    def test_prepare_partial_metrics(self) -> None:
        """Prepare metrics with missing fields (use defaults)."""
        metrics = {"average_hits": 1.0}
        result = prepare_metrics_display(metrics)
        self.assertEqual(result["average_hits"], 1.0)
        self.assertEqual(result["hit_rate_2_plus"], 0.0)
        self.assertEqual(result["hit_distribution"], {})


class TestPrepareConfigDisplay(TestCase):
    """Test config display preparation."""

    def test_prepare_config(self) -> None:
        """Format config for display."""
        config = {
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window_days": 10,
            "random_seed": 42,
        }
        result = prepare_config_display(config)
        self.assertIn("2025-01-01", result["period"])
        self.assertIn("2025-12-31", result["period"])
        self.assertEqual(result["training_window_days"], 10)
        self.assertEqual(result["random_seed"], 42)

    def test_prepare_config_missing_fields(self) -> None:
        """Format config with missing fields."""
        config: dict[str, int] = {}
        result = prepare_config_display(config)
        self.assertIn("?", result["period"])
        self.assertEqual(result["training_window_days"], 0)


class TestValidateRunData(TestCase):
    """Test run data validation."""

    def test_validate_valid_run(self) -> None:
        """Validate good run data."""
        data = {
            "config": {"strategy_name": "test"},
            "metrics": {"average_hits": 1.0},
            "status": "success",
        }
        is_valid, msg = validate_run_data(data)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_validate_no_data(self) -> None:
        """Reject None data."""
        is_valid, msg = validate_run_data(None)
        self.assertFalse(is_valid)
        self.assertIn("not found", msg)

    def test_validate_invalid_config(self) -> None:
        """Reject invalid config."""
        data = {
            "config": None,
            "metrics": {"average_hits": 1.0},
        }
        is_valid, msg = validate_run_data(data)
        self.assertFalse(is_valid)
        self.assertIn("config", msg)

    def test_validate_invalid_metrics(self) -> None:
        """Reject invalid metrics."""
        data = {
            "config": {"strategy_name": "test"},
            "metrics": None,
        }
        is_valid, msg = validate_run_data(data)
        self.assertFalse(is_valid)
        self.assertIn("metrics", msg)


class TestCompareRuns(TestCase):
    """Test run comparison."""

    def test_compare_valid_runs(self) -> None:
        """Compare two valid runs."""
        run1 = {
            "run_id": "run1",
            "config": {"strategy_name": "s1"},
            "metrics": {"average_hits": 1.5},
        }
        run2 = {
            "run_id": "run2",
            "config": {"strategy_name": "s2"},
            "metrics": {"average_hits": 2.5},
        }
        result = compare_runs(run1, run2)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["run1_avg_hits"], 1.5)
        self.assertEqual(result["run2_avg_hits"], 2.5)
        self.assertEqual(result["difference"], 1.0)

    def test_compare_missing_run(self) -> None:
        """Return None if run missing."""
        result = compare_runs(None, {"metrics": {}})
        self.assertIsNone(result)
        result = compare_runs({"metrics": {}}, None)
        self.assertIsNone(result)
