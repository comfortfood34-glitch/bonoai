"""Backtest query operations - pure business logic, no CLI or print."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ListRunsResult:
    """Result of listing runs."""

    count: int
    run_ids: list[str]


@dataclass
class ShowRunResult:
    """Result of showing run details."""

    run_id: str
    config: dict[str, Any] | None
    metrics: dict[str, Any] | None
    error: str | None = None


@dataclass
class CompareRunsResult:
    """Result of comparing two runs."""

    run_id_1: str
    run_id_2: str
    avg_diff: float
    error: str | None = None


@dataclass
class VerifyRunResult:
    """Result of verifying run integrity."""

    run_id: str
    valid: bool
    files_checked: int
    failed_files: list[str]
    error: str | None = None


def list_runs(artifacts_dir: Path) -> ListRunsResult:
    """List all backtest runs."""
    if not artifacts_dir.exists():
        return ListRunsResult(count=0, run_ids=[])

    manifests = sorted(artifacts_dir.glob("*/manifest.json"))
    run_ids = [m.parent.name for m in manifests][:10]

    return ListRunsResult(count=len(manifests), run_ids=run_ids)


def show_run(artifacts_dir: Path, run_id: str) -> ShowRunResult:
    """Show run details."""
    run_dir = artifacts_dir / run_id
    config_file = run_dir / "config.json"
    metrics_file = run_dir / "metrics.json"

    if not config_file.exists():
        return ShowRunResult(run_id=run_id, config=None, metrics=None, error="config not found")

    try:
        with open(config_file) as f:
            config = json.load(f)

        metrics = None
        if metrics_file.exists():
            with open(metrics_file) as f:
                metrics = json.load(f)

        return ShowRunResult(run_id=run_id, config=config, metrics=metrics)
    except (json.JSONDecodeError, OSError) as e:
        return ShowRunResult(run_id=run_id, config=None, metrics=None, error=str(e))


def compare_runs(
    artifacts_dir: Path,
    run_id_1: str,
    run_id_2: str,
) -> CompareRunsResult:
    """Compare two runs."""
    metrics1_file = artifacts_dir / run_id_1 / "metrics.json"
    metrics2_file = artifacts_dir / run_id_2 / "metrics.json"

    if not metrics1_file.exists():
        return CompareRunsResult(
            run_id_1=run_id_1,
            run_id_2=run_id_2,
            avg_diff=0.0,
            error="run 1 not found",
        )

    if not metrics2_file.exists():
        return CompareRunsResult(
            run_id_1=run_id_1,
            run_id_2=run_id_2,
            avg_diff=0.0,
            error="run 2 not found",
        )

    try:
        with open(metrics1_file) as f:
            m1 = json.load(f)
        with open(metrics2_file) as f:
            m2 = json.load(f)

        avg_diff = m2.get("average_hits", 0.0) - m1.get("average_hits", 0.0)
        return CompareRunsResult(run_id_1=run_id_1, run_id_2=run_id_2, avg_diff=avg_diff)
    except (json.JSONDecodeError, OSError) as e:
        return CompareRunsResult(
            run_id_1=run_id_1,
            run_id_2=run_id_2,
            avg_diff=0.0,
            error=str(e),
        )


def verify_run(artifacts_dir: Path, run_id: str) -> VerifyRunResult:
    """Verify run integrity via manifest SHA-256."""
    run_dir = artifacts_dir / run_id
    manifest_file = run_dir / "manifest.json"

    if not manifest_file.exists():
        return VerifyRunResult(
            run_id=run_id,
            valid=False,
            files_checked=0,
            failed_files=[],
            error="manifest not found",
        )

    try:
        with open(manifest_file) as f:
            manifest = json.load(f)

        files_to_check = list(manifest.get("files", {}).keys())
        all_valid = True
        failed_files: list[str] = []

        for fname in files_to_check:
            fpath = run_dir / fname
            if not fpath.exists():
                all_valid = False
                failed_files.append(f"{fname} (missing)")
                continue

            with open(fpath, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            expected_hash = manifest["files"][fname]

            if actual_hash != expected_hash:
                all_valid = False
                failed_files.append(f"{fname} (hash mismatch)")

        return VerifyRunResult(
            run_id=run_id,
            valid=all_valid,
            files_checked=len(files_to_check),
            failed_files=failed_files,
        )
    except (json.JSONDecodeError, OSError) as e:
        return VerifyRunResult(
            run_id=run_id,
            valid=False,
            files_checked=0,
            failed_files=[],
            error=str(e),
        )
