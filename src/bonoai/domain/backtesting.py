"""Backtesting contracts with walk-forward validation and temporal integrity."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal

SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
STRATEGY_NAMES: Final = frozenset(
    ["uniform_random", "frequency_only", "delay_only", "mixed_frequency_delay"]
)


class BacktestContractError(ValueError):
    """Base error for invalid backtesting configuration or results."""


class TemporalLeakageError(BacktestContractError):
    """Raised when backtesting violates temporal integrity."""


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    """Immutable backtesting configuration with reproducibility tracking."""

    strategy_name: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    training_window_days: int
    tickets_per_draw: int
    random_seed: int
    dataset_sha256: str
    code_commit_sha: str
    parameters: dict[str, str | int | float] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.strategy_name not in STRATEGY_NAMES:
            raise BacktestContractError(
                f"strategy_name must be one of {STRATEGY_NAMES}, got {self.strategy_name}"
            )

        for date_val in [self.start_date, self.end_date]:
            try:
                datetime.strptime(date_val, "%Y-%m-%d")
            except ValueError as e:
                raise BacktestContractError(
                    f"date must be YYYY-MM-DD format, got {date_val}"
                ) from e

        if self.start_date >= self.end_date:
            raise BacktestContractError(
                f"start_date {self.start_date} must be before end_date {self.end_date}"
            )

        if self.training_window_days <= 0:
            raise BacktestContractError("training_window_days must be positive")

        if self.tickets_per_draw <= 0 or self.tickets_per_draw > 1000:
            raise BacktestContractError("tickets_per_draw must be in range [1, 1000]")

        if self.random_seed < 0:
            raise BacktestContractError("random_seed must be non-negative")

        if not SHA256_PATTERN.fullmatch(self.dataset_sha256):
            raise BacktestContractError("dataset_sha256 must be 64 lowercase hex characters")

        if not SHA256_PATTERN.fullmatch(self.code_commit_sha):
            raise BacktestContractError("code_commit_sha must be 64 lowercase hex characters")

        if self.parameters is None:
            object.__setattr__(self, "parameters", {})

    @staticmethod
    def canonical_run_id(config: BacktestConfig) -> str:
        """Derive deterministic run_id from canonical config serialization.

        All config fields included for reproducibility:
        schema_version, strategy_name, start_date, end_date,
        training_window_days, tickets_per_draw, random_seed,
        dataset_sha256, code_commit_sha, parameters.
        """
        payload = {
            "schema_version": "2",
            "strategy_name": config.strategy_name,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "training_window_days": config.training_window_days,
            "tickets_per_draw": config.tickets_per_draw,
            "random_seed": config.random_seed,
            "dataset_sha256": config.dataset_sha256,
            "code_commit_sha": config.code_commit_sha,
            "parameters": config.parameters,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    """95% confidence interval for a metric."""

    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not (0 <= self.lower <= self.upper <= 1):
            raise BacktestContractError(
                f"CI bounds must be in [0, 1] with lower <= upper, got [{self.lower}, {self.upper}]"
            )


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    """Scientific metrics from walk-forward validation."""

    hit_distribution: dict[int, int]  # hit_count → frequency
    average_hits: float
    hit_rate_2_plus: float  # P(hits >= 2)
    hit_rate_3_plus: float
    hit_rate_4_plus: float
    hit_rate_5_plus: float
    hit_rate_6: float
    probability_score: float  # log-loss or similar
    baseline_comparison: dict[str, float]  # strategy_name → relative_improvement
    confidence_intervals: dict[str, ConfidenceInterval]

    def __post_init__(self) -> None:
        if not self.hit_distribution:
            raise BacktestContractError("hit_distribution must not be empty")

        total_draws = sum(self.hit_distribution.values())
        if total_draws <= 0:
            raise BacktestContractError("hit_distribution must have positive total")

        for hits, count in self.hit_distribution.items():
            if hits < 0 or hits > 6:
                raise BacktestContractError(f"hit counts must be in [0, 6], got {hits}")
            if count < 0:
                raise BacktestContractError(f"hit frequencies must be non-negative, got {count}")

        if not (0 <= self.average_hits <= 6):
            raise BacktestContractError(f"average_hits must be in [0, 6], got {self.average_hits}")

        for hit_rate in [
            self.hit_rate_2_plus,
            self.hit_rate_3_plus,
            self.hit_rate_4_plus,
            self.hit_rate_5_plus,
            self.hit_rate_6,
        ]:
            if not (0 <= hit_rate <= 1):
                raise BacktestContractError(f"hit_rate must be in [0, 1], got {hit_rate}")

        if not (0 <= self.probability_score <= 1):
            raise BacktestContractError(
                f"probability_score must be in [0, 1], got {self.probability_score}"
            )


@dataclass(frozen=True, slots=True)
class BacktestRun:
    """Complete record of one walk-forward validation run."""

    run_id: str  # deterministic: hash(config, dataset, code)
    config: BacktestConfig
    started_at_utc: datetime
    completed_at_utc: datetime
    status: Literal["success", "failed"]
    metrics: BacktestMetrics | None = None
    warnings: tuple[str, ...] = ()
    artifact_paths: dict[str, str] = None  # type: ignore

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise BacktestContractError("run_id must not be empty")

        if self.started_at_utc.tzinfo is None:
            raise BacktestContractError("started_at_utc must be timezone-aware")

        if self.completed_at_utc.tzinfo is None:
            raise BacktestContractError("completed_at_utc must be timezone-aware")

        if self.completed_at_utc < self.started_at_utc:
            raise BacktestContractError(
                "completed_at_utc must be >= started_at_utc"
            )

        if self.status == "success" and self.metrics is None:
            raise BacktestContractError("successful run must have metrics")

        if self.status == "failed" and self.metrics is not None:
            raise BacktestContractError("failed run must not have metrics")

        if self.artifact_paths is None:
            object.__setattr__(self, "artifact_paths", {})
