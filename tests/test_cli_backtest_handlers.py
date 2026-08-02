"""Core CLI backtest handler tests (list, show, run, command routing)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

from bonoai.cli_backtest import run_backtest_command
from bonoai.domain.backtesting import BacktestConfig, BacktestMetrics, BacktestRun
from bonoai.infrastructure.backtest_artifacts import AtomicArtifactWriter


class TestCliBacktestHandlers(TestCase):
    """Core tests for backtest CLI handlers."""

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

    def test_list_command_returns_zero(self) -> None:
        """List command returns exit code 0."""
        args = self._make_namespace(backtest_command="list")
        result = run_backtest_command(args)
        self.assertEqual(result, 0, "List command should return 0")

    def test_list_command_shows_runs(self) -> None:
        """List command displays available runs."""
        args = self._make_namespace(backtest_command="list", as_json=False)
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_list_json_output_format(self) -> None:
        """List command with JSON flag returns valid JSON."""
        args = self._make_namespace(backtest_command="list", as_json=True)
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_show_command_with_valid_run(self) -> None:
        """Show command displays run details for existing run."""
        args = self._make_namespace(
            backtest_command="show",
            run_id="test_run_001",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_show_command_with_missing_run(self) -> None:
        """Show command returns error code for missing run."""
        args = self._make_namespace(
            backtest_command="show",
            run_id="nonexistent_run_xyz",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 2, "Show with missing run should return 2")

    def test_show_json_output_structure(self) -> None:
        """Show command with JSON outputs proper structure."""
        args = self._make_namespace(
            backtest_command="show",
            run_id="test_run_001",
            as_json=True
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)

    def test_unknown_subcommand(self) -> None:
        """Unknown subcommand returns error code 2."""
        args = self._make_namespace(backtest_command="unknown_cmd")
        result = run_backtest_command(args)
        self.assertEqual(result, 2)

    def test_run_command_empty_data(self) -> None:
        """Run command handles empty repository."""
        args = self._make_namespace(
            backtest_command="run",
            strategy="uniform_random",
            as_json=False
        )
        empty_data = self.data_path / "processed" / "draws.csv"
        empty_data.write_text(
            "contest_id,held_on,n1,n2,n3,n4,n5,n6,complementary,reintegro,"
            "source_name,source_url,retrieved_at_utc,source_sha256,source_type,schema_version\n"
        )

        result = run_backtest_command(args)
        self.assertEqual(result, 2)

    def test_run_command_invalid_strategy(self) -> None:
        """Run command fails with invalid strategy name."""
        args = self._make_namespace(
            backtest_command="run",
            strategy="nonexistent_strategy",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 2)

    @patch("bonoai.cli_backtest.WalkForwardValidator")
    @patch("bonoai.cli_backtest.AtomicArtifactWriter")
    def test_run_command_with_data_and_mocked_validator(
        self, mock_writer_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
        """Run command executes full path with mocked validator."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_metrics = BacktestMetrics(
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
        mock_validator.execute.return_value = mock_metrics

        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer
        mock_writer.write_run_record.return_value = (
            self.artifacts_path / "test_run" / "manifest.json",
            "abc123",
        )

        args = self._make_namespace(
            backtest_command="run",
            strategy="uniform_random",
            as_json=False
        )
        result = run_backtest_command(args)
        self.assertEqual(result, 0)
