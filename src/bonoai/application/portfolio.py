"""Portfolio generation use cases."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from random import Random

from bonoai.domain.models import (
    DEFAULT_BUDGET_EUR,
    DRAW_SIZE,
    NUMBER_MAX,
    NUMBER_MIN,
    SIMPLE_BET_PRICE_EUR,
    Portfolio,
    Ticket,
)


@dataclass(frozen=True, slots=True)
class GenerationRun:
    """Reproducible output and its minimum provenance."""

    portfolio: Portfolio
    seed: int
    algorithm: str = "uniform-v1"

    def as_dict(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "seed": self.seed,
            "unit_price_eur": str(self.portfolio.unit_price_eur),
            "cost_eur": str(self.portfolio.cost_eur),
            "ticket_count": len(self.portfolio.tickets),
            "tickets": [list(ticket.numbers) for ticket in self.portfolio.tickets],
            "disclaimer": (
                "Baseline uniforme: organiza uma carteira reproduzível; "
                "não aumenta a probabilidade intrínseca das combinações."
            ),
        }


def _ticket_count_for_budget(budget_eur: Decimal, unit_price_eur: Decimal) -> int:
    if budget_eur <= 0:
        raise ValueError("budget must be positive")
    if unit_price_eur <= 0:
        raise ValueError("unit price must be positive")

    quotient = budget_eur / unit_price_eur
    if quotient != quotient.to_integral_value():
        raise ValueError("budget must be an exact multiple of the unit price")
    return int(quotient)


def generate_uniform_portfolio(
    *,
    budget_eur: Decimal = DEFAULT_BUDGET_EUR,
    unit_price_eur: Decimal = SIMPLE_BET_PRICE_EUR,
    seed: int = 42,
) -> GenerationRun:
    """Generate distinct simple bets uniformly and reproducibly."""
    ticket_count = _ticket_count_for_budget(budget_eur, unit_price_eur)
    random = Random(seed)
    tickets: set[Ticket] = set()

    while len(tickets) < ticket_count:
        values = random.sample(range(NUMBER_MIN, NUMBER_MAX + 1), DRAW_SIZE)
        tickets.add(Ticket(tuple(values)))

    ordered = tuple(sorted(tickets))
    portfolio = Portfolio(ordered, unit_price_eur=unit_price_eur)
    if portfolio.cost_eur != budget_eur:  # pragma: no cover - defensive invariant
        raise RuntimeError("generated portfolio cost does not match the requested budget")
    if len(portfolio.tickets) != ticket_count:  # pragma: no cover - defensive invariant
        raise RuntimeError("generator returned a partial portfolio")
    return GenerationRun(portfolio=portfolio, seed=seed)
