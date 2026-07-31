"""Integration tests for backtest CLI handlers with error paths."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock

from bonoai.cli_backtest import (
    _run_backtest_compare,
    _run_backtest_show,
    _run_backtest_verify,
)


class TestBacktestShowHandler(TestCase):
    """Test _run_backtest_show with error cases."""

    def test_show_missing_config_returns_error(self) -> None:
        """Show returns 2 when config missing."""
        with TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "nonexistent"
            args.as_json = False

            result = _run_backtest_show(args)
            self.assertEqual(result, 2)

    def test_show_with_json_flag(self) -> None:
        """Show with --json outputs valid JSON."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "test_run"
            run_dir.mkdir()

            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "uniform_random"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.5}, f)

            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "test_run"
            args.as_json = True

            result = _run_backtest_show(args)
            self.assertEqual(result, 0)


class TestBacktestCompareHandler(TestCase):
    """Test _run_backtest_compare with error cases."""

    def test_compare_missing_run_1_returns_error(self) -> None:
        """Compare returns 2 when first run missing."""
        with TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id_1 = "missing"
            args.run_id_2 = "also_missing"
            args.as_json = False

            result = _run_backtest_compare(args)
            self.assertEqual(result, 2)

    def test_compare_missing_run_2_returns_error(self) -> None:
        """Compare returns 2 when second run missing."""
        with TemporaryDirectory() as tmpdir:
            run1_dir = Path(tmpdir) / "run1"
            run1_dir.mkdir()

            with open(run1_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)

            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id_1 = "run1"
            args.run_id_2 = "missing"
            args.as_json = False

            result = _run_backtest_compare(args)
            self.assertEqual(result, 2)

    def test_compare_with_json_flag(self) -> None:
        """Compare with --json outputs valid JSON."""
        with TemporaryDirectory() as tmpdir:
            for rid in ["run1", "run2"]:
                rd = Path(tmpdir) / rid
                rd.mkdir()
                with open(rd / "metrics.json", "w") as f:
                    json.dump({"average_hits": 1.5 if rid == "run1" else 2.0}, f)

            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id_1 = "run1"
            args.run_id_2 = "run2"
            args.as_json = True

            result = _run_backtest_compare(args)
            self.assertEqual(result, 0)


class TestBacktestVerifyHandler(TestCase):
    """Test _run_backtest_verify with integrity checks."""

    def test_verify_missing_manifest_returns_error(self) -> None:
        """Verify returns 2 when manifest missing."""
        with TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "missing"
            args.as_json = False

            result = _run_backtest_verify(args)
            self.assertEqual(result, 2)

    def test_verify_mismatched_hash_returns_failure(self) -> None:
        """Verify returns 1 when hash mismatches."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "test_run"
            run_dir.mkdir()

            # Create files with content
            config_content = b'{"strategy_name": "test"}'
            with open(run_dir / "config.json", "wb") as f:
                f.write(config_content)

            # Create manifest with wrong hash
            manifest = {
                "files": {
                    "config.json": "0" * 64,  # Wrong hash
                }
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "test_run"
            args.as_json = False

            result = _run_backtest_verify(args)
            self.assertEqual(result, 1)

    def test_verify_missing_artifact_file_returns_failure(self) -> None:
        """Verify returns 1 when artifact file missing."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "test_run"
            run_dir.mkdir()

            # Create manifest referencing missing file
            manifest = {
                "files": {
                    "config.json": "a" * 64,
                    "missing.json": "b" * 64,
                }
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create only one file
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)

            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "test_run"
            args.as_json = False

            result = _run_backtest_verify(args)
            self.assertEqual(result, 1)

    def test_verify_with_json_flag(self) -> None:
        """Verify with --json outputs JSON result."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "test_run"
            run_dir.mkdir()

            config_content = b'{"strategy_name": "test"}'
            with open(run_dir / "config.json", "wb") as f:
                f.write(config_content)

            manifest = {
                "files": {
                    "config.json": hashlib.sha256(config_content).hexdigest(),
                }
            }
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "test_run"
            args.as_json = True

            result = _run_backtest_verify(args)
            self.assertEqual(result, 0)
