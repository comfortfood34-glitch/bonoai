"""Walk-forward validation leakage detection tests."""

from datetime import UTC, date, datetime
from unittest import TestCase

from bonoai.application.walk_forward import TemporalLeakageDetected, WalkForwardValidator
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw


class TestTemporalLeakageDetection(TestCase):
    """Verify temporal leakage detection in walk-forward validation."""

    def _make_draw(
        self, contest_id: str, held_on: date,
        numbers: tuple[int, ...] = (1, 2, 3, 4, 5, 6)
    ) -> CanonicalDrawRecord:
        """Helper to create a draw."""
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

    def test_target_date_not_in_dataset_raises_temporal_leakage(self) -> None:
        """Training request for non-existent target date raises."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 5)
        )
        validator = WalkForwardValidator(draws)
        with self.assertRaises(TemporalLeakageDetected):
            validator.get_training_data(date(2025, 2, 1), training_window_days=30)

    def test_insufficient_historical_data_raises_temporal_leakage(self) -> None:
        """Request with insufficient prior data raises temporal leakage."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 4)
        )
        validator = WalkForwardValidator(draws)
        with self.assertRaises(TemporalLeakageDetected):
            validator.get_training_data(date(2025, 1, 1), training_window_days=30)

    def test_training_data_never_includes_target_date(self) -> None:
        """Training data must strictly exclude target date."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 11)
        )
        validator = WalkForwardValidator(draws)
        target = date(2025, 1, 6)
        training = validator.get_training_data(target, training_window_days=30)
        self.assertFalse(any(d.draw.held_on == target for d in training))

    def test_training_data_never_includes_future_dates(self) -> None:
        """Training data must strictly exclude future dates."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 11)
        )
        validator = WalkForwardValidator(draws)
        target = date(2025, 1, 6)
        training = validator.get_training_data(target, training_window_days=30)
        self.assertTrue(all(d.draw.held_on < target for d in training))

    def test_get_target_draw_for_missing_date_raises_leakage_error(self) -> None:
        """Getting target draw for non-existent date raises."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 5)
        )
        validator = WalkForwardValidator(draws)
        with self.assertRaises(TemporalLeakageDetected):
            validator.get_target_draw(date(2025, 3, 1))

    def test_window_boundary_respects_training_period_start(self) -> None:
        """Training window includes data exactly at window start."""
        draws = tuple(
            self._make_draw(f"id{i}", date(2025, 1, i))
            for i in range(1, 11)
        )
        validator = WalkForwardValidator(draws)
        target = date(2025, 1, 6)
        training = validator.get_training_data(target, training_window_days=3)
        dates_in_training = {d.draw.held_on for d in training}
        self.assertIn(date(2025, 1, 3), dates_in_training)

    def test_unsorted_draws_raises_on_initialization(self) -> None:
        """Unsorted draw list raises ValueError on init."""
        d1 = self._make_draw("id1", date(2025, 1, 5))
        d2 = self._make_draw("id2", date(2025, 1, 1))
        with self.assertRaises(ValueError):
            WalkForwardValidator((d1, d2))

    def test_empty_draws_raises_on_initialization(self) -> None:
        """Empty draw list raises ValueError on init."""
        with self.assertRaises(ValueError):
            WalkForwardValidator(())
