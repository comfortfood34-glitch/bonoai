from decimal import Decimal
from unittest import TestCase

from bonoai.application.portfolio import generate_uniform_portfolio


class UniformPortfolioTests(TestCase):
    def test_default_budget_produces_exactly_ten_distinct_tickets(self) -> None:
        run = generate_uniform_portfolio(seed=42)

        self.assertEqual(len(run.portfolio.tickets), 10)
        self.assertEqual(len(set(run.portfolio.tickets)), 10)
        self.assertEqual(run.portfolio.cost_eur, Decimal("5.00"))

    def test_same_seed_is_reproducible(self) -> None:
        first = generate_uniform_portfolio(seed=123)
        second = generate_uniform_portfolio(seed=123)

        self.assertEqual(first, second)

    def test_different_seed_changes_the_portfolio(self) -> None:
        first = generate_uniform_portfolio(seed=123)
        second = generate_uniform_portfolio(seed=456)

        self.assertNotEqual(first.portfolio, second.portfolio)

    def test_rejects_non_divisible_budget(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact multiple"):
            generate_uniform_portfolio(budget_eur=Decimal("5.10"))

    def test_rejects_non_positive_budget(self) -> None:
        with self.assertRaisesRegex(ValueError, "budget must be positive"):
            generate_uniform_portfolio(budget_eur=Decimal("0"))

    def test_rejects_non_positive_unit_price(self) -> None:
        with self.assertRaisesRegex(ValueError, "unit price must be positive"):
            generate_uniform_portfolio(unit_price_eur=Decimal("0"))

    def test_serialized_run_preserves_provenance(self) -> None:
        payload = generate_uniform_portfolio(seed=7).as_dict()

        self.assertEqual(payload["seed"], 7)
        self.assertEqual(payload["algorithm"], "uniform-v1")
        self.assertEqual(payload["ticket_count"], 10)
        self.assertEqual(payload["cost_eur"], "5.00")
