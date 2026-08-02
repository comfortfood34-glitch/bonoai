"""Tests for BacktestMetrics contract."""

from __future__ import annotations

from unittest import TestCase

from bonoai.domain.backtesting import (
    BacktestContractError,
    BacktestMetrics,
    ConfidenceInterval,
)


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
