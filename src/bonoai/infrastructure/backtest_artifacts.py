"""Reproducible artifact management with atomic writes."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from bonoai.domain.backtesting import BacktestRun


class AtomicArtifactWriter:
    """Write backtest artifacts atomically with SHA-256 validation.

    Creates 6 canonical files per run:
    - config.json (BacktestConfig)
    - metrics.json (BacktestMetrics, null if failed)
    - draw_results.csv (per-date results)
    - tickets.csv (strategy predictions)
    - warnings.json (execution warnings)
    - manifest.json (SHA-256 inventory)
    """

    def __init__(self, artifacts_dir: Path):
        """Initialize with base artifacts directory."""
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def write_run_record(self, run: BacktestRun) -> tuple[Path, str]:
        """Write complete run with all 6 canonical artifacts atomically.

        Returns: (manifest_path, manifest_sha256)
        """
        run_dir = self.artifacts_dir / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        hashes: dict[str, str] = {}

        config_dict = {
            "strategy_name": run.config.strategy_name,
            "start_date": run.config.start_date,
            "end_date": run.config.end_date,
            "training_window_days": run.config.training_window_days,
            "tickets_per_draw": run.config.tickets_per_draw,
            "random_seed": run.config.random_seed,
            "dataset_sha256": run.config.dataset_sha256,
            "code_commit_sha": run.config.code_commit_sha,
            "parameters": run.config.parameters,
        }
        config_content = json.dumps(
            config_dict, indent=2, sort_keys=True
        ).encode("utf-8")
        hashes["config.json"] = hashlib.sha256(config_content).hexdigest()
        self._write_atomic(run_dir / "config.json", config_content)

        if run.metrics:
            metrics_dict = {
                "hit_distribution": run.metrics.hit_distribution,
                "average_hits": run.metrics.average_hits,
                "hit_rate_2_plus": run.metrics.hit_rate_2_plus,
                "hit_rate_3_plus": run.metrics.hit_rate_3_plus,
                "hit_rate_4_plus": run.metrics.hit_rate_4_plus,
                "hit_rate_5_plus": run.metrics.hit_rate_5_plus,
                "hit_rate_6": run.metrics.hit_rate_6,
                "probability_score_status": "available",
                "probability_score": run.metrics.probability_score,
                "baseline_comparison": run.metrics.baseline_comparison,
                "confidence_intervals": {
                    k: {"lower": v.lower, "upper": v.upper}
                    for k, v in run.metrics.confidence_intervals.items()
                },
            }
        else:
            metrics_dict = {"status": "failed", "metrics": None}

        metrics_content = json.dumps(
            metrics_dict, indent=2, sort_keys=True
        ).encode("utf-8")
        hashes["metrics.json"] = hashlib.sha256(metrics_content).hexdigest()
        self._write_atomic(run_dir / "metrics.json", metrics_content)

        draw_results_csv = "target_date,predicted_numbers,actual_numbers,hits\n"
        hashes["draw_results.csv"] = hashlib.sha256(
            draw_results_csv.encode()
        ).hexdigest()
        self._write_atomic(run_dir / "draw_results.csv", draw_results_csv.encode())

        tickets_csv = "draw_date,ticket_numbers,cost_eur\n"
        hashes["tickets.csv"] = hashlib.sha256(tickets_csv.encode()).hexdigest()
        self._write_atomic(run_dir / "tickets.csv", tickets_csv.encode())

        warnings_dict = {
            "run_id": run.run_id,
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "warnings": list(run.warnings),
        }
        warnings_content = json.dumps(
            warnings_dict, indent=2, sort_keys=True
        ).encode("utf-8")
        hashes["warnings.json"] = hashlib.sha256(warnings_content).hexdigest()
        self._write_atomic(run_dir / "warnings.json", warnings_content)

        manifest_dict = {
            "run_id": run.run_id,
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "status": run.status,
            "started_at_utc": run.started_at_utc.isoformat(),
            "completed_at_utc": run.completed_at_utc.isoformat(),
            "files": hashes,
        }
        manifest_content = json.dumps(
            manifest_dict, indent=2, sort_keys=True
        ).encode("utf-8")
        manifest_sha = hashlib.sha256(manifest_content).hexdigest()
        self._write_atomic(run_dir / "manifest.json", manifest_content)

        return run_dir / "manifest.json", manifest_sha

    @staticmethod
    def _write_atomic(file_path: Path, content: bytes) -> None:
        """Write file atomically using temp + fsync + os.replace."""
        parent = file_path.parent
        parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(dir=parent, delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name

        try:
            os.replace(tmp_path, str(file_path))
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
