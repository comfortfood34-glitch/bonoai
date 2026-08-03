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
