"""Artifact atomicity and integrity tests."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.backtesting import (
    BacktestConfig,
    BacktestMetrics,
    BacktestRun,
    ConfidenceInterval,
)
from bonoai.infrastructure.backtest_artifacts import AtomicArtifactWriter


class TestArtifactCreation(TestCase):
    """Verify all 6 canonical artifacts are created."""

    def test_all_six_artifacts_created(self) -> None:
        """Write creates config, metrics, draw_results, tickets, warnings, manifest."""
        with TemporaryDirectory() as tmpdir:
            writer = AtomicArtifactWriter(Path(tmpdir))
            config = BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-01-10",
                training_window_days=5,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0"*64,
                code_commit_sha="0"*64,
            )
            metrics = BacktestMetrics(
                hit_distribution={0: 5, 1: 3, 2: 1},
                average_hits=0.9,
                hit_rate_2_plus=0.1,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.15,
                baseline_comparison={},
                confidence_intervals={
                    "average_hits": ConfidenceInterval(lower=0.05, upper=0.3)
                },
            )
            run = BacktestRun(
                run_id="test123456789abc",
                config=config,
                started_at_utc=datetime.now(UTC),
                completed_at_utc=datetime.now(UTC),
                status="success",
                metrics=metrics,
            )
            manifest_path, _sha = writer.write_run_record(run)
            run_dir = manifest_path.parent

            expected_files = {
                "config.json",
                "metrics.json",
                "draw_results.csv",
                "tickets.csv",
                "warnings.json",
                "manifest.json",
            }
            actual_files = {f.name for f in run_dir.iterdir() if f.is_file()}
            self.assertEqual(expected_files, actual_files)

    def test_no_run_json_created(self) -> None:
        """Verify run.json is NOT created (contract breach if present)."""
        with TemporaryDirectory() as tmpdir:
            writer = AtomicArtifactWriter(Path(tmpdir))
            config = BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-01-10",
                training_window_days=5,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0"*64,
                code_commit_sha="0"*64,
            )
            metrics = BacktestMetrics(
                hit_distribution={0: 5, 1: 3, 2: 1},
                average_hits=0.9,
                hit_rate_2_plus=0.1,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.15,
                baseline_comparison={},
                confidence_intervals={
                    "average_hits": ConfidenceInterval(lower=0.05, upper=0.3)
                },
            )
            run = BacktestRun(
                run_id="test123456789def",
                config=config,
                started_at_utc=datetime.now(UTC),
                completed_at_utc=datetime.now(UTC),
                status="success",
                metrics=metrics,
            )
            manifest_path, _sha = writer.write_run_record(run)
            run_dir = manifest_path.parent
            run_json = run_dir / "run.json"
            self.assertFalse(run_json.exists())

    def test_manifest_contains_all_file_hashes(self) -> None:
        """Manifest includes SHA-256 for all 5 artifact files."""
        with TemporaryDirectory() as tmpdir:
            writer = AtomicArtifactWriter(Path(tmpdir))
            config = BacktestConfig(
                strategy_name="frequency_only",
                start_date="2025-01-01",
                end_date="2025-01-10",
                training_window_days=5,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0"*64,
                code_commit_sha="0"*64,
            )
            metrics = BacktestMetrics(
                hit_distribution={0: 9},
                average_hits=0.0,
                hit_rate_2_plus=0.0,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.0,
                baseline_comparison={},
                confidence_intervals={
                    "average_hits": ConfidenceInterval(lower=0.0, upper=0.08)
                },
            )
            run = BacktestRun(
                run_id="testhash1234567g",
                config=config,
                started_at_utc=datetime.now(UTC),
                completed_at_utc=datetime.now(UTC),
                status="success",
                metrics=metrics,
            )
            manifest_path, _sha = writer.write_run_record(run)
            with open(manifest_path) as f:
                manifest = json.load(f)

            expected_hashes = {
                "config.json",
                "metrics.json",
                "draw_results.csv",
                "tickets.csv",
                "warnings.json",
            }
            actual_hashes = set(manifest["files"].keys())
            self.assertEqual(expected_hashes, actual_hashes)
            for _fname, hash_val in manifest["files"].items():
                self.assertEqual(len(hash_val), 64)
                self.assertTrue(all(c in "0123456789abcdef" for c in hash_val))

    def test_manifest_hash_values_are_correct(self) -> None:
        """Manifest SHA-256 values match actual file contents."""
        with TemporaryDirectory() as tmpdir:
            writer = AtomicArtifactWriter(Path(tmpdir))
            config = BacktestConfig(
                strategy_name="delay_only",
                start_date="2025-01-01",
                end_date="2025-01-10",
                training_window_days=5,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0"*64,
                code_commit_sha="0"*64,
            )
            metrics = BacktestMetrics(
                hit_distribution={1: 9},
                average_hits=1.0,
                hit_rate_2_plus=0.0,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.1666666666,
                baseline_comparison={},
                confidence_intervals={
                    "average_hits": ConfidenceInterval(lower=0.08, upper=0.25)
                },
            )
            run = BacktestRun(
                run_id="testhash1234567h",
                config=config,
                started_at_utc=datetime.now(UTC),
                completed_at_utc=datetime.now(UTC),
                status="success",
                metrics=metrics,
            )
            manifest_path, _sha = writer.write_run_record(run)
            run_dir = manifest_path.parent

            with open(manifest_path) as f:
                manifest = json.load(f)

            for fname, expected_hash in manifest["files"].items():
                fpath = run_dir / fname
                with open(fpath, "rb") as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()
                self.assertEqual(expected_hash, actual_hash)

    def test_idempotent_write_same_content(self) -> None:
        """Writing identical run produces identical core artifacts."""
        with TemporaryDirectory() as tmpdir:
            writer = AtomicArtifactWriter(Path(tmpdir))
            config = BacktestConfig(
                strategy_name="mixed_frequency_delay",
                start_date="2025-01-01",
                end_date="2025-01-10",
                training_window_days=5,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="0"*64,
                code_commit_sha="0"*64,
            )
            metrics = BacktestMetrics(
                hit_distribution={2: 9},
                average_hits=2.0,
                hit_rate_2_plus=1.0,
                hit_rate_3_plus=0.0,
                hit_rate_4_plus=0.0,
                hit_rate_5_plus=0.0,
                hit_rate_6=0.0,
                probability_score=0.333333,
                baseline_comparison={},
                confidence_intervals={
                    "average_hits": ConfidenceInterval(lower=0.25, upper=0.41)
                },
            )
            run = BacktestRun(
                run_id="testhash1234567i",
                config=config,
                started_at_utc=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
                completed_at_utc=datetime(2025, 1, 1, 12, 1, 0, tzinfo=UTC),
                status="success",
                metrics=metrics,
            )

            manifest_path_1, _ = writer.write_run_record(run)
            run_dir = manifest_path_1.parent
            hashes_before = {
                f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                for f in run_dir.iterdir()
                if f.is_file() and f.name not in {"manifest.json", "warnings.json"}
            }

            _, _ = writer.write_run_record(run)
            hashes_after = {
                f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                for f in run_dir.iterdir()
                if f.is_file() and f.name not in {"manifest.json", "warnings.json"}
            }

            self.assertEqual(hashes_before, hashes_after)
