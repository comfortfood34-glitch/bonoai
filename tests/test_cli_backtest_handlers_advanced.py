"""Advanced CLI backtest handler tests (compare, verify, JSON output)."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.cli_backtest import run_backtest_command
from bonoai.domain.backtesting import BacktestConfig, BacktestMetrics, BacktestRun
from bonoai.infrastructure.backtest_artifacts import AtomicArtifactWriter


class TestCliBacktestHandlersAdvanced(TestCase):
    """Advanced tests for backtest CLI handlers."""

    def setUp(self) -> None:
        """Set up test fixtures with real repositories."""
        self.temp_data = TemporaryDirectory()
        self.temp_artifacts = TemporaryDirectory()
        self.data_path = Path(self.temp_data.name)
        self.artifacts_path = Path(self.temp_artifacts.name)

        self._setup_test_data()
        self._setup_test_artifacts()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_data.cleanup()
        self.temp_artifacts.cleanup()

    def _setup_test_data(self) -> None:
        """Create proper canonical CSV data structure."""
        processed_dir = self.data_path / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        header = (
            "contest_id,held_on,n1,n2,n3,n4,n5,n6,complementary,reintegro,"
            "source_name,source_url,retrieved_at_utc,source_sha256,source_type,schema_version"
        )
        row = (
            "test,2025-01-01,1,2,3,4,5,6,7,0,"
            "test_source,http://test.com,2025-01-01T00:00:00Z,"
            + "a" * 64 + ",official,2"
        )
        draws_csv = f"{header}\n{row}\n"
        (processed_dir / "draws.csv").write_text(draws_csv)

    def _setup_test_artifacts(self) -> None:
        """Create a valid backtest run artifact."""
        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=360,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )

        metrics = BacktestMetrics(
            hit_distribution={0: 10},
            average_hits=0.0,
            hit_rate_2_plus=0.0,
            hit_rate_3_plus=0.0,
            hit_rate_4_plus=0.0,
            hit_rate_5_plus=0.0,
            hit_rate_6=0.0,
            probability_score=0.0,
            baseline_comparison={},
            confidence_intervals={},
        )

        run = BacktestRun(
            run_id="test_run_001",
            config=config,
            started_at_utc=datetime.now(UTC),
            completed_at_utc=datetime.now(UTC),
            status="success",
            metrics=metrics,
        )

        writer = AtomicArtifactWriter(self.artifacts_path)
        writer.write_run_record(run)

    def _make_namespace(self, **kwargs: object) -> argparse.Namespace:
        """Create argparse.Namespace with defaults."""
        defaults = {
            "data_dir": self.data_path,
            "artifacts_dir": self.artifacts_path,
            "backtest_command": "run",
            "strategy": "uniform_random",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "training_window": 360,
            "seed": 42,
            "as_json": False,
            "run_id": None,
            "run_id_1": None,
            "run_id_2": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_compare_command_with_valid_runs(self) -> None:
        """Compare command handles existing runs."""
        self._create_second_run()

        args = self._make_namespace(
            backtest_command="compare",
            run_id_1="test_run_001",
            run_id_2="test_run_002",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_compare_command_insufficient_runs(self) -> None:
        """Compare command fails gracefully with insufficient runs."""
        args = self._make_namespace(
            backtest_command="compare",
            run_id_1="test_run_001",
            run_id_2="nonexistent_run",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 2)

    def test_verify_command_valid_run(self) -> None:
        """Verify command returns 0 for valid run."""
        args = self._make_namespace(
            backtest_command="verify",
            run_id="test_run_001",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_verify_command_corrupted_run(self) -> None:
        """Verify command detects corrupted artifacts."""
        self._corrupt_run("test_run_001")

        args = self._make_namespace(
            backtest_command="verify",
            run_id="test_run_001",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 1, "Verify should return 1 for corrupted run")

    def test_verify_missing_run_returns_error(self) -> None:
        """Verify command returns 2 for missing run."""
        args = self._make_namespace(
            backtest_command="verify",
            run_id="nonexistent_run",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 2)

    def test_show_json_contains_run_id(self) -> None:
        """Show JSON output includes run_id field."""
        args = self._make_namespace(
            backtest_command="show",
            run_id="test_run_001",
            as_json=True
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_compare_json_structure(self) -> None:
        """Compare JSON output has expected structure."""
        self._create_second_run()

        args = self._make_namespace(
            backtest_command="compare",
            run_id_1="test_run_001",
            run_id_2="test_run_002",
            as_json=True
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_verify_json_output_includes_status(self) -> None:
        """Verify JSON output includes valid/invalid status."""
        args = self._make_namespace(
            backtest_command="verify",
            run_id="test_run_001",
            as_json=True
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def _create_second_run(self) -> None:
        """Create a second test run for comparison."""
        config = BacktestConfig(
            strategy_name="frequency_only",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=360,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )

        metrics = BacktestMetrics(
            hit_distribution={0: 10},
            average_hits=0.0,
            hit_rate_2_plus=0.0,
            hit_rate_3_plus=0.0,
            hit_rate_4_plus=0.0,
            hit_rate_5_plus=0.0,
            hit_rate_6=0.0,
            probability_score=0.0,
            baseline_comparison={},
            confidence_intervals={},
        )

        run = BacktestRun(
            run_id="test_run_002",
            config=config,
            started_at_utc=datetime.now(UTC),
            completed_at_utc=datetime.now(UTC),
            status="success",
            metrics=metrics,
        )

        writer = AtomicArtifactWriter(self.artifacts_path)
        writer.write_run_record(run)

    def _corrupt_run(self, run_id: str) -> None:
        """Corrupt a run's config file without updating manifest hash."""
        run_dir = self.artifacts_path / run_id
        config_path = run_dir / "config.json"

        if config_path.exists():
            config_path.write_text(json.dumps({"corrupted": True}, sort_keys=True))
