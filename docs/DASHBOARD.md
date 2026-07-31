# BonoAI Backtest Dashboard

## Setup

### Installation

Install Streamlit optional dependency:

```bash
pip install bonoai[dashboard]
```

Or install Streamlit directly:

```bash
pip install streamlit>=1.40,<2.0
```

Verify:
```bash
python -c "import streamlit; print(streamlit.__version__)"
```

### Launch

Run the dashboard:

```bash
streamlit run src/bonoai/dashboard.py
```

Or with custom artifacts directory:

```bash
streamlit run src/bonoai/dashboard.py -- --artifacts-dir /path/to/backtests/runs
```

The dashboard starts on `http://localhost:8501`

## Features

### Run Selection
Dropdown to choose from all completed backtest runs. Runs are identified by run_id (first 16 chars of SHA-256 hash).

### Metrics Display
- **Strategy**: Selected strategy name
- **Status**: Success/Failed indicator
- **Average Hits**: Mean number of matches per draw

### Hit Rate Distribution
Four-column layout showing:
- Hit Rate (2+): % draws with ≥2 matches
- Hit Rate (3+): % draws with ≥3 matches
- Hit Rate (4+): % draws with ≥4 matches
- Hit Rate (6): % draws with all 6 matches (jackpot probability)

### Distribution Chart
Bar chart showing frequency of hit counts (0-6 matches).

### Configuration Summary
JSON display of:
- Date period (start → end)
- Training window days
- Random seed

## Read-Only Constraint

The dashboard is **read-only**. It displays artifacts only:
- Cannot modify run records
- Cannot delete runs
- Cannot create new runs (use CLI)

To modify data, edit artifact files directly or use CLI commands:
```bash
bonoai backtest run ...     # Create new run
bonoai backtest verify ...  # Check integrity
```

## Scientific Integrity

**Warning**: Results show historical fitness only. Lottery outcomes are random. This analysis does not predict future draws.

## Artifact Files

The dashboard reads from the following structure:
```
backtests/runs/<run_id>/
├── config.json        # BacktestConfig
├── metrics.json       # BacktestMetrics
├── draw_results.csv   # Results per draw
├── tickets.csv        # Predicted tickets
├── warnings.json      # Warnings/omissions
└── manifest.json      # SHA-256 hashes
```

The dashboard requires at least `config.json` and `metrics.json` to display results.

## Troubleshooting

### "No backtests found"
- Check `--artifacts-dir` path exists
- Verify runs have `manifest.json` in `<run_id>/` subdirectories
- Run: `ls backtests/runs/*/manifest.json`

### "Failed to load metrics"
- Check JSON is valid: `cat backtests/runs/<run_id>/metrics.json | python -m json.tool`
- Check file permissions: `ls -l backtests/runs/<run_id>/metrics.json`

### Streamlit not found
- Install: `pip install bonoai[dashboard]`
- Or: `pip install streamlit>=1.40`
