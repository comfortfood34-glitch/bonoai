"""Command-line interface for BonoAI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from bonoai import __version__
from bonoai.application.portfolio import generate_uniform_portfolio
from bonoai.domain.models import DEFAULT_BUDGET_EUR, SIMPLE_BET_PRICE_EUR


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError(f"invalid decimal value: {value}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bonoai",
        description="Pesquisa reproduzível para a Bonoloto, sem promessas preditivas.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("info", help="mostra os invariantes do projeto")

    generate = subparsers.add_parser(
        "generate",
        help="gera uma carteira usando o baseline uniforme",
    )
    generate.add_argument("--budget", type=_decimal, default=DEFAULT_BUDGET_EUR)
    generate.add_argument("--unit-price", type=_decimal, default=SIMPLE_BET_PRICE_EUR)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _run_info() -> int:
    print(f"BonoAI {__version__}")
    print("Escopo: Bonoloto, 6 números distintos entre 1 e 49")
    print("Padrão: €5,00 = 10 apostas simples de €0,50")
    print("Postura: análise e backtesting; nenhuma promessa de previsão")
    return 0


def _run_generate(args: argparse.Namespace) -> int:
    run = generate_uniform_portfolio(
        budget_eur=args.budget,
        unit_price_eur=args.unit_price,
        seed=args.seed,
    )
    if args.as_json:
        print(json.dumps(run.as_dict(), ensure_ascii=False, indent=2))
        return 0

    print(
        f"BonoAI | {len(run.portfolio.tickets)} apostas | "
        f"custo €{run.portfolio.cost_eur} | seed {run.seed}"
    )
    for index, ticket in enumerate(run.portfolio.tickets, start=1):
        formatted = " ".join(f"{number:02d}" for number in ticket.numbers)
        print(f"{index:02d}: {formatted}")
    print("Baseline uniforme; não aumenta a chance intrínseca de cada combinação.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "info":
            return _run_info()
        if args.command == "generate":
            return _run_generate(args)
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    parser.error(f"unknown command: {args.command}")  # pragma: no cover
    return 2  # pragma: no cover
