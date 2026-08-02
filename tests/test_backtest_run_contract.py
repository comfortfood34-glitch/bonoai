"""Tests for BacktestRun contract."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from bonoai.domain.backtesting import (
    BacktestConfig,
    BacktestContractError,
    BacktestMetrics,
    BacktestRun,
)


class TestBacktestRun(TestCase):
    """Validate BacktestRun contract."""

    def test_successful_run_with_metrics(self) -> None:
        """Successful run requires metrics."""
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
        now = datetime.now(UTC)
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
            run_id="abc123",
            config=config,
            started_at_utc=now,
            completed_at_utc=now,
            status="success",
            metrics=metrics,
        )
        self.assertEqual(run.status, "success")

    def test_successful_run_without_metrics_raises_error(self) -> None:
        """Successful run without metrics raises BacktestContractError."""
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
        now = datetime.now(UTC)
        with self.assertRaises(BacktestContractError):
            BacktestRun(
                run_id="abc123",
                config=config,
                started_at_utc=now,
                completed_at_utc=now,
                status="success",
                metrics=None,
            )

    def test_completed_before_started_raises_error(self) -> None:
        """Completed time < started time raises BacktestContractError."""
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
        now = datetime.now(UTC)
        earlier = datetime(2020, 1, 1, tzinfo=UTC)
        with self.assertRaises(BacktestContractError):
            BacktestRun(
                run_id="abc123",
                config=config,
                started_at_utc=now,
                completed_at_utc=earlier,
                status="failed",
            )

    def test_empty_run_id_raises_error(self) -> None:
        """Empty run_id raises BacktestContractError."""
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
        now = datetime.now(UTC)
        with self.assertRaises(BacktestContractError):
            BacktestRun(
                run_id="",
                config=config,
                started_at_utc=now,
                completed_at_utc=now,
                status="failed",
            )

    def test_timezone_naive_started_raises_error(self) -> None:
        """Timezone-naive started_at_utc raises BacktestContractError."""
        from datetime import datetime as dt
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
        now = datetime.now(UTC)
        naive_time = dt(2025, 1, 1)
        with self.assertRaises(BacktestContractError):
            BacktestRun(
                run_id="abc123",
                config=config,
                started_at_utc=naive_time,
                completed_at_utc=now,
                status="failed",
            )

    def test_timezone_naive_completed_raises_error(self) -> None:
        """Timezone-naive completed_at_utc raises BacktestContractError."""
        from datetime import datetime as dt
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
        now = datetime.now(UTC)
        naive_time = dt(2025, 1, 1)
        with self.assertRaises(BacktestContractError):
            BacktestRun(
                run_id="abc123",
                config=config,
                started_at_utc=now,
                completed_at_utc=naive_time,
                status="failed",
            )

    def test_failed_run_with_metrics_raises_error(self) -> None:
        """Failed run with metrics raises BacktestContractError."""
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
        now = datetime.now(UTC)
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
        with self.assertRaises(BacktestContractError):
            BacktestRun(
                run_id="abc123",
                config=config,
                started_at_utc=now,
                completed_at_utc=now,
                status="failed",
                metrics=metrics,
            )
