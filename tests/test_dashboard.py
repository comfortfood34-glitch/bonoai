"""Dashboard MVP functionality tests."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.dashboard import load_run_data


class TestDashboardRunDataLoader(TestCase):
    """Verify dashboard data loading functionality."""

    def test_load_run_data_returns_dict_for_valid_json(self) -> None:
        """load_run_data returns parsed JSON dict."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {"strategy_name": "test"}
            metrics_data = {"average_hits": 2.5}
            manifest_data = {"run_id": "test123", "status": "success"}
            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump(metrics_data, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)
            result = load_run_data(run_dir)
            if result is None:
                self.fail("result should not be None")
            self.assertEqual(result["run_id"], "test123")
            self.assertEqual(result["status"], "success")

    def test_load_run_data_returns_none_for_missing_file(self) -> None:
        """load_run_data returns None if files don't exist."""
        result = load_run_data(Path("/nonexistent/run"))
        self.assertIsNone(result)

    def test_load_run_data_returns_none_for_invalid_json(self) -> None:
        """load_run_data returns None for malformed JSON."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                f.write("{ invalid json }")
            with open(run_dir / "metrics.json", "w") as f:
                f.write("{ invalid json }")
            with open(run_dir / "manifest.json", "w") as f:
                f.write("{ invalid json }")
            result = load_run_data(run_dir)
            self.assertIsNone(result)

    def test_load_run_data_preserves_all_fields(self) -> None:
        """load_run_data preserves all JSON fields."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {
                "strategy_name": "uniform_random",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "training_window_days": 360,
            }
            metrics_data = {
                "average_hits": 2.3,
                "hit_rate_2_plus": 0.45,
                "hit_rate_6": 0.01,
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
            self.assertEqual(result["config"]["strategy_name"], "uniform_random")
            self.assertEqual(result["metrics"]["average_hits"], 2.3)

    def test_load_run_data_handles_empty_file(self) -> None:
        """load_run_data returns None for empty file."""
        with TemporaryDirectory() as tmpdir:
            run_file = Path(tmpdir) / "run.json"
            run_file.write_text("")
            result = load_run_data(run_file)
            self.assertIsNone(result)


class TestDashboardReadOnlyConstraints(TestCase):
    """Verify dashboard maintains read-only constraints."""

    def test_load_run_data_does_not_modify_file(self) -> None:
        """load_run_data does not write or modify files."""
        with TemporaryDirectory() as tmpdir:
            run_file = Path(tmpdir) / "run.json"
            test_data = {"run_id": "test", "status": "success"}
            with open(run_file, "w") as f:
                json.dump(test_data, f)
            original_mtime = run_file.stat().st_mtime
            load_run_data(run_file)
            new_mtime = run_file.stat().st_mtime
            self.assertEqual(original_mtime, new_mtime)

    def test_dashboard_imports_streamlit_safely(self) -> None:
        """Dashboard uses TYPE_CHECKING guard for Streamlit import."""
        import inspect

        from bonoai import dashboard
        source = inspect.getsource(dashboard)
        self.assertIn("TYPE_CHECKING", source)
        self.assertIn("import streamlit", source)

    def test_main_function_exists_and_callable(self) -> None:
        """Dashboard has callable main() function."""
        from bonoai.dashboard import main
        self.assertTrue(callable(main))

    def test_main_raises_import_error_without_streamlit(self) -> None:
        """main() raises ImportError if Streamlit unavailable."""
        with patch.dict('sys.modules', {'streamlit': None}):
            from bonoai.dashboard import main
            with self.assertRaises(ImportError):
                main()


class TestDashboardConfigContract(TestCase):
    """Verify dashboard config display contract."""

    def test_run_data_includes_config_section(self) -> None:
        """Run data must include config for dashboard display."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {
                "strategy_name": "uniform_random",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }
            metrics_data = {"average_hits": 1.0}
            manifest_data = {"run_id": "test", "status": "success"}
            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump(metrics_data, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)
            result = load_run_data(run_dir)
            if result is None:
                self.fail("result should not be None")
            self.assertIn("config", result)
            self.assertEqual(result["config"]["strategy_name"], "uniform_random")

    def test_run_data_includes_metrics_section(self) -> None:
        """Run data must include metrics for dashboard display."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            config_data = {"strategy_name": "test"}
            metrics_data = {
                "average_hits": 2.5,
                "hit_rate_2_plus": 0.5,
            }
            manifest_data = {"run_id": "test", "status": "success"}
            with open(run_dir / "config.json", "w") as f:
                json.dump(config_data, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump(metrics_data, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)
            result = load_run_data(run_dir)
            if result is None:
                self.fail("result should not be None")
            self.assertIn("metrics", result)
            self.assertIn("average_hits", result["metrics"])
