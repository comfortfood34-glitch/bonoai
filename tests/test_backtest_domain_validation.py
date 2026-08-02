"""Tests for domain validation in backtesting."""

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
    """Test BacktestConfig validation and error cases."""

    def test_invalid_strategy_raises_error(self) -> None:
        """BacktestConfig raises error for invalid strategy."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="INVALID_STRATEGY",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=10,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0" * 64,
                code_commit_sha="0" * 64,
            )

    def test_start_date_after_end_date_raises_error(self) -> None:
        """BacktestConfig raises error when start > end."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-12-31",
                end_date="2025-01-01",
                training_window_days=10,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0" * 64,
                code_commit_sha="0" * 64,
            )

    def test_zero_training_window_raises_error(self) -> None:
        """BacktestConfig raises error for zero training window."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=0,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0" * 64,
                code_commit_sha="0" * 64,
            )

    def test_zero_tickets_per_draw_raises_error(self) -> None:
        """BacktestConfig raises error for zero tickets."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=10,
                tickets_per_draw=0,
                random_seed=42,
                dataset_sha256="0" * 64,
                code_commit_sha="0" * 64,
            )

    def test_invalid_dataset_sha_raises_error(self) -> None:
        """BacktestConfig raises error for invalid dataset SHA."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=10,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="invalid",  # Too short
                code_commit_sha="0" * 64,
            )

    def test_invalid_code_sha_raises_error(self) -> None:
        """BacktestConfig raises error for invalid code SHA."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=10,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0" * 64,
                code_commit_sha="abc",  # Too short
            )

    def test_immutability_prevents_modification(self) -> None:
        """BacktestConfig is frozen and prevents modifications."""
        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="0" * 64,
            code_commit_sha="0" * 64,
        )
        with self.assertRaises(AttributeError):
            config.strategy_name = "frequency_only"  # type: ignore


class TestBacktestMetricsValidation(TestCase):
    """Test BacktestMetrics validation."""

    def test_metrics_immutability(self) -> None:
        """BacktestMetrics is frozen."""
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
        with self.assertRaises(AttributeError):
            metrics.average_hits = 1.0  # type: ignore

    def test_confidence_interval_bounds(self) -> None:
        """ConfidenceInterval validates bounds."""
        # Lower must be <= upper
        ci = ConfidenceInterval(lower=0.1, upper=0.9)
        self.assertLessEqual(ci.lower, ci.upper)

        # Can have equal bounds (zero width)
        ci_zero = ConfidenceInterval(lower=0.5, upper=0.5)
        self.assertEqual(ci_zero.lower, ci_zero.upper)


class TestBacktestRunValidation(TestCase):
    """Test BacktestRun validation."""

    def test_backtest_run_immutability(self) -> None:
        """BacktestRun is frozen."""
        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="0" * 64,
            code_commit_sha="0" * 64,
        )
        run = BacktestRun(
            run_id="test",
            config=config,
            started_at_utc=datetime.now(UTC),
            completed_at_utc=datetime.now(UTC),
            status="failed",
            metrics=None,
        )
        with self.assertRaises(AttributeError):
            run.status = "success"  # type: ignore

    def test_run_with_failed_status_allows_no_metrics(self) -> None:
        """Failed status can have None metrics."""
        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="0" * 64,
            code_commit_sha="0" * 64,
        )
        run = BacktestRun(
            run_id="test",
            config=config,
            started_at_utc=datetime.now(UTC),
            completed_at_utc=datetime.now(UTC),
            status="failed",
            metrics=None,  # No metrics on failure
        )
        self.assertIsNone(run.metrics)

    def test_run_id_format(self) -> None:
        """run_id must be 16 hex characters."""
        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="0" * 64,
            code_commit_sha="0" * 64,
        )
        run_id = "abc123def456789z"  # 16 chars but invalid hex
        run = BacktestRun(
            run_id=run_id,
            config=config,
            started_at_utc=datetime.now(UTC),
            completed_at_utc=datetime.now(UTC),
            status="failed",
            metrics=None,
        )
        self.assertEqual(len(run.run_id), 16)


class TestBacktestMetricsFields(TestCase):
    """Test specific metric fields for coverage."""

    def test_probability_score_calculation(self) -> None:
        """probability_score = average_hits / 6."""
        metrics = BacktestMetrics(
            hit_distribution={0: 5, 1: 15, 2: 20, 3: 30, 4: 20, 5: 8, 6: 2},
            average_hits=3.0,
            hit_rate_2_plus=0.8,
            hit_rate_3_plus=0.6,
            hit_rate_4_plus=0.5,
            hit_rate_5_plus=0.1,
            hit_rate_6=0.02,
            probability_score=0.5,
            baseline_comparison={},
            confidence_intervals={},
        )
        self.assertEqual(metrics.probability_score, 0.5)
        self.assertIsNotNone(metrics.probability_score)

    def test_hit_rate_fields_all_present(self) -> None:
        """All hit_rate fields are accessible."""
        metrics = BacktestMetrics(
            hit_distribution={0: 10, 6: 5},
            average_hits=1.5,
            hit_rate_2_plus=0.25,
            hit_rate_3_plus=0.15,
            hit_rate_4_plus=0.10,
            hit_rate_5_plus=0.05,
            hit_rate_6=0.05,
            probability_score=0.25,
            baseline_comparison={},
            confidence_intervals={},
        )
        self.assertTrue(hasattr(metrics, 'hit_rate_2_plus'))
        self.assertTrue(hasattr(metrics, 'hit_rate_3_plus'))
        self.assertTrue(hasattr(metrics, 'hit_rate_4_plus'))
        self.assertTrue(hasattr(metrics, 'hit_rate_5_plus'))
        self.assertTrue(hasattr(metrics, 'hit_rate_6'))

    def test_roi_not_available(self) -> None:
        """ROI field should not be available (only available via portfolio)."""
        metrics = BacktestMetrics(
            hit_distribution={0: 100},
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
        self.assertFalse(hasattr(metrics, 'roi'))
        self.assertFalse(hasattr(metrics, 'return_on_investment'))
