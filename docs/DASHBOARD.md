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

Or with custom artifacts directory (official data):

```bash
export BONOAI_BACKTEST_RUNS_DIR=/path/to/backtests/runs
streamlit run src/bonoai/dashboard.py
```

The dashboard starts on `http://localhost:8501`

### Data Sources & Priority

The dashboard automatically selects data in this order:

1. **Environment Variable** (highest priority)
   - `BONOAI_BACKTEST_RUNS_DIR` - Path to official backtest results
   - Example: `export BONOAI_BACKTEST_RUNS_DIR=/data/official_backtests`

2. **Local Directory**
   - `backtests/runs/` - Local official backtest results
   - Used if env var not set and directory contains valid runs

3. **Demo Data** (lowest priority, fallback)
   - `examples/demo_backtests/` - Synthetic demonstration data
   - Used only when no official data is available
   - **Shows mandatory banner**: "MODO DEMONSTRAÇÃO — dados sintéticos, não correspondem a resultados oficiais da Bonoloto."

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

## Public Deployment (Streamlit Community Cloud)

### Prerequisites

- GitHub repository with BonoAI code pushed
- Streamlit Community Cloud account (free at https://streamlit.io/cloud)
- Demo data in `examples/demo_backtests/` (versionized in repo)

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git checkout feat/public-dashboard-deployment
   git push -u origin feat/public-dashboard-deployment
   ```

2. **Create PR to main** (optional, for review)
   ```bash
   gh pr create --base main --title "feat: public dashboard deployment"
   ```

3. **Deploy to Streamlit Community Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app" → "GitHub repository"
   - Select: `comfortfood34-glitch/bonoai`
   - Branch: `feat/public-dashboard-deployment` (or `main` after merge)
   - Main file path: `src/bonoai/dashboard.py`
   - Click "Deploy"

4. **Configure Environment (if using official data)**
   - In Streamlit Cloud dashboard, go to app settings
   - Add Secrets (if official data URL or path needed):
     ```toml
     [env]
     BONOAI_BACKTEST_RUNS_DIR = "/path/or/url/to/official/data"
     ```
   - Currently: Demo data only (no secrets needed)

### URL & Sharing

Once deployed, the dashboard is available at:
```
https://bonoai-dashboard.streamlit.app/
```

The URL is permanent and can be shared publicly.

### Data Strategy for Public Deployment

**Current Approach (Demo Only)**
- Dashboard uses `examples/demo_backtests/` with demo data
- Banner clearly states: "MODO DEMONSTRAÇÃO — dados sintéticos"
- No official data exposed publicly
- Safe for unlimited public access

**Future Approach (with Official Data)**
To enable official data on public dashboard:
1. Set `BONOAI_BACKTEST_RUNS_DIR` secret in Streamlit Cloud settings
2. Point to official historical data (read-only)
3. Verify banner is NOT shown (official data only)
4. Monitor for data leaks or misuse

### Monitoring & Maintenance

- Check app logs in Streamlit Cloud dashboard
- Monitor for errors or crashes
- Review traffic and usage patterns
- Update demo data as needed
- Never commit official data to repository
