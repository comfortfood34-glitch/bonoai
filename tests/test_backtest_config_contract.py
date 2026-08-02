"""Tests for BacktestConfig and ConfidenceInterval contracts."""

from __future__ import annotations

from unittest import TestCase

from bonoai.domain.backtesting import (
    BacktestConfig,
    BacktestContractError,
    ConfidenceInterval,
)


class TestBacktestConfigValidation(TestCase):
    """Validate BacktestConfig contract enforcement."""

    def test_valid_config_creates_successfully(self) -> None:
        """Valid config is accepted."""
        config = BacktestConfig(
            strategy_name="uniform_random",
            start_date="2025-01-01",
            end_date="2025-12-31",
            training_window_days=360,
            tickets_per_draw=10,
            random_seed=42,
            dataset_sha256="a" * 64,
            code_commit_sha="b" * 64,
        )
        self.assertEqual(config.strategy_name, "uniform_random")

    def test_invalid_strategy_raises_error(self) -> None:
        """Invalid strategy name raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="invalid_strategy",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_date_format_raises_error(self) -> None:
        """Invalid date format raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="01/01/2025",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_start_after_end_raises_error(self) -> None:
        """Start date >= end date raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-12-31",
                end_date="2025-01-01",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_negative_training_window_raises_error(self) -> None:
        """Negative training window raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=-1,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_sha256_raises_error(self) -> None:
        """Non-hex SHA-256 raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=42,
                dataset_sha256="zzzz" + "a" * 60,
                code_commit_sha="b" * 64,
            )

    def test_negative_random_seed_raises_error(self) -> None:
        """Negative random_seed raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=10,
                random_seed=-1,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_tickets_per_draw_zero_raises_error(self) -> None:
        """Zero tickets_per_draw raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=0,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )

    def test_invalid_tickets_per_draw_too_large_raises_error(self) -> None:
        """tickets_per_draw > 1000 raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            BacktestConfig(
                strategy_name="uniform_random",
                start_date="2025-01-01",
                end_date="2025-12-31",
                training_window_days=360,
                tickets_per_draw=1001,
                random_seed=42,
                dataset_sha256="a" * 64,
                code_commit_sha="b" * 64,
            )


class TestConfidenceInterval(TestCase):
    """Validate ConfidenceInterval contract."""

    def test_valid_interval_creates_successfully(self) -> None:
        """Valid CI is accepted."""
        ci = ConfidenceInterval(lower=0.1, upper=0.9)
        self.assertEqual(ci.lower, 0.1)

    def test_lower_greater_than_upper_raises_error(self) -> None:
        """lower > upper raises BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            ConfidenceInterval(lower=0.9, upper=0.1)

    def test_out_of_range_raises_error(self) -> None:
        """Values outside [0, 1] raise BacktestContractError."""
        with self.assertRaises(BacktestContractError):
            ConfidenceInterval(lower=-0.1, upper=0.5)
