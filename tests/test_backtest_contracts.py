"""Tests for backtesting contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from bonoai.domain.backtesting import (
    BacktestConfig,
    BacktestContractError,
    BacktestMetrics,
    BacktestRun,
    ConfidenceInterval,
)


class TestBacktestConfigValidation(TestCase):
    """Validate BacktestConfig contract enforcement."""

    def test_valid_config_creates_successfully(self) -> None:
        """Valid config is accepted."""
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
        self.assertEqual(config.strategy_name, "uniform_random")

    def test_invalid_strategy_raises_error(self) -> None:
        """Invalid strategy name raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="invalid_strategy",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_date_format_raises_error(self) -> None:
        """Invalid date format raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="01/01/2025",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_start_after_end_raises_error(self) -> None:
        """Start date >= end date raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-12-31",
                end_date="2025-01-01",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_negative_training_window_raises_error(self) -> None:
        """Negative training window raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=-1,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_sha256_raises_error(self) -> None:
        """Non-hex SHA-256 raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="zzzz" + "a" * 60,
                code_commit_sha="b" * 64,
            )

    def test_negative_random_seed_raises_error(self) -> None:
        """Negative random_seed raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=-1,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_tickets_per_draw_zero_raises_error(self) -> None:
        """Zero tickets_per_draw raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=0,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_tickets_per_draw_too_large_raises_error(self) -> None:
        """tickets_per_draw > 1000 raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=1001,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )


class TestConfidenceInterval(TestCase):
    """Validate ConfidenceInterval contract."""

    def test_valid_interval_creates_successfully(self) -> None:
        """Valid CI is accepted."""
        ci = ConfidenceInterval(lower=0.1, upper=0.9)
        self.assertEqual(ci.lower, 0.1)

    def test_lower_greater_than_upper_raises_error(self) -> None:
        """lower > upper raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            ConfidenceInterval(lower=0.9, upper=0.1)

    def test_out_of_range_raises_error(self) -> None:
        """Values outside [0, 1] raise BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            ConfidenceInterval(lower=-0.1, upper=0.5)


class TestBacktestMetrics(TestCase):
    """Validate BacktestMetrics contract."""

    def test_valid_metrics_creates_successfully(self) -> None:
        """Valid metrics are accepted."""
        metrics = BacktestMetrics(
            hit_distribution={0: 10, 1: 5, 2: 3},
            average_hits=0.5,
            hit_rate_2_plus=0.2,
            hit_rate_3_plus=0.1,
            hit_rate_4_plus=0.05,
            hit_rate_5_plus=0.01,
            hit_rate_6=0.0,
            probability_score=0.1,
            baseline_comparison={},
            confidence_intervals={"avg": ConfidenceInterval(0.0, 1.0)},
        )
        self.assertEqual(metrics.average_hits, 0.5)

    def test_empty_distribution_raises_error(self) -> None:
        """Empty hit_distribution raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestMetrics(
                hit_distribution={},
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

    def test_invalid_hit_count_raises_error(self) -> None:
        """Hit count outside [0, 6] raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestMetrics(
                hit_distribution={7: 1},
                average_hits=0.5,
                hit_rate_2_plus=0.0,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.0,
                baseline_comparison={},
                confidence_intervals={},
            )

    def test_negative_hit_frequency_raises_error(self) -> None:
        """Negative hit frequency raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestMetrics(
                hit_distribution={0: -1},
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

    def test_average_hits_out_of_range_raises_error(self) -> None:
        """average_hits outside [0, 6] raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestMetrics(
                hit_distribution={0: 10},
                average_hits=7.0,
                hit_rate_2_plus=0.0,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.0,
                baseline_comparison={},
                confidence_intervals={},
            )

    def test_hit_rate_out_of_range_raises_error(self) -> None:
        """hit_rate outside [0, 1] raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestMetrics(
                hit_distribution={0: 10},
                average_hits=0.5,
                hit_rate_2_plus=1.5,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.0,
                baseline_comparison={},
                confidence_intervals={},
            )

    def test_probability_score_out_of_range_raises_error(self) -> None:
        """probability_score outside [0, 1] raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestMetrics(
                hit_distribution={0: 10},
                average_hits=0.5,
                hit_rate_2_plus=0.0,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=1.5,
                baseline_comparison={},
                confidence_intervals={},
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
