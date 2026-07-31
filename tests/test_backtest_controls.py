"""Tests for scientific control mechanisms."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.backtest_controls import LeakageTest, NegativeControl, ReproducibilityTest
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw


class TestLeakageTest(TestCase):
    """Verify temporal leakage detection."""

    def _make_draw(self, contest_id: str, held_on: date) -> CanonicalDrawRecord:
        """Helper to create a draw."""
        draw = Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=8,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        return CanonicalDrawRecord(draw=draw, provenances=(provenance,))

    def test_deterministic_strategy_passes_test(self) -> None:
        """Deterministic strategy passes leakage test."""
        def deterministic_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 2, 3, 4, 5, 6)

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_det, _msg = LeakageTest.verify_strategy_callable_is_deterministic(
            deterministic_strategy, draws
        )
        self.assertTrue(is_det)

    def test_non_deterministic_strategy_fails_test(self) -> None:
        """Non-deterministic strategy fails leakage test."""
        import random

        def non_deterministic_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            # Ignores seed, truly random
            return tuple(sorted(random.sample(range(1, 50), 6)))

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_det, _msg = LeakageTest.verify_strategy_callable_is_deterministic(
            non_deterministic_strategy, draws
        )
        self.assertFalse(is_det)

    def test_strategy_with_wrong_output_fails_test(self) -> None:
        """Strategy returning wrong output fails test."""
        def bad_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 2, 3, 4, 5)  # Only 5 numbers

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_det, _msg = LeakageTest.verify_strategy_callable_is_deterministic(
            bad_strategy, draws
        )
        self.assertFalse(is_det)

    def test_strategy_with_duplicate_numbers_fails_test(self) -> None:
        """Strategy returning duplicates fails test."""
        def bad_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 1, 1, 1, 1, 1)

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_det, _msg = LeakageTest.verify_strategy_callable_is_deterministic(
            bad_strategy, draws
        )
        self.assertFalse(is_det)

    def test_strategy_with_out_of_range_fails_test(self) -> None:
        """Strategy returning out-of-range numbers fails test."""
        def bad_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 2, 3, 4, 5, 60)  # 60 > 49

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_det, _msg = LeakageTest.verify_strategy_callable_is_deterministic(
            bad_strategy, draws
        )
        self.assertFalse(is_det)

    def test_insufficient_draws_returns_true(self) -> None:
        """Insufficient draws to test determinism returns True."""
        def dummy_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            return (1, 2, 3, 4, 5, 6)

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 2))
        is_det, msg = LeakageTest.verify_strategy_callable_is_deterministic(
            dummy_strategy, draws
        )
        self.assertTrue(is_det)
        self.assertIn("insufficient", msg)

    def test_strategy_raising_exception_fails(self) -> None:
        """Strategy that raises exception fails test."""
        def exception_strategy(
            draws: tuple[CanonicalDrawRecord, ...], seed: int
        ) -> tuple[int, ...]:
            raise ValueError("test error")

        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_det, msg = LeakageTest.verify_strategy_callable_is_deterministic(
            exception_strategy, draws
        )
        self.assertFalse(is_det)
        self.assertIn("exception", msg)


class TestReproducibilityTest(TestCase):
    """Verify reproducibility testing."""

    def _make_draw(self, contest_id: str, held_on: date) -> CanonicalDrawRecord:
        """Helper to create a draw."""
        draw = Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=8,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        return CanonicalDrawRecord(draw=draw, provenances=(provenance,))

    def test_identical_datasets_pass_reproducibility(self) -> None:
        """Identical datasets pass reproducibility test."""
        draws = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        is_repro, _msg = ReproducibilityTest.can_reproduce_run(draws, draws)
        self.assertTrue(is_repro)

    def test_different_lengths_fail_reproducibility(self) -> None:
        """Different dataset lengths fail test."""
        draws1 = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 5))
        draws2 = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 3))
        is_repro, _msg = ReproducibilityTest.can_reproduce_run(draws1, draws2)
        self.assertFalse(is_repro)

    def test_different_order_fails_reproducibility(self) -> None:
        """Different draw order fails test."""
        draws1 = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 4))
        draws2 = (draws1[2], draws1[0], draws1[1])
        is_repro, _msg = ReproducibilityTest.can_reproduce_run(draws1, draws2)
        self.assertFalse(is_repro)

    def test_contest_id_mismatch_fails_reproducibility(self) -> None:
        """Different contest IDs fail reproducibility test."""
        draws1 = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 4))
        draw_2 = Draw(
            contest_id="different_id",
            held_on=date(2025, 1, 1),
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=8,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        draws2 = (CanonicalDrawRecord(draw=draw_2, provenances=(provenance,)), *draws1[1:])
        is_repro, _msg = ReproducibilityTest.can_reproduce_run(draws1, draws2)
        self.assertFalse(is_repro)

    def test_held_on_mismatch_fails_reproducibility(self) -> None:
        """Different held_on dates fail reproducibility test."""
        draws1 = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 4))
        draw_2 = Draw(
            contest_id="id1",
            held_on=date(2025, 2, 1),
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=8,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        draws2 = (CanonicalDrawRecord(draw=draw_2, provenances=(provenance,)), *draws1[1:])
        is_repro, _msg = ReproducibilityTest.can_reproduce_run(draws1, draws2)
        self.assertFalse(is_repro)

    def test_numbers_mismatch_fails_reproducibility(self) -> None:
        """Different numbers fail reproducibility test."""
        draws1 = tuple(self._make_draw(f"id{i}", date(2025, 1, i)) for i in range(1, 4))
        draw_2 = Draw(
            contest_id="id1",
            held_on=date(2025, 1, 1),
            numbers=(2, 3, 4, 5, 6, 7),
            complementary=8,
            reintegro=9,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        draws2 = (CanonicalDrawRecord(draw=draw_2, provenances=(provenance,)), *draws1[1:])
        is_repro, _msg = ReproducibilityTest.can_reproduce_run(draws1, draws2)
        self.assertFalse(is_repro)


class TestNegativeControl(TestCase):
    """Verify negative control mechanisms."""

    def _make_draw(self, numbers: tuple[int, ...], held_on: date) -> CanonicalDrawRecord:
        """Helper to create a draw."""
        draw = Draw(
            contest_id="test",
            held_on=held_on,
            numbers=numbers,
            complementary=7,
            reintegro=8,
        )
        provenance = SourceProvenance(
            source_name="test",
            source_url="https://test.com",
            retrieved_at_utc=datetime.now(UTC),
            source_sha256="a" * 64,
            source_type="official",
        )
        return CanonicalDrawRecord(draw=draw, provenances=(provenance,))

    def test_generate_random_draws_preserves_dates(self) -> None:
        """Random control preserves draw dates."""
        draws = tuple(
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, i))
            for i in range(1, 4)
        )
        control_draws = NegativeControl.generate_random_draws(draws, 42)

        self.assertEqual(len(control_draws), len(draws))
        for original, control in zip(draws, control_draws, strict=True):
            self.assertEqual(original.draw.held_on, control.draw.held_on)

    def test_generate_random_draws_randomizes_numbers(self) -> None:
        """Random control changes numbers."""
        draws = tuple(
            self._make_draw((1, 2, 3, 4, 5, 6), date(2025, 1, 1))
            for _ in range(1)
        )
        control_draws = NegativeControl.generate_random_draws(draws, 42)

        # Numbers should be different (very high probability)
        self.assertNotEqual(draws[0].draw.numbers, control_draws[0].draw.numbers)

    def test_compute_baseline_performance(self) -> None:
        """Baseline performance computation."""
        hit_counts = [0, 1, 2, 2, 1, 0, 0, 1, 2, 1]
        baseline = NegativeControl.compute_baseline_performance(hit_counts)

        self.assertIn("average_hits", baseline)
        self.assertIn("hit_rate_2_plus", baseline)
        self.assertEqual(baseline["average_hits"], 1.0)

    def test_compute_baseline_performance_empty(self) -> None:
        """Empty hit counts returns empty dict."""
        baseline = NegativeControl.compute_baseline_performance([])
        self.assertEqual(baseline, {})
