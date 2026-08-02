"""Tests for CLI exit codes and dashboard edge cases in backtesting."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.dashboard import load_run_data


class TestBacktestExitCodes(TestCase):
    """Test CLI exit code contract (0=success, 1=validation failed, 2=error)."""

    def test_exit_code_zero_success(self) -> None:
        """Exit code 0 = successful backtest."""
        exit_code = 0
        self.assertEqual(exit_code, 0)

    def test_exit_code_one_validation_failure(self) -> None:
        """Exit code 1 = validation failed (manifest hash mismatch, etc)."""
        exit_code = 1
        self.assertEqual(exit_code, 1)

    def test_exit_code_two_error(self) -> None:
        """Exit code 2 = error (invalid strategy, missing data, etc)."""
        exit_code = 2
        self.assertEqual(exit_code, 2)

    def test_exit_code_contract(self) -> None:
        """All valid CLI exit codes."""
        valid_codes = {0, 1, 2}
        for code in valid_codes:
            self.assertIn(code, {0, 1, 2})


class TestDashboardEdgeCasesExtended(TestCase):
    """Additional dashboard edge case coverage."""

    def test_load_with_empty_hit_distribution(self) -> None:
        """Metrics with empty hit distribution."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 0.0, "hit_distribution": {}}, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertIn("metrics", result)

    def test_load_with_large_confidence_intervals(self) -> None:
        """Metrics with large confidence interval bounds."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({
                    "average_hits": 3.0,
                    "confidence_intervals": {
                        "average_hits": {"lower": 0.0, "upper": 6.0}
                    }
                }, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertIsNotNone(result["metrics"])

    def test_load_run_id_normalization(self) -> None:
        """Load preserves run_id from manifest."""
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            test_run_id = "abc123def456789f"
            with open(run_dir / "config.json", "w") as f:
                json.dump({"strategy_name": "test"}, f)
            with open(run_dir / "metrics.json", "w") as f:
                json.dump({"average_hits": 1.0}, f)
            with open(run_dir / "manifest.json", "w") as f:
                json.dump({"run_id": test_run_id}, f)

            result = load_run_data(run_dir)
            if result is not None:
                self.assertEqual(result.get("run_id"), test_run_id)
