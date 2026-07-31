# Walk-Forward Backtesting for Bonoloto

**Scientific Integrity Warning**: This module implements walk-forward validation to prevent temporal leakage. Results reflect historical fitness only and do not predict future lottery outcomes.

## Overview

`bonoai backtest` provides reproducible walk-forward validation using deterministic baseline strategies without machine learning components.

## Commands

### backtest run
Execute walk-forward validation for a strategy across a date range.

```bash
bonoai backtest run \
  --strategy uniform_random \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --training-window 360 \
  --seed 42
```

**Strategies**:
- `uniform_random`: Random selection from all 49 numbers
- `frequency_only`: Favor historically frequent numbers
- `delay_only`: Favor numbers absent from recent draws
- `mixed_frequency_delay`: Combine both signals

**Output**: JSON run record with metrics saved to `backtests/runs/<run_id>/run.json`

### backtest list
List all completed backtest runs.

```bash
bonoai backtest list
```

### backtest show
Display detailed results for a specific run.

```bash
bonoai backtest show <run_id>
bonoai backtest show <run_id> --json
```

### backtest compare
Compare metrics between two runs.

```bash
bonoai backtest compare <run_id_1> <run_id_2>
```

### backtest verify
Verify artifact integrity and completeness.

```bash
bonoai backtest verify <run_id>
```

## Walk-Forward Validation

Each target date `T` in the specified range:
1. **Training data**: All draws with `date < T` within training window
2. **Strategy build**: Apply strategy to training data with fixed seed
3. **Evaluation**: Compare strategy output to actual target draw `T`
4. **Hit count**: Count matching numbers (0-6)

## Temporal Leakage Prevention

The validator raises `TemporalLeakageDetected` if:
- Target date is not in dataset
- Insufficient prior data for training window
- Strategy receives target or future data

## Artifact Structure

```
backtests/runs/<run_id>/
├── run.json          # Complete run record (config, metrics, status)
├── config.json       # BacktestConfig (strategy, dates, hyperparameters)
├── metrics.json      # BacktestMetrics (distributions, hit rates)
├── draw_results.csv  # Per-date results (target_date, hits, numbers)
├── tickets.csv       # Strategy predictions per draw
├── warnings.json     # Dates skipped or warnings
└── manifest.json     # File inventory with SHA-256 hashes
```

All files are written atomically (temp → fsync → os.replace) for crash-safety.

## Metrics

- `average_hits`: Mean number of matches per draw (0-6)
- `hit_rate_2_plus`: % of draws with ≥2 matches
- `hit_rate_3_plus`: % of draws with ≥3 matches
- `hit_rate_4_plus`: % of draws with ≥4 matches
- `hit_rate_5_plus`: % of draws with ≥5 matches
- `hit_rate_6`: % of draws with all 6 matches (jackpot)
- `probability_score`: Normalized average (average_hits / 6)
- `confidence_intervals`: Bounds on metrics (95% CI approximation)

## Scientific Controls

**Determinism**: All strategies are deterministic given seed + training data. Reproduce runs by repeating with same seed.

**Reproducibility**: Each run captures dataset SHA-256 and code commit SHA to verify data/code consistency.

**Negative control**: Compare against random baseline (included in uniform_random strategy).

## Dashboard

View results in Streamlit:

```bash
pip install bonoai[dashboard]
streamlit run src/bonoai/dashboard.py -- --artifacts-dir backtests/runs
```

The dashboard is read-only; edit runs via CLI or direct artifact manipulation.

## No Machine Learning

This module excludes all ML: no XGBoost, LightGBM, CatBoost, RandomForest, or ensemble methods. Strategies are heuristic-only.
