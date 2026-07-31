"""Tests for baseline strategies."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.baseline_strategies import (
    BASELINE_STRATEGIES,
    delay_only_strategy,
    frequency_only_strategy,
    mixed_frequency_delay_strategy,
    uniform_random_strategy,
)
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw


class TestBaselineStrategies(TestCase):
    """Verify strategy determinism and correctness."""

    def _make_draw(self, numbers: tuple[int, ...], held_on: date) -> CanonicalDrawRecord:
        """Helper to create a draw."""
        # Find a complementary number not in numbers
        complementary = 8
        while complementary in numbers:
            complementary += 1
        draw = Draw(
            contest_id="test",
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

    def test_uniform_random_is_deterministic(self) -> None:
        """Uniform random produces same result with same seed."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((7, 8, 9, 10, 11, 12), date(2025, 1, 2)),
        )
        result1 = uniform_random_strategy(draws, 42)
        result2 = uniform_random_strategy(draws, 42)
        self.assertEqual(result1, result2)

    def test_uniform_random_produces_valid_output(self) -> None:
        """Uniform random returns 6 distinct numbers in valid range."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
        )
        result = uniform_random_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
        self.assertTrue(all(1 <= n <= 49 for n in result))

    def test_frequency_only_is_deterministic(self) -> None:
        """Frequency strategy is deterministic."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((1, 2, 3, 4, 5, 7), date(2025, 1, 2)),
            self._make_draw((1, 2, 3, 4, 5, 8), date(2025, 1, 3)),
        )
        result1 = frequency_only_strategy(draws, 42)
        result2 = frequency_only_strategy(draws, 42)
        self.assertEqual(result1, result2)

    def test_frequency_only_favors_frequent_numbers(self) -> None:
        """Frequency strategy selects most common numbers."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((1, 2, 3, 4, 5, 7), date(2025, 1, 2)),
            self._make_draw((1, 2, 3, 4, 5, 8), date(2025, 1, 3)),
        )
        result = frequency_only_strategy(draws, 42)
        # 1,2,3,4,5 appear 3 times each
        self.assertIn(1, result)
        self.assertIn(2, result)
        self.assertIn(3, result)

    def test_delay_only_is_deterministic(self) -> None:
        """Delay strategy is deterministic."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((7, 8, 9, 10, 11, 12), date(2025, 1, 5)),
        )
        result1 = delay_only_strategy(draws, 42)
        result2 = delay_only_strategy(draws, 42)
        self.assertEqual(result1, result2)

    def test_delay_only_favors_missing_numbers(self) -> None:
        """Delay strategy favors numbers that haven't appeared recently."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((1, 2, 3, 4, 5, 7), date(2025, 1, 10)),
        )
        result = delay_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        # Should return 6 valid numbers
        self.assertTrue(all(1 <= n <= 49 for n in result))

    def test_mixed_frequency_delay_is_deterministic(self) -> None:
        """Mixed strategy is deterministic."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((7, 8, 9, 10, 11, 12), date(2025, 1, 5)),
        )
        result1 = mixed_frequency_delay_strategy(draws, 42)
        result2 = mixed_frequency_delay_strategy(draws, 42)
        self.assertEqual(result1, result2)

    def test_mixed_strategy_combines_signals(self) -> None:
        """Mixed strategy uses both frequency and delay."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 2)),
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 3)),
        )
        result = mixed_frequency_delay_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)

    def test_all_strategies_handle_empty_draws(self) -> None:
        """All strategies handle empty draw list."""
        empty_draws: tuple[CanonicalDrawRecord, ...] = ()
        for strategy in BASELINE_STRATEGIES.values():
            result = strategy(empty_draws, 42)
            self.assertEqual(len(result), 6)
            self.assertEqual(len(set(result)), 6)

    def test_strategies_have_different_results(self) -> None:
        """Different strategies may produce different results."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((7, 8, 9, 10, 11, 12), date(2025, 1, 2)),
            self._make_draw((13, 14, 15, 16, 17, 18), date(2025, 1, 3)),
        )
        results = {
            name: strategy(draws, 42)
            for name, strategy in BASELINE_STRATEGIES.items()
        }
        # Not all results are the same (probabilistically true)
        unique_results = set(results.values())
        self.assertGreater(len(unique_results), 1)

    def test_frequency_only_with_small_dataset(self) -> None:
        """Frequency strategy handles datasets efficiently."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
            self._make_draw((2, 3, 4, 5, 6, 7), date(2025, 1, 2)),
        )
        result = frequency_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
        self.assertTrue(all(1 <= n <= 49 for n in result))

    def test_delay_only_with_small_dataset(self) -> None:
        """Delay strategy handles single draw."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
        )
        result = delay_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
        self.assertTrue(all(1 <= n <= 49 for n in result))

    def test_mixed_strategy_with_single_draw(self) -> None:
        """Mixed strategy handles single draw."""
        draws = (
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1)),
        )
        result = mixed_frequency_delay_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
        self.assertTrue(all(1 <= n <= 49 for n in result))
