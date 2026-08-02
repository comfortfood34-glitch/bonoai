"""Backtest CLI commands - thin parsing and formatting layer."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from bonoai.application.backtest_queries import (
    compare_runs,
    list_runs,
    show_run,
    verify_run,
)
from bonoai.application.baseline_strategies import BASELINE_STRATEGIES
from bonoai.application.walk_forward import WalkForwardValidator
from bonoai.domain.backtesting import BacktestConfig, BacktestRun
from bonoai.infrastructure.backtest_artifacts import AtomicArtifactWriter
from bonoai.infrastructure.csv_repository import CsvDrawRepository


def _canonical_repository(data_dir: Path) -> CsvDrawRepository:
    return CsvDrawRepository(data_dir / "processed" / "draws.csv")


def run_backtest_command(args: argparse.Namespace) -> int:
    """Execute backtest subcommands."""
    if args.backtest_command == "run":
        return _run_backtest_run(args)
    if args.backtest_command == "list":
        return _run_backtest_list(args)
    if args.backtest_command == "show":
        return _run_backtest_show(args)
    if args.backtest_command == "compare":
        return _run_backtest_compare(args)
    if args.backtest_command == "verify":
        return _run_backtest_verify(args)
    return 2


def _run_backtest_run(args: argparse.Namespace) -> int:
    """Execute walk-forward validation."""
    repository = _canonical_repository(args.data_dir)
    records = tuple(repository.list_all())

    if not records:
        print("ERROR: base canônica vazia", file=sys.stderr)
        return 2

    try:
        config = BacktestConfig(
            strategy_name=args.strategy,
            start_date=args.start_date,
            end_date=args.end_date,
            training_window_days=args.training_window,
            tickets_per_draw=10,
            random_seed=args.seed,
            dataset_sha256="0" * 64,
            code_commit_sha="0" * 64,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    run_id = BacktestConfig.canonical_run_id(config)

    validator = WalkForwardValidator(records)
    strategy_fn = BASELINE_STRATEGIES[args.strategy]

    try:
        metrics = validator.execute(config, strategy_fn)
        run = BacktestRun(
            run_id=run_id,
            config=config,
            started_at_utc=datetime.now(UTC),
            completed_at_utc=datetime.now(UTC),
            status="success",
            metrics=metrics,
        )

        writer = AtomicArtifactWriter(args.artifacts_dir)
        run_file, sha = writer.write_run_record(run)

        if args.as_json:
            output = {"run_id": run_id, "status": "success", "file": str(run_file), "sha256": sha}
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0

        print(f"Backtest: {run.config.strategy_name}")
        print(f"Período: {run.config.start_date} → {run.config.end_date}")
        if run.metrics:
            print(f"Média de acertos: {run.metrics.average_hits:.2f}")
            print(f"Taxa 2+: {run.metrics.hit_rate_2_plus:.1%}")
            print(f"Taxa 6: {run.metrics.hit_rate_6:.1%}")
        print(f"Salvo em: {run_file}")
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def _run_backtest_list(args: argparse.Namespace) -> int:
    """List all backtest runs."""
    result = list_runs(args.artifacts_dir)

    if args.as_json:
        print(json.dumps({
            "count": result.count,
            "runs": result.run_ids,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"Execuções: {result.count}")
        for run_id in result.run_ids:
            print(f"  {run_id}")

    return 0


def _run_backtest_show(args: argparse.Namespace) -> int:
    """Show detailed backtest results."""
    result = show_run(args.artifacts_dir, args.run_id)

    if result.error:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 2

    if args.as_json:
        output = {
            "run_id": result.run_id,
            "config": result.config,
            "metrics": result.metrics,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result.run_id}")
        if result.config:
            print(f"Estratégia: {result.config.get('strategy_name', '?')}")
        if result.metrics and "average_hits" in result.metrics:
            print(f"Média: {result.metrics['average_hits']:.2f}")

    return 0


def _run_backtest_compare(args: argparse.Namespace) -> int:
    """Compare two backtest runs."""
    result = compare_runs(args.artifacts_dir, args.run_id_1, args.run_id_2)

    if result.error:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps({
            "run_1": result.run_id_1,
            "run_2": result.run_id_2,
            "avg_diff": result.avg_diff,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"Comparação: {result.run_id_1[:8]} vs {result.run_id_2[:8]}")
        print(f"Diferença média: {result.avg_diff:+.2f}")

    return 0


def _run_backtest_verify(args: argparse.Namespace) -> int:
    """Verify backtest integrity and artifact SHA-256."""
    result = verify_run(args.artifacts_dir, args.run_id)

    if result.error:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps({
            "run_id": result.run_id,
            "valid": result.valid,
            "files_checked": result.files_checked,
            "failed": result.failed_files,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"Verificação: {result.run_id[:8]}")
        print(f"Status: {'✓ válido' if result.valid else '✗ inválido'}")
        print(f"Arquivos: {result.files_checked} verificados")
        if result.failed_files:
            for fail in result.failed_files:
                print(f"  ✗ {fail}")

    return 0 if result.valid else 1
