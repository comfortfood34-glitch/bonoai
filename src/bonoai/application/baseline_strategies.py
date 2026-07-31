"""Baseline strategies for scientific backtesting without ML.

All strategies are deterministic given the same data and random seed.
None use or reveal the target draw. All follow lottery probability integrity.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable

from bonoai.domain.data import CanonicalDrawRecord
from bonoai.domain.models import DRAW_SIZE, NUMBER_MAX, NUMBER_MIN

StrategyFunction = Callable[[tuple[CanonicalDrawRecord, ...], int], tuple[int, ...]]


def uniform_random_strategy(
    training_draws: tuple[CanonicalDrawRecord, ...], random_seed: int
) -> tuple[int, ...]:
    """Generate numbers uniformly at random.

    Provides scientific control: baseline with no structural information.
    Same seed + data = same result (deterministic).
    """
    rng = random.Random(random_seed)
    numbers = tuple(sorted(rng.sample(range(NUMBER_MIN, NUMBER_MAX + 1), DRAW_SIZE)))
    return numbers


def frequency_only_strategy(
    training_draws: tuple[CanonicalDrawRecord, ...], random_seed: int
) -> tuple[int, ...]:
    """Select numbers by historical frequency (most frequent first)."""
    if not training_draws:
        return uniform_random_strategy(training_draws, random_seed)

    counter: Counter[int] = Counter()
    for record in training_draws:
        for num in record.draw.numbers:
            counter[num] += 1

    most_common = counter.most_common(DRAW_SIZE)
    if len(most_common) < DRAW_SIZE:
        rng = random.Random(random_seed)
        remaining = [
            n for n in range(NUMBER_MIN, NUMBER_MAX + 1)
            if n not in {num for num, _ in most_common}
        ]
        missing = rng.sample(remaining, DRAW_SIZE - len(most_common))
        most_common.extend((n, 0) for n in missing)

    numbers = tuple(sorted(num for num, _ in most_common[:DRAW_SIZE]))
    return numbers


def delay_only_strategy(
    training_draws: tuple[CanonicalDrawRecord, ...], random_seed: int
) -> tuple[int, ...]:
    """Select numbers with highest 'delay' (days since last appearance).

    Delay = days between last draw and most recent target date.
    Highest delays are assumed 'due' in simple statistical intuition.
    """
    if not training_draws:
        return uniform_random_strategy(training_draws, random_seed)

    most_recent_date = training_draws[-1].draw.held_on
    last_draw_date: dict[int, int] = {}

    for record in sorted(training_draws, key=lambda r: r.draw.held_on):
        for num in record.draw.numbers:
            last_draw_date[num] = (most_recent_date - record.draw.held_on).days

    delays = [(num, delay) for num, delay in last_draw_date.items()]
    if not delays:
        return uniform_random_strategy(training_draws, random_seed)

    delays.sort(key=lambda x: (-x[1], x[0]))  # descending delay, ascending number for tie-break
    numbers = tuple(sorted(num for num, _ in delays[:DRAW_SIZE]))
    return numbers


def mixed_frequency_delay_strategy(
    training_draws: tuple[CanonicalDrawRecord, ...], random_seed: int
) -> tuple[int, ...]:
    """Blend frequency and delay: weighted score by both signals.

    Score = 0.6 * normalized_frequency + 0.4 * normalized_delay
    Deterministic weighting, no hyperparameter tuning on holdout.
    """
    if not training_draws:
        return uniform_random_strategy(training_draws, random_seed)

    most_recent_date = training_draws[-1].draw.held_on
    freq: Counter[int] = Counter()
    last_draw_date: dict[int, int] = {}

    for record in sorted(training_draws, key=lambda r: r.draw.held_on):
        for num in record.draw.numbers:
            freq[num] += 1
            last_draw_date[num] = (most_recent_date - record.draw.held_on).days

    if not freq:
        return uniform_random_strategy(training_draws, random_seed)

    max_freq = max(freq.values()) if freq else 1
    max_delay = max(last_draw_date.values()) if last_draw_date else 1

    scores: list[tuple[int, float]] = []
    for num in range(NUMBER_MIN, NUMBER_MAX + 1):
        norm_freq = freq.get(num, 0) / max_freq if max_freq > 0 else 0.0
        norm_delay = last_draw_date.get(num, 0) / max_delay if max_delay > 0 else 0.0
        score = 0.6 * norm_freq + 0.4 * norm_delay
        scores.append((num, score))

    scores.sort(key=lambda x: (-x[1], x[0]))  # descending score, ascending number for tie-break
    numbers = tuple(sorted(num for num, _ in scores[:DRAW_SIZE]))
    return numbers


BASELINE_STRATEGIES: dict[str, StrategyFunction] = {
    "uniform_random": uniform_random_strategy,
    "frequency_only": frequency_only_strategy,
    "delay_only": delay_only_strategy,
    "mixed_frequency_delay": mixed_frequency_delay_strategy,
}
