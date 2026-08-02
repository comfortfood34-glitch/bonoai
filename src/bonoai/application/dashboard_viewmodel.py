"""Dashboard view model - pure business logic, no Streamlit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def load_run_data(run_dir: Path) -> dict[str, Any] | None:
    """Load backtest run from separate config and metrics files.

    Returns None if required files missing or JSON invalid.
    Tolerant of missing manifest (uses defaults).
    """
    config_file = run_dir / "config.json"
    metrics_file = run_dir / "metrics.json"
    manifest_file = run_dir / "manifest.json"

    if not config_file.exists() or not metrics_file.exists():
        return None

    try:
        with open(config_file) as f:
            config = cast(dict[str, Any], json.load(f))
        with open(metrics_file) as f:
            metrics = cast(dict[str, Any], json.load(f))

        manifest: dict[str, Any] = {}
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = cast(dict[str, Any], json.load(f))

        return {
            "config": config,
            "metrics": metrics,
            "status": manifest.get("status", "unknown"),
            "run_id": manifest.get("run_id", ""),
        }
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def list_runs(artifacts_dir: Path) -> list[str]:
    """Get all backtest run IDs from artifacts directory."""
    if not artifacts_dir.exists():
        return []

    manifests = sorted(artifacts_dir.glob("*/manifest.json"))
    return [m.parent.name for m in manifests]


def get_run_info(artifacts_dir: Path, run_id: str) -> dict[str, Any] | None:
    """Get run data by ID."""
    run_dir = artifacts_dir / run_id
    return load_run_data(run_dir)


def format_status_label(status: str) -> str:
    """Format status for display."""
    if status == "success":
        return "✅ Success"
    if status == "failed":
        return "❌ Failed"
    return f"⚠️ {status}"


def prepare_metrics_display(metrics: dict[str, Any]) -> dict[str, Any]:
    """Extract and format metrics for display."""
    return {
        "average_hits": metrics.get("average_hits", 0.0),
        "hit_rate_2_plus": metrics.get("hit_rate_2_plus", 0.0),
        "hit_rate_3_plus": metrics.get("hit_rate_3_plus", 0.0),
        "hit_rate_4_plus": metrics.get("hit_rate_4_plus", 0.0),
        "hit_rate_6": metrics.get("hit_rate_6", 0.0),
        "hit_distribution": metrics.get("hit_distribution", {}),
    }


def prepare_config_display(config: dict[str, Any]) -> dict[str, Any]:
    """Extract and format config for display."""
    return {
        "period": f"{config.get('start_date', '?')} → {config.get('end_date', '?')}",
        "training_window_days": config.get("training_window_days", 0),
        "random_seed": config.get("random_seed", 0),
    }


def validate_run_data(data: dict[str, Any] | None) -> tuple[bool, str]:
    """Validate run data completeness. Returns (is_valid, error_message)."""
    if not data:
        return False, "Run data not found"

    if not isinstance(data.get("config"), dict):
        return False, "Invalid config"

    if not isinstance(data.get("metrics"), dict):
        return False, "Invalid metrics"

    return True, ""


def compare_runs(
    run1_data: dict[str, Any] | None,
    run2_data: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Compare two runs. Returns comparison dict or None if invalid."""
    if not run1_data or not run2_data:
        return None

    metrics1 = prepare_metrics_display(run1_data.get("metrics", {}))
    metrics2 = prepare_metrics_display(run2_data.get("metrics", {}))

    return {
        "run1_id": run1_data.get("run_id", ""),
        "run2_id": run2_data.get("run_id", ""),
        "run1_strategy": run1_data.get("config", {}).get("strategy_name", ""),
        "run2_strategy": run2_data.get("config", {}).get("strategy_name", ""),
        "run1_avg_hits": metrics1["average_hits"],
        "run2_avg_hits": metrics2["average_hits"],
        "difference": abs(metrics1["average_hits"] - metrics2["average_hits"]),
    }
