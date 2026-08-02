"""Command-line interface for BonoAI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from bonoai import __version__
from bonoai.application.audit import reconcile_sources
from bonoai.application.audit_models import AuditPolicy
from bonoai.application.ingestion import ingest_draws
from bonoai.application.portfolio import generate_uniform_portfolio
from bonoai.cli_backtest import run_backtest_command
from bonoai.cli_migrate import run_data_migrate
from bonoai.domain.data import DataContractError
from bonoai.domain.models import DEFAULT_BUDGET_EUR, SIMPLE_BET_PRICE_EUR
from bonoai.infrastructure.csv_bootstrap import CsvHistoricalSource
from bonoai.infrastructure.csv_repository import CsvDrawRepository
from bonoai.infrastructure.raw_archive import FilesystemRawArchive
from bonoai.infrastructure.raw_payload_reader import FilesystemRawPayloadReader
from bonoai.infrastructure.selae_rss import SelaeRssSource


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

    update = subparsers.add_parser(
        "data-update",
        help="arquiva e incorpora resultados novos do RSS oficial da SELAE",
    )
    update.add_argument("--data-dir", type=Path, default=Path("data"))
    update.add_argument("--timeout", type=float, default=20.0)
    update.add_argument("--json", action="store_true", dest="as_json")

    status = subparsers.add_parser(
        "data-status",
        help="mostra o estado do conjunto canônico local",
    )
    status.add_argument("--data-dir", type=Path, default=Path("data"))
    status.add_argument("--json", action="store_true", dest="as_json")

    migrate = subparsers.add_parser(
        "data-migrate",
        help="migra dados de schema v1 para v2 (idempotente)",
    )
    migrate.add_argument("--data-dir", type=Path, default=Path("data"))
    migrate.add_argument("--json", action="store_true", dest="as_json")

    bootstrap = subparsers.add_parser(
        "data-bootstrap",
        help="carrega dados históricos de um arquivo CSV local",
    )
    bootstrap.add_argument("--file", type=Path, help="caminho do arquivo CSV")
    bootstrap.add_argument("--url", type=str, help="(BLOQUEADO) URL remota de fonte histórica")
    bootstrap.add_argument("--source-name", type=str, default="auxiliary", help="nome da fonte")
    bootstrap.add_argument("--data-dir", type=Path, default=Path("data"))
    bootstrap.add_argument("--json", action="store_true", dest="as_json")

    audit = subparsers.add_parser(
        "data-audit",
        help="audita e reconcilia fontes de dados",
    )
    audit.add_argument("--data-dir", type=Path, default=Path("data"))
    audit.add_argument("--json", action="store_true", dest="as_json")

    backtest = subparsers.add_parser("backtest", help="walk-forward validation")
    backtest_subparsers = backtest.add_subparsers(dest="backtest_command", required=True)
    backtest_run = backtest_subparsers.add_parser("run", help="executa walk-forward")
    backtest_run.add_argument(
        "--strategy", type=str, required=True,
        choices=[
            "uniform_random", "frequency_only", "delay_only", "mixed_frequency_delay"
        ],
    )
    backtest_run.add_argument("--start-date", type=str, required=True)
    backtest_run.add_argument("--end-date", type=str, required=True)
    backtest_run.add_argument("--training-window", type=int, default=360)
    backtest_run.add_argument("--seed", type=int, default=42)
    backtest_run.add_argument("--data-dir", type=Path, default=Path("data"))
    backtest_run.add_argument("--artifacts-dir", type=Path, default=Path("backtests/runs"))
    backtest_run.add_argument("--json", action="store_true", dest="as_json")

    backtest_list = backtest_subparsers.add_parser("list", help="lista execuções")
    backtest_list.add_argument("--artifacts-dir", type=Path, default=Path("backtests/runs"))
    backtest_list.add_argument("--json", action="store_true", dest="as_json")
    backtest_show = backtest_subparsers.add_parser("show", help="mostra resultado")
    backtest_show.add_argument("run_id", type=str, help="run_id")
    backtest_show.add_argument("--artifacts-dir", type=Path, default=Path("backtests/runs"))
    backtest_show.add_argument("--json", action="store_true", dest="as_json")
    backtest_compare = backtest_subparsers.add_parser("compare", help="compara runs")
    backtest_compare.add_argument("run_id_1", type=str)
    backtest_compare.add_argument("run_id_2", type=str)
    backtest_compare.add_argument("--artifacts-dir", type=Path, default=Path("backtests/runs"))
    backtest_compare.add_argument("--json", action="store_true", dest="as_json")
    backtest_verify = backtest_subparsers.add_parser("verify", help="verifica integridade")
    backtest_verify.add_argument("run_id", type=str, help="run_id")
    backtest_verify.add_argument("--artifacts-dir", type=Path, default=Path("backtests/runs"))
    backtest_verify.add_argument("--json", action="store_true", dest="as_json")

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


def _canonical_repository(data_dir: Path) -> CsvDrawRepository:
    return CsvDrawRepository(data_dir / "processed" / "draws.csv")

def _run_data_update(args: argparse.Namespace) -> int:
    report = ingest_draws(
        source=SelaeRssSource(timeout_seconds=args.timeout),
        repository=_canonical_repository(args.data_dir),
        raw_archive=FilesystemRawArchive(args.data_dir / "raw"),
    )
    if args.as_json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
        return 0

    print(
        f"SELAE: {report.fetched} lidos, {report.inserted} novos, "
        f"{report.duplicates} já existentes"
    )
    print(f"Base canônica: {report.total} concursos")
    print(f"Último concurso: {report.latest_draw or 'nenhum'}")
    print(f"Bruto arquivado em: {report.raw_archive_path}")
    return 0


def _run_data_status(args: argparse.Namespace) -> int:
    repository = _canonical_repository(args.data_dir)
    records = repository.list_all()
    payload = {
        "canonical_path": str(repository.path),
        "draw_count": len(records),
        "first_draw": records[0].draw.held_on.isoformat() if records else None,
        "last_draw": records[-1].draw.held_on.isoformat() if records else None,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"Base canônica: {payload['canonical_path']}")
    print(f"Concursos: {payload['draw_count']}")
    print(f"Período: {payload['first_draw'] or 'vazio'} → {payload['last_draw'] or 'vazio'}")
    return 0


def _run_data_bootstrap(args: argparse.Namespace) -> int:
    if getattr(args, "url", None):
        import sys
        print("ERROR: fonte histórica remota não aprovada: --url bloqueada", file=sys.stderr)
        return 2
    if not getattr(args, "file", None):
        import sys
        print("ERROR: --file é obrigatório", file=sys.stderr)
        return 2

    source = CsvHistoricalSource(args.file, source_name=args.source_name)
    records = source.load()
    repository = _canonical_repository(args.data_dir)
    audit = reconcile_sources(repository.list_all(), records)

    if audit.has_conflicts():
        parser = build_parser()
        conflict_ids = [c.contest_id for c in audit.conflicts]
        msg = f"Found {len(audit.conflicts)} conflicting result(s): {', '.join(conflict_ids)}"
        parser.error(msg)

    result = repository.append_validated(audit.merged_records)
    if args.as_json:
        output = {
            "loaded_from": str(args.file),
            "inserted_draws": result.inserted_draws,
            "added_provenances": result.added_provenances,
            "duplicate_provenances": result.duplicate_provenances,
            "total": result.total,
            "conflicts": len(audit.conflicts),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    print(f"Histórico carregado: {args.file}")
    print(f"Novos concursos: {result.inserted_draws}")
    print(f"Novas proveniências: {result.added_provenances}")
    print(f"Proveniências duplicadas: {result.duplicate_provenances}")
    print(f"Total na base: {result.total}")
    return 0


def _run_data_audit(args: argparse.Namespace) -> int:
    repository = _canonical_repository(args.data_dir)
    records = repository.list_all()
    raw_reader = FilesystemRawPayloadReader(args.data_dir / "raw")

    try:
        audit = reconcile_sources(records, None, raw_reader, AuditPolicy())
    except RuntimeError as error:
        import sys
        print(f"Erro operacional: {error}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return audit.exit_code()

    print(f"Base canônica: {len(records)} concursos")
    if audit.findings:
        print("Achados da auditoria:")
        for finding in audit.findings:
            print(f"  [{finding.severity.upper()}] {finding.code}: {finding.message}")
    if audit.conflicts:
        print(f"Conflitos: {len(audit.conflicts)}")
        for conflict in audit.conflicts:
            print(
                f"  {conflict.contest_id}: "
                f"oficial={conflict.official_numbers}, "
                f"auxiliar={conflict.auxiliary_numbers}"
            )
    else:
        print("Nenhum conflito encontrado")
    return audit.exit_code()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "info":
            return _run_info()
        if args.command == "generate":
            return _run_generate(args)
        if args.command == "data-update":
            return _run_data_update(args)
        if args.command == "data-status":
            return _run_data_status(args)
        if args.command == "data-migrate":
            return run_data_migrate(args)
        if args.command == "data-bootstrap":
            return _run_data_bootstrap(args)
        if args.command == "data-audit":
            return _run_data_audit(args)
        if args.command == "backtest":
            return run_backtest_command(args)
    except (OSError, ValueError, RuntimeError, DataContractError) as error:
        parser.error(str(error))
    parser.error(f"unknown command: {args.command}")
    return 2
