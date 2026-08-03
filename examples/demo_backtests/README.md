# Demo Backtests

Synthetic backtest results for demonstration purposes only.

**These results do NOT correspond to official Bonoloto draws.**

Use `BONOAI_BACKTEST_RUNS_DIR` environment variable to specify real backtest runs.

## Files

- `demo_run_001/`: Example uniform_random strategy execution
  - Contains 6 canonical artifacts (config.json, metrics.json, etc.)
  - Demonstrates dashboard functionality
  - For reference only

## Usage

```bash
# Local development with demo data
export BONOAI_BACKTEST_RUNS_DIR=examples/demo_backtests
streamlit run src/bonoai/dashboard.py
```

The dashboard will display "MODO DEMONSTRAÇÃO" banner to indicate synthetic data.
