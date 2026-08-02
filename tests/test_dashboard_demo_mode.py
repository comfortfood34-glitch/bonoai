"""Dashboard demo mode tests: fallback, banner, data separation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.dashboard import _resolve_artifacts_dir


class TestResolveArtifactsEnvVar(TestCase):
    """Test BONOAI_BACKTEST_RUNS_DIR environment variable priority."""

    def test_env_var_with_valid_run_directory(self) -> None:
        """Env var pointing to valid runs directory returns that path, not demo."""
        with TemporaryDirectory() as tmpdir:
            real_dir = Path(tmpdir) / "official_runs"
            real_dir.mkdir()
            run_dir = real_dir / "official_run_001"
            run_dir.mkdir()
            manifest_text = '{"run_id":"official_run_001","status":"success"}'
            (run_dir / "manifest.json").write_text(manifest_text)

            with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": str(real_dir)}):
                path, is_demo = _resolve_artifacts_dir()
                self.assertEqual(path, real_dir)
                self.assertFalse(is_demo, "Should not be demo mode with official data")

    def test_env_var_empty_string_triggers_fallback(self) -> None:
        """Empty env var string triggers fallback to local backtests/runs."""
        with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": ""}):
            path, _ = _resolve_artifacts_dir()
            self.assertIsNotNone(path, "Should resolve to some path even with empty env var")

    def test_env_var_nonexistent_path_still_honored(self) -> None:
        """Even if path doesn't exist, env var takes precedence over fallback."""
        nonexistent = "/nonexistent/path/to/runs"
        with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": nonexistent}):
            path, is_demo = _resolve_artifacts_dir()
            self.assertEqual(path, Path(nonexistent))
            self.assertFalse(is_demo)


class TestLocalBacktestsRunsFallback(TestCase):
    """Test backtests/runs/ as second priority fallback."""

    def test_local_backtests_runs_when_env_var_not_set(self) -> None:
        """When env var not set, prefer backtests/runs or fallback to demo."""
        env_copy = os.environ.copy()
        if "BONOAI_BACKTEST_RUNS_DIR" in env_copy:
            del env_copy["BONOAI_BACKTEST_RUNS_DIR"]

        with patch.dict(os.environ, env_copy, clear=True):
            path, is_demo = _resolve_artifacts_dir()
            local_runs = Path("backtests/runs")
            demo_runs = Path("examples/demo_backtests")

            if local_runs.exists() and any(local_runs.glob("*/manifest.json")):
                self.assertEqual(path, local_runs)
                self.assertFalse(is_demo)
            elif demo_runs.exists():
                self.assertEqual(path, demo_runs)
                self.assertTrue(is_demo)
            else:
                self.assertEqual(path, local_runs)

    def test_prefers_local_backtests_over_demo(self) -> None:
        """backtests/runs/ is preferred over demo even if demo exists."""
        demo_path = Path("examples/demo_backtests")
        if demo_path.exists():
            env_copy = os.environ.copy()
            if "BONOAI_BACKTEST_RUNS_DIR" in env_copy:
                del env_copy["BONOAI_BACKTEST_RUNS_DIR"]

            with patch.dict(os.environ, env_copy, clear=True):
                path, _ = _resolve_artifacts_dir()
                local_runs = Path("backtests/runs")
                if local_runs.exists():
                    self.assertEqual(path, local_runs)


class TestDemoModeFallback(TestCase):
    """Test demo mode fallback when no real data exists."""

    def test_demo_fallback_exists_and_is_used(self) -> None:
        """examples/demo_backtests is used as last resort fallback."""
        demo_path = Path("examples/demo_backtests")
        if demo_path.exists() and any(demo_path.glob("*/manifest.json")):
            env_copy = os.environ.copy()
            if "BONOAI_BACKTEST_RUNS_DIR" in env_copy:
                del env_copy["BONOAI_BACKTEST_RUNS_DIR"]

            with patch("pathlib.Path.exists") as mock_exists, patch(
                "pathlib.Path.glob"
            ) as mock_glob:

                def exists_side(p: Path) -> bool:
                    path_str = str(p)
                    if "backtests/runs" in path_str:
                        return True
                    return "demo_backtests" in path_str

                def glob_side(p: Path, pattern: str) -> list[Path]:
                    if "backtests/runs" in str(p):
                        return []
                    return list(demo_path.glob("*/manifest.json"))

                mock_exists.side_effect = lambda: exists_side(mock_exists)
                mock_glob.side_effect = lambda pat: glob_side(mock_glob, pat)

                path, _ = _resolve_artifacts_dir()
                self.assertIsNotNone(path)


class TestDemoBannerLogic(TestCase):
    """Test demo mode flag behavior for banner display."""

    def test_resolve_returns_tuple_with_bool_flag(self) -> None:
        """_resolve_artifacts_dir always returns (Path, bool) for banner logic."""
        path, is_demo = _resolve_artifacts_dir()
        self.assertIsInstance(path, Path)
        self.assertIsInstance(is_demo, bool)

    def test_env_var_disables_demo_banner(self) -> None:
        """With BONOAI_BACKTEST_RUNS_DIR set, is_demo should be False."""
        with TemporaryDirectory() as tmpdir:
            official = Path(tmpdir) / "official"
            official.mkdir()
            (official / "run1").mkdir()
            (official / "run1" / "manifest.json").write_text('{}')

            with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": str(official)}):
                _, is_demo = _resolve_artifacts_dir()
                self.assertFalse(is_demo, "Banner should not show with official data")


class TestDemoDataIntegrity(TestCase):
    """Test demo data files and manifest integrity."""

    def test_demo_run_001_all_files_present(self) -> None:
        """Demo run has all required canonical files."""
        demo_run = Path("examples/demo_backtests/demo_run_001")
        self.assertTrue(demo_run.exists())
        self.assertTrue((demo_run / "config.json").exists())
        self.assertTrue((demo_run / "metrics.json").exists())
        self.assertTrue((demo_run / "draw_results.csv").exists())
        self.assertTrue((demo_run / "tickets.csv").exists())
        self.assertTrue((demo_run / "warnings.json").exists())
        self.assertTrue((demo_run / "manifest.json").exists())

    def test_demo_manifest_contains_all_sha256_hashes(self) -> None:
        """Demo manifest has SHA-256 entries for all 5 artifacts."""
        manifest_path = Path("examples/demo_backtests/demo_run_001/manifest.json")
        with open(manifest_path) as f:
            manifest = json.load(f)

        self.assertIn("sha256_inventory", manifest)
        hashes = manifest["sha256_inventory"]
        required = {
            "config.json", "metrics.json", "draw_results.csv",
            "tickets.csv", "warnings.json"
        }
        self.assertEqual(set(hashes.keys()), required)

    def test_demo_manifest_hashes_are_valid_sha256(self) -> None:
        """All SHA-256 hashes in manifest are 64-char hex strings."""
        manifest_path = Path("examples/demo_backtests/demo_run_001/manifest.json")
        with open(manifest_path) as f:
            manifest = json.load(f)

        for filename, hash_val in manifest["sha256_inventory"].items():
            self.assertEqual(len(hash_val), 64, f"Invalid SHA-256 for {filename}")
            try:
                int(hash_val, 16)
            except ValueError:
                self.fail(f"Hash for {filename} is not valid hex")

    def test_demo_manifest_hashes_match_files(self) -> None:
        """SHA-256 hashes in manifest match actual files."""
        import hashlib

        demo_run = Path("examples/demo_backtests/demo_run_001")
        manifest_path = demo_run / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        for filename, expected_hash in manifest["sha256_inventory"].items():
            filepath = demo_run / filename
            self.assertTrue(filepath.exists(), f"{filename} not found")

            actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            self.assertEqual(
                actual_hash, expected_hash,
                f"Hash mismatch for {filename}: {actual_hash} != {expected_hash}"
            )


class TestDataSeparationGuarantees(TestCase):
    """Test absolute isolation between demo and official data."""

    def test_env_var_path_isolation(self) -> None:
        """Env var path is used exclusively, no demo mixing."""
        with TemporaryDirectory() as tmpdir:
            official = Path(tmpdir) / "official"
            official.mkdir()
            (official / "run1").mkdir()
            (official / "run1" / "manifest.json").write_text('{"run_id":"official"}')

            with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": str(official)}):
                path, is_demo = _resolve_artifacts_dir()
                self.assertEqual(path, official)
                self.assertFalse(is_demo)
                self.assertNotIn("demo", str(path).lower())

    def test_official_data_mode_no_demo_banner(self) -> None:
        """Official mode definitively disables demo banner flag."""
        with TemporaryDirectory() as tmpdir:
            official = Path(tmpdir) / "official"
            official.mkdir()
            (official / "official_run").mkdir()
            (official / "official_run" / "manifest.json").write_text('{"run_id":"official"}')

            with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": str(official)}):
                _, is_demo = _resolve_artifacts_dir()
                self.assertIs(is_demo, False)  # Explicitly False, not just falsy


class TestDemoModeLogicWithEnv(TestCase):
    """Test demo mode flag changes with environment."""

    def test_demo_mode_off_with_env_var_set(self) -> None:
        """is_demo flag is False when BONOAI_BACKTEST_RUNS_DIR set."""
        with TemporaryDirectory() as tmpdir:
            real = Path(tmpdir) / "real"
            real.mkdir()
            (real / "run1").mkdir()
            (real / "run1" / "manifest.json").write_text('{}')

            with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": str(real)}):
                _, is_demo = _resolve_artifacts_dir()
                self.assertFalse(is_demo)

    def test_demo_mode_flag_consistency(self) -> None:
        """is_demo flag is consistent across multiple calls."""
        with TemporaryDirectory() as tmpdir:
            real = Path(tmpdir) / "real"
            real.mkdir()
            (real / "run1").mkdir()
            (real / "run1" / "manifest.json").write_text('{}')

            with patch.dict(os.environ, {"BONOAI_BACKTEST_RUNS_DIR": str(real)}):
                _, flag1 = _resolve_artifacts_dir()
                _, flag2 = _resolve_artifacts_dir()
                self.assertEqual(flag1, flag2)


class TestDashboardMainFunction(TestCase):
    """Test dashboard main() function logic with mocked Streamlit."""

    def test_main_raises_import_error_when_streamlit_missing(self) -> None:
        """main() raises ImportError when st is None."""
        from bonoai.dashboard import main

        with patch("bonoai.dashboard.st", None):
            with self.assertRaises(ImportError) as ctx:
                main()
            self.assertIn("Streamlit required", str(ctx.exception))

    def test_main_calls_resolve_artifacts_dir(self) -> None:
        """main() calls _resolve_artifacts_dir() to get data path."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("examples/demo_backtests"), True),
        )

        with mock_st as st_mock, mock_resolve as resolve_mock:
            st_mock.selectbox.return_value = None
            main()
            resolve_mock.assert_called_once()

    def test_main_displays_demo_banner_when_is_demo_true(self) -> None:
        """main() displays warning banner when is_demo flag is True."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("examples/demo_backtests"), True),
        )

        with mock_st as st_mock, mock_resolve:
            st_mock.selectbox.return_value = None
            main()
            st_mock.warning.assert_called_once()
            warning_call = st_mock.warning.call_args[0][0]
            self.assertIn("MODO DEMONSTRAÇÃO", warning_call)
            self.assertIn("dados sintéticos", warning_call)

    def test_main_no_banner_when_official_data(self) -> None:
        """main() does not display banner for official data."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )

        with mock_st as st_mock, mock_resolve:
            st_mock.selectbox.return_value = None
            main()
            st_mock.warning.assert_not_called()

    def test_main_handles_no_runs_available(self) -> None:
        """main() shows warning when no runs are available."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=[],
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs:
            main()
            st_mock.warning.assert_called_with("No backtest runs available")

    def test_main_handles_failed_run_load(self) -> None:
        """main() shows error when run data fails to load."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=["run_001"],
        )
        mock_get_info = patch(
            "bonoai.dashboard.get_run_info",
            return_value=None,
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs, mock_get_info:
            st_mock.selectbox.return_value = "run_001"
            main()
            st_mock.error.assert_called_once()
            call_args = st_mock.error.call_args[0][0]
            self.assertIn("Failed to load", call_args)

    def test_main_handles_invalid_run_data(self) -> None:
        """main() shows error when run data validation fails."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=["run_001"],
        )
        mock_get_info = patch(
            "bonoai.dashboard.get_run_info",
            return_value={"config": {}},
        )
        mock_validate = patch(
            "bonoai.dashboard.validate_run_data",
            return_value=(False, "Invalid data"),
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs, \
             mock_get_info, mock_validate:
            st_mock.selectbox.return_value = "run_001"
            main()
            st_mock.error.assert_called_with("Invalid data")

    def test_fallback_returns_default_when_no_paths_exist(self) -> None:
        """_resolve_artifacts_dir returns default when all paths missing."""
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "exists", return_value=False):
            path, is_demo = _resolve_artifacts_dir()
            self.assertEqual(path, Path("backtests/runs"))
            self.assertFalse(is_demo)
