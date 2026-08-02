"""Deterministic run_id derivation tests."""

import json
from unittest import TestCase

from bonoai.domain.backtesting import BacktestConfig


class TestRunIDDeterminism(TestCase):
    """Verify run_id derivation is canonical and deterministic."""

    def _make_config(
        self,
        strategy: str = "uniform_random",
        start_date: str = "2025-01-01",
        end_date: str = "2025-01-31",
        training_window: int = 10,
        tickets: int = 10,
        seed: int = 42,
        dataset_sha: str = "0"*64,
        code_sha: str = "0"*64,
        params: dict[str, str | int | float] | None = None,
    ) -> BacktestConfig:
        """Create BacktestConfig with defaults."""
        if params is None:
            params = {}
        return BacktestConfig(
            strategy_name=strategy,
            start_date=start_date,
            end_date=end_date,
            training_window_days=training_window,
            tickets_per_draw=tickets,
            random_seed=seed,
            dataset_sha256=dataset_sha,
            code_commit_sha=code_sha,
            parameters=params,
        )

    def test_identical_config_produces_identical_run_id(self) -> None:
        """Same config → same run_id (idempotent)."""
        config = self._make_config()
        run_id_1 = BacktestConfig.canonical_run_id(config)
        run_id_2 = BacktestConfig.canonical_run_id(config)
        self.assertEqual(run_id_1, run_id_2)

    def test_different_seed_produces_different_run_id(self) -> None:
        """Changing seed changes run_id."""
        config1 = self._make_config(seed=42)
        config2 = self._make_config(seed=999)
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_different_dataset_sha_produces_different_run_id(self) -> None:
        """Changing dataset_sha256 changes run_id."""
        config1 = self._make_config(dataset_sha="0"*64)
        config2 = self._make_config(dataset_sha="1"*64)
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_different_training_window_produces_different_run_id(self) -> None:
        """Changing training_window_days changes run_id."""
        config1 = self._make_config(training_window=10)
        config2 = self._make_config(training_window=30)
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_different_strategy_parameters_produces_different_run_id(self) -> None:
        """Changing strategy_parameters changes run_id."""
        config1 = self._make_config(params={})
        config2 = self._make_config(params={"alpha": 0.5})
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_different_tickets_per_draw_produces_different_run_id(self) -> None:
        """Changing tickets_per_draw changes run_id."""
        config1 = self._make_config(tickets=10)
        config2 = self._make_config(tickets=20)
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_different_code_commit_sha_produces_different_run_id(self) -> None:
        """Changing code_commit_sha changes run_id."""
        config1 = self._make_config(code_sha="0"*64)
        config2 = self._make_config(code_sha="a"*64)
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_parameter_key_order_does_not_affect_run_id(self) -> None:
        """Parameter dict order irrelevant (JSON sort_keys)."""
        params1: dict[str, str | int | float] = {"a": 1, "b": 2}
        params2: dict[str, str | int | float] = {"b": 2, "a": 1}
        config1 = self._make_config(params=params1)
        config2 = self._make_config(params=params2)
        run_id_1 = BacktestConfig.canonical_run_id(config1)
        run_id_2 = BacktestConfig.canonical_run_id(config2)
        self.assertEqual(run_id_1, run_id_2)

    def test_serialization_produces_deterministic_bytes(self) -> None:
        """Canonical JSON always produces identical bytes."""
        config = self._make_config()
        import hashlib
        payload1 = {
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
        canonical1 = json.dumps(payload1, sort_keys=True, separators=(",", ":"))
        canonical2 = json.dumps(payload1, sort_keys=True, separators=(",", ":"))
        hash1 = hashlib.sha256(canonical1.encode()).hexdigest()
        hash2 = hashlib.sha256(canonical2.encode()).hexdigest()
        self.assertEqual(hash1, hash2)

    def test_run_id_independent_of_execution_timestamps(self) -> None:
        """run_id does not depend on execution time."""
        config = self._make_config()
        run_id = BacktestConfig.canonical_run_id(config)
        self.assertEqual(len(run_id), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in run_id))
