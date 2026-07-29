"""Explicit information cutoffs used to prevent target leakage."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from bonoai.domain.models import Draw


@dataclass(frozen=True, slots=True)
class TemporalCutoff:
    """Allow only draws strictly earlier than a target date."""

    target_date: date

    def visible_draws(self, draws: Iterable[Draw]) -> tuple[Draw, ...]:
        visible = (draw for draw in draws if draw.held_on < self.target_date)
        return tuple(sorted(visible, key=lambda draw: (draw.held_on, draw.contest_id)))

    def assert_visible(self, draw: Draw) -> None:
        if draw.held_on >= self.target_date:
            raise ValueError(
                f"draw {draw.contest_id} is not visible before target "
                f"{self.target_date.isoformat()}"
            )
