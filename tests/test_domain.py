from datetime import date
from decimal import Decimal
from unittest import TestCase

from bonoai.domain.models import Draw, Portfolio, Ticket, normalize_main_numbers


class NumberContractTests(TestCase):
    def test_normalizes_numbers(self) -> None:
        self.assertEqual(normalize_main_numbers([49, 3, 20, 1, 11, 7]), (1, 3, 7, 11, 20, 49))

    def test_rejects_wrong_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected 6"):
            normalize_main_numbers([1, 2, 3])

    def test_rejects_duplicates(self) -> None:
        with self.assertRaisesRegex(ValueError, "distinct"):
            normalize_main_numbers([1, 2, 3, 4, 5, 5])

    def test_rejects_out_of_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 49"):
            normalize_main_numbers([0, 2, 3, 4, 5, 6])


class DrawContractTests(TestCase):
    def test_accepts_valid_metadata(self) -> None:
        draw = Draw(
            contest_id="2026-001",
            held_on=date(2026, 1, 1),
            numbers=(1, 2, 3, 4, 5, 6),
            complementary=7,
            reintegro=0,
        )
        self.assertEqual(draw.numbers, (1, 2, 3, 4, 5, 6))

    def test_rejects_repeated_complementary(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not repeat"):
            Draw(
                contest_id="2026-001",
                held_on=date(2026, 1, 1),
                numbers=(1, 2, 3, 4, 5, 6),
                complementary=6,
                reintegro=0,
            )

    def test_rejects_empty_contest_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            Draw(
                contest_id=" ",
                held_on=date(2026, 1, 1),
                numbers=(1, 2, 3, 4, 5, 6),
                complementary=7,
                reintegro=0,
            )

    def test_rejects_invalid_complementary(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 49"):
            Draw(
                contest_id="2026-001",
                held_on=date(2026, 1, 1),
                numbers=(1, 2, 3, 4, 5, 6),
                complementary=50,
                reintegro=0,
            )

    def test_rejects_invalid_reintegro(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 9"):
            Draw(
                contest_id="2026-001",
                held_on=date(2026, 1, 1),
                numbers=(1, 2, 3, 4, 5, 6),
                complementary=7,
                reintegro=10,
            )


class PortfolioContractTests(TestCase):
    def test_rejects_empty_portfolio(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            Portfolio(())

    def test_rejects_duplicate_tickets(self) -> None:
        ticket = Ticket((1, 2, 3, 4, 5, 6))
        with self.assertRaisesRegex(ValueError, "distinct"):
            Portfolio((ticket, ticket))

    def test_calculates_decimal_cost(self) -> None:
        portfolio = Portfolio(
            (
                Ticket((1, 2, 3, 4, 5, 6)),
                Ticket((7, 8, 9, 10, 11, 12)),
            ),
            unit_price_eur=Decimal("0.50"),
        )
        self.assertEqual(portfolio.cost_eur, Decimal("1.00"))

    def test_rejects_non_positive_price(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            Portfolio(
                (Ticket((1, 2, 3, 4, 5, 6)),),
                unit_price_eur=Decimal("0"),
            )
