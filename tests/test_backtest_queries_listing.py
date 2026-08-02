"""Tests for backtest query listing operations."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.backtest_queries import list_runs


class TestListRuns(TestCase):
    """Test list_runs functionality."""

    def test_list_empty_directory(self) -> None:
        """Return empty list for nonexistent directory."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            result = list_runs(artifacts)
            self.assertEqual(result.count, 0)
            self.assertEqual(result.run_ids, [])

    def test_list_nonexistent_path(self) -> None:
        """Return empty list when path doesn't exist."""
        nonexistent = Path("/tmp/nonexistent_path_xyz_abc_123")
        result = list_runs(nonexistent)
        self.assertEqual(result.count, 0)
        self.assertEqual(result.run_ids, [])

    def test_list_single_run(self) -> None:
        """List single run."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "run1"
            run_dir.mkdir()
            with open(run_dir / "manifest.json", "w") as f:
                json.dump({"run_id": "run1"}, f)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 1)
            self.assertEqual(result.run_ids, ["run1"])

    def test_list_multiple_runs(self) -> None:
        """List multiple runs, sorted."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for i in range(5):
                run_dir = artifacts / f"run{i}"
                run_dir.mkdir()
                with open(run_dir / "manifest.json", "w") as f:
                    json.dump({"run_id": f"run{i}"}, f)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 5)
            self.assertEqual(len(result.run_ids), 5)
            self.assertIn("run0", result.run_ids)
            self.assertIn("run4", result.run_ids)

    def test_list_more_than_ten_runs(self) -> None:
        """List respects 10-run limit in run_ids."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            for i in range(15):
                run_dir = artifacts / f"run{i:02d}"
                run_dir.mkdir()
                with open(run_dir / "manifest.json", "w") as f:
                    json.dump({"run_id": f"run{i:02d}"}, f)

            result = list_runs(artifacts)
            self.assertEqual(result.count, 15)
            self.assertEqual(len(result.run_ids), 10)

    def test_list_ignores_non_manifest_files(self) -> None:
        """Only count directories with manifest.json."""
        with TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            run_dir = artifacts / "run1"
            run_dir.mkdir()
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)

            other_dir = artifacts / "other"
            other_dir.mkdir()

            result = list_runs(artifacts)
            self.assertEqual(result.count, 0)
            self.assertEqual(result.run_ids, [])
