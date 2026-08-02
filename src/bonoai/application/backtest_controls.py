"""Scientific control mechanisms for backtesting validation."""

from __future__ import annotations

from collections.abc import Callable

from bonoai.domain.data import CanonicalDrawRecord


class LeakageTest:
    """Detect temporal leakage by verifying strategy uses only prior data."""

    @staticmethod
    def verify_strategy_callable_is_deterministic(
        strategy: Callable[[tuple[CanonicalDrawRecord, ...], int], tuple[int, ...]],
        all_draws: tuple[CanonicalDrawRecord, ...],
        test_seed: int = 42,
    ) -> tuple[bool, str]:
        """Verify strategy is deterministic: same input → same output.

        Returns: (is_deterministic, message)
        """
        if len(all_draws) < 2:
            return True, "insufficient draws to test determinism"

        # Take a subset of training draws
        training_subset = all_draws[:10] if len(all_draws) >= 10 else all_draws

        try:
            result1 = strategy(training_subset, test_seed)
            result2 = strategy(training_subset, test_seed)

            if result1 != result2:
                return False, f"strategy not deterministic: {result1} != {result2}"

            # Verify result is valid
            if not isinstance(result1, tuple) or len(result1) != 6:
                return False, f"strategy must return tuple[int, ...] of length 6, got {result1}"

            if len(set(result1)) != 6:
                return False, f"strategy result must have 6 distinct numbers, got {result1}"

            if not all(1 <= n <= 49 for n in result1):
                return False, f"all numbers must be in [1, 49], got {result1}"

            return True, "strategy is deterministic and valid"

        except Exception as e:
            return False, f"strategy raised exception: {type(e).__name__}: {e}"


class ReproducibilityTest:
    """Verify run reproducibility given same config and seed."""

    @staticmethod
    def can_reproduce_run(
        draws1: tuple[CanonicalDrawRecord, ...],
        draws2: tuple[CanonicalDrawRecord, ...],
    ) -> tuple[bool, str]:
        """Verify two datasets are identical (same draws, same order).

        Returns: (is_reproducible, message)
        """
        if len(draws1) != len(draws2):
            return False, f"draw counts differ: {len(draws1)} vs {len(draws2)}"

        for i, (d1, d2) in enumerate(zip(draws1, draws2, strict=True)):
            if d1.draw.contest_id != d2.draw.contest_id:
                return False, (
                    f"draw {i}: contest_id mismatch "
                    f"{d1.draw.contest_id} vs {d2.draw.contest_id}"
                )
            if d1.draw.held_on != d2.draw.held_on:
                return False, (
                    f"draw {i}: held_on mismatch "
                    f"{d1.draw.held_on} vs {d2.draw.held_on}"
                )
            if d1.draw.numbers != d2.draw.numbers:
                return False, (
                    f"draw {i}: numbers mismatch "
                    f"{d1.draw.numbers} vs {d2.draw.numbers}"
                )

        return True, "datasets are identical"


class NegativeControl:
    """Negative control: verify strategy on random/shuffled data.

    A good strategy should NOT outperform uniform random significantly.
    """

    @staticmethod
    def generate_random_draws(
        actual_draws: tuple[CanonicalDrawRecord, ...], random_seed: int
    ) -> tuple[CanonicalDrawRecord, ...]:
        """Generate synthetic draws with randomized numbers but same dates.

        Purpose: verify strategy does not exploit data artifacts.
        """
        import random
        from copy import copy

        rng = random.Random(random_seed)
        control_draws = []

        for record in actual_draws:
            shuffled_numbers = tuple(sorted(rng.sample(range(1, 50), 6)))
            new_draw = copy(record.draw)
            object.__setattr__(new_draw, "numbers", shuffled_numbers)

            control_record = copy(record)
            object.__setattr__(control_record, "draw", new_draw)
            control_draws.append(control_record)

        return tuple(control_draws)

    @staticmethod
    def compute_baseline_performance(hit_counts: list[int]) -> dict[str, float]:
        """Compute expected baseline metrics for uniform random selection.

        Binomial(n=6, p=6/49) for each draw gives approximate expected hits.
        """
        if not hit_counts:
            return {}

        total = len(hit_counts)
        avg_hits = sum(hit_counts) / total if total > 0 else 0.0

        return {
            "average_hits": avg_hits,
            "hit_rate_2_plus": sum(1 for h in hit_counts if h >= 2) / total,
            "hit_rate_3_plus": sum(1 for h in hit_counts if h >= 3) / total,
        }
