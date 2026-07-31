"""Tests for walk-forward validation without temporal leakage."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.walk_forward import TemporalLeakageDetected, WalkForwardValidator
from bonoai.domain.backtesting import BacktestConfig
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw


class TestWalkForwardValidator(TestCase):
    """Verify temporal integrity and walk-forward correctness."""

    def _make_draw(
        self, contest_id: str, held_on: date,
        numbers: tuple[int, ...] = (1, 2, 3, 4, 5, 6)
    ) -> CanonicalDrawRecord:
        """Helper to create a draw."""
        # Find a complementary number not in numbers
        complementary = 8
        while complementary in numbers:
            complementary += 1
        draw = Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=numbers,
            complementary=complementary,
            reintegro=0,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        return CanonicalDrawRecord(draw=draw, provenances=(provenance,))

    def test_validator_with_empty_draws_raises_error(self) -> None:
        """Empty draws raise ValueError."""
        with self.assertRaises(ValueError):
            WalkForwardValidator(())

    def test_validator_with_unsorted_draws_raises_error(self) -> None:
        """Unsorted draws raise ValueError."""
        d1 = self._make_draw("id1", date(2025, 1, 2))
        d2 = self._make_draw("id2", date(2025, 1, 1))
        with self.assertRaises(ValueError):
            WalkForwardValidator((d1, d2))

    def test_get_training_data_excludes_target_and_future(self) -> None:
        """Training data excludes target and future dates."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 11)
        )
        validator = WalkForwardValidator(draws)

        target = date(2025, 1, 5)
        training = validator.get_training_data(target, training_window_days=10)

        self.assertTrue(all(d.draw.held_on < target for d in training))
        self.assertEqual(len(training), 4)  # Jan 1-4

    def test_get_training_data_missing_target_raises_leakage_error(self) -> None:
        """Missing target date raises TemporalLeakageDetected."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 5)
        )
        validator = WalkForwardValidator(draws)

        with self.assertRaises(TemporalLeakageDetected):
            validator.get_training_data(date(2025, 2, 1), training_window_days=10)

    def test_get_training_data_insufficient_history_raises_leakage_error(self) -> None:
        """Insufficient training history raises TemporalLeakageDetected."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 3)
        )
        validator = WalkForwardValidator(draws)

        # Request first draw with 10-day window - no prior data available
        with self.assertRaises(TemporalLeakageDetected):
            validator.get_training_data(date(2025, 1, 1), training_window_days=10)

    def test_get_target_draw_returns_correct_draw(self) -> None:
        """get_target_draw returns the draw for target date."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 5)
        )
        validator = WalkForwardValidator(draws)

        target = validator.get_target_draw(date(2025, 1, 3))
        self.assertEqual(target.draw.contest_id, "id3")

    def test_execute_with_deterministic_strategy(self) -> None:
        """Execute computes metrics from deterministic strategy."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 11)
        )
        validator = WalkForwardValidator(draws)

        def strategy(
            training_draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            # Always return same numbers
            return (1, 2, 3, 4, 5, 6)

        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-05",
            end_date="2025-01-10",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )

        metrics = validator.execute(config, strategy)
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.average_hits, 0)

    def test_count_hits_calculates_correctly(self) -> None:
        """Hit counting is correct."""
        strategy = (1, 2, 3, 4, 5, 6)
        actual = (1, 2, 3, 7, 8, 9)
        hits = WalkForwardValidator._count_hits(strategy, actual)
        self.assertEqual(hits, 3)

    def test_count_hits_no_overlap(self) -> None:
        """Hit counting with no overlap."""
        strategy = (1, 2, 3, 4, 5, 6)
        actual = (7, 8, 9, 10, 11, 12)
        hits = WalkForwardValidator._count_hits(strategy, actual)
        self.assertEqual(hits, 0)

    def test_metrics_have_valid_distributions(self) -> None:
        """Computed metrics have valid hit distributions."""
        # Create varied draws so strategy can produce different hit counts
        draws = tuple(
            self._make_draw(
                f"id{i}",
                date(2025, 1, i),
                numbers=(
                    (1, 2, 3, 4, 5, 6) if i % 3 == 0
                    else (10, 11, 12, 13, 14, 15) if i % 3 == 1
                    else (20, 21, 22, 23, 24, 25)
                ),
            )
            for i in range(1, 21)
        )
        validator = WalkForwardValidator(draws)

        def varied_strategy(
            training_draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            # Return different patterns
            seed_val = int(seed) % 3
            if seed_val == 0:
                return (1, 2, 3, 4, 5, 6)
            else:
                return (10, 20, 30, 40, 45, 49)

        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-05",
            end_date="2025-01-20",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )

        metrics = validator.execute(config, varied_strategy)
        self.assertIn(0, metrics.hit_distribution)
        self.assertGreater(len(metrics.hit_distribution), 0)

    def test_execute_skips_missing_target_dates(self) -> None:
        """Execute skips dates without draws in dataset."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in [1, 3, 5]  # Missing 2, 4
        )
        validator = WalkForwardValidator(draws)

        def strategy(
            training_draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 2, 3, 4, 5, 6)

        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-05",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )

        metrics = validator.execute(config, strategy)
        # Should have processed dates 3 and 5 (1 only has training data from Jan 1)
        self.assertGreater(len(metrics.hit_distribution), 0)

    def test_execute_no_valid_target_dates_raises_error(self) -> None:
        """Execute raises ValueError when no valid target dates."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 4)
        )
        validator = WalkForwardValidator(draws)

        def strategy(
            training_draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 2, 3, 4, 5, 6)

        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-02-01",
            end_date="2025-02-10",
            training_window_days=10,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )

        with self.assertRaises(ValueError):
            validator.execute(config, strategy)
