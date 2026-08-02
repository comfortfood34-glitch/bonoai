"""Dashboard MVP for backtest results (read-only Streamlit UI)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bonoai.application.dashboard_viewmodel import (
    format_status_label,
    get_run_info,
    list_runs,
    prepare_config_display,
    validate_run_data,
)

if TYPE_CHECKING:
    import streamlit as st
else:
    try:
        import streamlit as st  # type: ignore[import-not-found]
    except ImportError:
        st = None  # type: ignore[assignment]


def load_run_data(run_dir: Path) -> dict[str, Any] | None:
    """Legacy import-compatible wrapper."""
    from bonoai.application.dashboard_viewmodel import load_run_data as _load

    return _load(run_dir)


def main(artifacts_dir: str = "backtests/runs") -> None:
    """Dashboard main entry point - Streamlit UI only."""
    if st is None:
        raise ImportError("Streamlit required for dashboard; install with: pip install streamlit")

    env_artifacts_dir = os.environ.get("BONOAI_BACKTEST_RUNS_DIR")
    final_artifacts_dir = env_artifacts_dir if env_artifacts_dir else artifacts_dir

    st.set_page_config(page_title="BonoAI Backtest Dashboard", layout="wide")
    st.title("🎰 BonoAI Backtest Results")
    st.markdown("Walk-forward validation without temporal leakage")
    st.markdown("---")

    artifacts_path = Path(final_artifacts_dir)

    run_ids = list_runs(artifacts_path)
    if not run_ids:
        st.warning("No backtest runs available")
        return

    selected_run = st.selectbox("Select Run", run_ids, key="run_select")

    if selected_run:
        data = get_run_info(artifacts_path, selected_run)

        if data:
            is_valid, error_msg = validate_run_data(data)
            if not is_valid:
                st.error(error_msg)
                return

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Strategy", data["config"]["strategy_name"])
            with col2:
                status_label = format_status_label(data["status"])
                st.metric("Status", status_label)
            with col3:
                metrics = data["metrics"]
                st.metric("Avg Hits", f"{metrics.get('average_hits', 0.0):.2f}")

            st.divider()

            metrics = data["metrics"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Hit Rate (2+)", f"{metrics.get('hit_rate_2_plus', 0.0):.1%}")
            with col2:
                st.metric("Hit Rate (3+)", f"{metrics.get('hit_rate_3_plus', 0.0):.1%}")
            with col3:
                st.metric("Hit Rate (4+)", f"{metrics.get('hit_rate_4_plus', 0.0):.1%}")
            with col4:
                st.metric("Hit Rate (6)", f"{metrics.get('hit_rate_6', 0.0):.1%}")

            st.divider()
            st.subheader("Distribution")

            hit_dist = metrics.get("hit_distribution", {})
            if hit_dist:
                try:
                    import pandas as pd  # type: ignore[import-untyped]

                    dist_df = pd.DataFrame(
                        list(hit_dist.items()),
                        columns=["Hits", "Count"]
                    )
                    st.bar_chart(dist_df.set_index("Hits"))
                except ImportError:
                    st.info("pandas required for charts")

            st.divider()
            st.subheader("Configuration")
            config_display = prepare_config_display(data["config"])
            st.json(config_display)

        else:
            st.error(f"Failed to load {selected_run}")


if __name__ == "__main__":
    main()
