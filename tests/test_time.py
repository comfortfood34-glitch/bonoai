from datetime import date
from unittest import TestCase

from bonoai.domain.models import Draw
from bonoai.domain.time import TemporalCutoff


def make_draw(contest_id: str, held_on: date, first_number: int) -> Draw:
    numbers = tuple(range(first_number, first_number + 6))
    complementary = 49 if 49 not in numbers else 48
    return Draw(
        contest_id=contest_id,
        held_on=held_on,
        numbers=numbers,
        complementary=complementary,
        reintegro=0,
    )


class TemporalCutoffTests(TestCase):
    def test_target_and_future_draws_are_invisible(self) -> None:
        past = make_draw("past", date(2026, 1, 1), 1)
        target = make_draw("target", date(2026, 1, 2), 7)
        future = make_draw("future", date(2026, 1, 3), 13)

        visible = TemporalCutoff(target.held_on).visible_draws([future, target, past])

        self.assertEqual(visible, (past,))

    def test_guard_rejects_target_draw(self) -> None:
        target = make_draw("target", date(2026, 1, 2), 7)

        with self.assertRaisesRegex(ValueError, "not visible"):
            TemporalCutoff(target.held_on).assert_visible(target)

    def test_guard_accepts_past_draw(self) -> None:
        past = make_draw("past", date(2026, 1, 1), 1)

        TemporalCutoff(date(2026, 1, 2)).assert_visible(past)
