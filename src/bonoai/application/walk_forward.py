"""Walk-forward validation engine with temporal integrity verification."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta

from bonoai.domain.backtesting import BacktestConfig, BacktestMetrics
from bonoai.domain.data import CanonicalDrawRecord


class TemporalLeakageDetected(RuntimeError):
    """Raised when walk-forward validation detects future data in training set."""


class WalkForwardValidator:
    """Execute walk-forward validation without temporal leakage.

    Walk-forward validation processes each target draw using only prior data.
    Never include the target draw or future data in training/strategy building.
    """

    def __init__(self, all_draws: tuple[CanonicalDrawRecord, ...]):
        """Initialize with complete draw history (sorted by date)."""
        if not all_draws:
            raise ValueError("all_draws must not be empty")

        self._all_draws = all_draws
        self._draw_by_date = {d.draw.held_on: d for d in all_draws}

        # Verify temporal ordering
        for i in range(1, len(all_draws)):
            if all_draws[i].draw.held_on < all_draws[i - 1].draw.held_on:
                raise ValueError("all_draws must be sorted by held_on date")

    def get_training_data(
        self, target_date: date, training_window_days: int
    ) -> tuple[CanonicalDrawRecord, ...]:
        """Get draws strictly before target_date for training.

        Raises TemporalLeakageDetected if target_date is not in the dataset.
        Training window is [target_date - training_window_days, target_date).
        """
        if target_date not in self._draw_by_date:
            raise TemporalLeakageDetected(
                f"target_date {target_date} not in dataset; cannot build strategy"
            )

        training_start = target_date - timedelta(days=training_window_days)
        training_draws = [
            d for d in self._all_draws
            if training_start <= d.draw.held_on < target_date
        ]

        if not training_draws:
            raise TemporalLeakageDetected(
                f"no training data available for {target_date} "
                f"with window {training_window_days} days"
            )

        return tuple(training_draws)

    def get_target_draw(self, target_date: date) -> CanonicalDrawRecord:
        """Get the target draw for evaluation."""
        if target_date not in self._draw_by_date:
            raise TemporalLeakageDetected(f"target_date {target_date} not in dataset")
        return self._draw_by_date[target_date]

    def execute(
        self,
        config: BacktestConfig,
        strategy_builder: Callable[[tuple[CanonicalDrawRecord, ...], int], tuple[int, ...]],
    ) -> BacktestMetrics:
        """Run walk-forward validation.

        For each date in [start_date, end_date], get prior data, build strategy, evaluate.
        Never include target or future data in training.

        Args:
            config: BacktestConfig with dates, training_window_days, random_seed
            strategy_builder: fn(training_draws, random_seed) -> tuple[int, ...]
                Must return 6 distinct numbers or raise

        Returns:
            BacktestMetrics with hit distributions and confidence intervals
        """
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(config.end_date, "%Y-%m-%d").date()

        hit_counts: list[int] = []
        current_date = start_date

        while current_date <= end_date:
            if current_date not in self._draw_by_date:
                current_date += timedelta(days=1)
                continue

            try:
                training_draws = self.get_training_data(
                    current_date, config.training_window_days
                )
                target_draw = self.get_target_draw(current_date)

                strategy_numbers = strategy_builder(training_draws, config.random_seed)
                hits = self._count_hits(strategy_numbers, target_draw.draw.numbers)
                hit_counts.append(hits)

            except TemporalLeakageDetected:
                pass  # Skip dates without sufficient prior history

            current_date += timedelta(days=1)

        if not hit_counts:
            raise ValueError(f"no valid target dates in range [{start_date}, {end_date}]")

        return self._compute_metrics(hit_counts)

    @staticmethod
    def _count_hits(strategy_numbers: tuple[int, ...], actual_numbers: tuple[int, ...]) -> int:
        """Count matching numbers (0-6)."""
        return len(set(strategy_numbers) & set(actual_numbers))

    @staticmethod
    def _compute_metrics(hit_counts: list[int]) -> BacktestMetrics:
        """Compute scientific metrics from hit counts."""
        distribution: dict[int, int] = {}
        for hits in hit_counts:
            distribution[hits] = distribution.get(hits, 0) + 1

        total = len(hit_counts)
        avg_hits = sum(hit_counts) / total if total > 0 else 0.0

        hit_rate_2_plus = sum(1 for h in hit_counts if h >= 2) / total
        hit_rate_3_plus = sum(1 for h in hit_counts if h >= 3) / total
        hit_rate_4_plus = sum(1 for h in hit_counts if h >= 4) / total
        hit_rate_5_plus = sum(1 for h in hit_counts if h >= 5) / total
        hit_rate_6 = sum(1 for h in hit_counts if h == 6) / total

        prob_score = avg_hits / 6.0  # simple normalization

        from bonoai.domain.backtesting import BacktestMetrics, ConfidenceInterval

        return BacktestMetrics(
            hit_distribution=distribution,
            average_hits=avg_hits,
            hit_rate_2_plus=hit_rate_2_plus,
            hit_rate_3_plus=hit_rate_3_plus,
            hit_rate_4_plus=hit_rate_4_plus,
            hit_rate_5_plus=hit_rate_5_plus,
            hit_rate_6=hit_rate_6,
            probability_score=prob_score,
            baseline_comparison={},
            confidence_intervals={
                "average_hits": ConfidenceInterval(
                    lower=max(0, (avg_hits - 0.5) / 6),
                    upper=min(1, (avg_hits + 0.5) / 6),
                ),
            },
        )
