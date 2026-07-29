"""Core Bonoloto entities with fail-closed validation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Final

NUMBER_MIN: Final = 1
NUMBER_MAX: Final = 49
DRAW_SIZE: Final = 6
SIMPLE_BET_PRICE_EUR: Final = Decimal("0.50")
DEFAULT_BUDGET_EUR: Final = Decimal("5.00")


def normalize_main_numbers(values: Iterable[int]) -> tuple[int, ...]:
    """Return a canonical six-number tuple or raise on invalid input."""
    numbers = tuple(sorted(values))
    if len(numbers) != DRAW_SIZE:
        raise ValueError(f"expected {DRAW_SIZE} numbers, received {len(numbers)}")
    if len(set(numbers)) != DRAW_SIZE:
        raise ValueError("main numbers must be distinct")
    if numbers[0] < NUMBER_MIN or numbers[-1] > NUMBER_MAX:
        raise ValueError(f"main numbers must be between {NUMBER_MIN} and {NUMBER_MAX}")
    return numbers


@dataclass(frozen=True, slots=True)
class Draw:
    """A validated canonical Bonoloto draw."""

    contest_id: str
    held_on: date
    numbers: tuple[int, ...]
    complementary: int | None = None
    reintegro: int | None = None

    def __post_init__(self) -> None:
        if not self.contest_id.strip():
            raise ValueError("contest_id must not be empty")
        canonical = normalize_main_numbers(self.numbers)
        object.__setattr__(self, "numbers", canonical)

        if self.complementary is not None:
            if not NUMBER_MIN <= self.complementary <= NUMBER_MAX:
                raise ValueError("complementary must be between 1 and 49")
            if self.complementary in canonical:
                raise ValueError("complementary must not repeat a main number")

        if self.reintegro is not None and not 0 <= self.reintegro <= 9:
            raise ValueError("reintegro must be between 0 and 9")


@dataclass(frozen=True, slots=True, order=True)
class Ticket:
    """One simple Bonoloto bet."""

    numbers: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "numbers", normalize_main_numbers(self.numbers))


@dataclass(frozen=True, slots=True)
class Portfolio:
    """A complete collection of distinct simple bets."""

    tickets: tuple[Ticket, ...]
    unit_price_eur: Decimal = SIMPLE_BET_PRICE_EUR

    def __post_init__(self) -> None:
        if not self.tickets:
            raise ValueError("portfolio must contain at least one ticket")
        if len(set(self.tickets)) != len(self.tickets):
            raise ValueError("portfolio tickets must be distinct")
        if self.unit_price_eur <= 0:
            raise ValueError("unit price must be positive")

    @property
    def cost_eur(self) -> Decimal:
        return self.unit_price_eur * len(self.tickets)
