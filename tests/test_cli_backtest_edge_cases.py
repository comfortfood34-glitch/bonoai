"""Tests for CLI backtest edge cases and error scenarios."""

import argparse
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli_backtest import (
    _run_backtest_compare,
    _run_backtest_list,
    _run_backtest_show,
    _run_backtest_verify,
)


class TestCliBacktestEdgeCases(TestCase):
    """Test CLI edge cases and error handling."""

    def setUp(self) -> None:
        """Set up empty artifacts directory."""
        self.tmpdir = TemporaryDirectory()
        self.artifacts_dir = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def _create_incomplete_run(self, run_id: str) -> None:
        """Create run with missing files."""
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True)
        # Only config, missing metrics and manifest
        with open(run_dir / "config.json", "w") as f:
            json.dump({"strategy_name": "test"}, f)

    def test_list_runs_empty_directory(self) -> None:
        """List runs with empty directory."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_list(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Execuções: 0", output)

    def test_list_runs_empty_json(self) -> None:
        """List runs empty with JSON output."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_list(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["runs"], [])

    def test_show_run_incomplete_data(self) -> None:
        """Show run with incomplete data (missing metrics) returns success."""
        self._create_incomplete_run("incomplete_run")

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="incomplete_run",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()):
            result = _run_backtest_show(args)

        # Can still show config even if metrics missing
        self.assertEqual(result, 0)

    def test_show_run_incomplete_json(self) -> None:
        """Show run incomplete with JSON output."""
        self._create_incomplete_run("incomplete_run")

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="incomplete_run",
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_show(args)
            output = fake_out.getvalue()

        # Can still show with metrics: null
        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertIsNotNone(data["config"])

    def test_compare_runs_both_missing(self) -> None:
        """Compare runs when both are missing."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id_1="nonexistent1",
            run_id_2="nonexistent2",
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()):
            result = _run_backtest_compare(args)

        self.assertEqual(result, 2)

    def test_compare_runs_one_incomplete(self) -> None:
        """Compare runs when one is incomplete."""
        self._create_incomplete_run("incomplete")

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id_1="incomplete",
            run_id_2="nonexistent",
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()):
            result = _run_backtest_compare(args)

        self.assertEqual(result, 2)

    def test_verify_run_missing_all_files(self) -> None:
        """Verify run when directory is empty."""
        (self.artifacts_dir / "empty_run").mkdir()

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="empty_run",
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()):
            result = _run_backtest_verify(args)

        self.assertEqual(result, 2)

    def test_verify_run_missing_files_json(self) -> None:
        """Verify run with missing files JSON output."""
        (self.artifacts_dir / "empty_run").mkdir()

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="empty_run",
            as_json=True,
        )

        with patch("sys.stderr", new=StringIO()):
            result = _run_backtest_verify(args)

        self.assertEqual(result, 2)

    def test_list_runs_multiple_plain(self) -> None:
        """List multiple runs plain output."""
        for i in range(1, 4):
            run_dir = self.artifacts_dir / f"run_{i:03d}"
            run_dir.mkdir()
            with open(run_dir / "manifest.json", "w") as f:
                json.dump({"run_id": f"run_{i:03d}"}, f)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_list(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Execuções: 3", output)
        for i in range(1, 4):
            self.assertIn(f"run_{i:03d}", output)

    def test_show_run_with_no_average_hits(self) -> None:
        """Show run where metrics has no average_hits."""
        run_dir = self.artifacts_dir / "test_run"
        run_dir.mkdir()
        with open(run_dir / "config.json", "w") as f:
            json.dump({"strategy_name": "test"}, f)
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"hit_distribution": {0: 100}}, f)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="test_run",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()):
            result = _run_backtest_show(args)

        # Should not crash
        self.assertEqual(result, 0)
