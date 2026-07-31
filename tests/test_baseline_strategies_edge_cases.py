"""Tests for baseline_strategies edge cases."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.baseline_strategies import (
    delay_only_strategy,
    frequency_only_strategy,
    mixed_frequency_delay_strategy,
)
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw


class TestBaselineStrategiesEdgeCases(TestCase):
    """Test baseline strategies edge cases for missing branches."""

    def _make_draw(
        self, contest_id: str, held_on: date,
        numbers: tuple[int, ...] = (1, 2, 3, 4, 5, 6)
    ) -> CanonicalDrawRecord:
        """Create a test draw."""
        complementary = 7
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
            
        )
        return CanonicalDrawRecord(draw=draw, provenance=provenance,))

    def test_frequency_only_with_very_few_unique_numbers(self) -> None:
        """Frequency strategy with only 3 unique numbers (need 6)."""
        draws = tuple(
            self._make_draw(
                f"id{i}",
                date(2025, 1, i),
                numbers=(10, 11, 12, 13, 14, 15) if i % 2 == 0 else (20, 21, 22, 23, 24, 25),
            )
            for i in range(1, 3)
        )

        result = frequency_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
        self.assertTrue(all(1 <= n <= 50 for n in result))

    def test_delay_only_with_all_same_numbers(self) -> None:
        """Delay strategy when all draws have identical numbers."""
        draws = tuple(
            self._make_draw(
                f"id{i}",
                date(2025, 1, i),
                numbers=(10, 11, 12, 13, 14, 15),
            )
            for i in range(1, 5)
        )

        result = delay_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(set(result), {10, 11, 12, 13, 14, 15})

    def test_mixed_with_limited_unique_numbers(self) -> None:
        """Mixed strategy with draws having limited unique numbers."""
        draws = tuple(
            self._make_draw(
                f"id{i}",
                date(2025, 1, i),
                numbers=(1, 2, 3, 4, 5, 6) if i < 3 else (7, 8, 9, 10, 11, 12),
            )
            for i in range(1, 4)
        )

        result = mixed_frequency_delay_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)

    def test_frequency_only_complete_coverage(self) -> None:
        """Frequency strategy needing all 6 numbers filled from random."""
        draws = tuple(
            self._make_draw(
                f"id{i}",
                date(2025, 1, i),
                numbers=(1, 2, 3, 4, 5, 6) if i == 1 else (10, 11, 12, 13, 14, 15),
            )
            for i in range(1, 3)
        )

        result = frequency_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
        self.assertTrue(all(1 <= n <= 50 for n in result))

    def test_delay_only_with_no_delays_recorded(self) -> None:
        """Delay strategy when delay calculation returns empty."""
        # Empty draws list edge case handled differently
        draws = ()
        result = delay_only_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)

    def test_mixed_with_empty_frequency_counter(self) -> None:
        """Mixed strategy with no frequencies recorded."""
        draws = ()
        result = mixed_frequency_delay_strategy(draws, 42)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(set(result)), 6)
