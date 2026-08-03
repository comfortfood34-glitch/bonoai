"""Dashboard main() function tests with mocked Streamlit."""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from bonoai.dashboard import _resolve_artifacts_dir


class TestDashboardMainFunction(TestCase):
    """Test dashboard main() function logic with mocked Streamlit."""

    def test_main_raises_import_error_when_streamlit_missing(self) -> None:
        """main() raises ImportError when st is None."""
        from bonoai.dashboard import main

        with patch("bonoai.dashboard.st", None):
            with self.assertRaises(ImportError) as ctx:
                main()
            self.assertIn("Streamlit required", str(ctx.exception))

    def test_main_calls_resolve_artifacts_dir(self) -> None:
        """main() calls _resolve_artifacts_dir() to get data path."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("examples/demo_backtests"), True),
        )

        with mock_st as st_mock, mock_resolve as resolve_mock:
            st_mock.selectbox.return_value = None
            main()
            resolve_mock.assert_called_once()

    def test_main_displays_demo_banner_when_is_demo_true(self) -> None:
        """main() displays warning banner when is_demo flag is True."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("examples/demo_backtests"), True),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=["run_001"],
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs:
            st_mock.selectbox.return_value = None
            main()
            st_mock.warning.assert_called_once()
            warning_call = st_mock.warning.call_args[0][0]
            self.assertIn("MODO DEMONSTRAÇÃO", warning_call)
            self.assertIn("dados sintéticos", warning_call)

    def test_main_no_banner_when_official_data(self) -> None:
        """main() does not display banner for official data."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=["run_001"],
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs:
            st_mock.selectbox.return_value = None
            main()
            st_mock.warning.assert_not_called()

    def test_main_handles_no_runs_available(self) -> None:
        """main() shows warning when no runs are available."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=[],
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs:
            main()
            st_mock.warning.assert_called_with("No backtest runs available")

    def test_main_handles_failed_run_load(self) -> None:
        """main() shows error when run data fails to load."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=["run_001"],
        )
        mock_get_info = patch(
            "bonoai.dashboard.get_run_info",
            return_value=None,
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs, mock_get_info:
            st_mock.selectbox.return_value = "run_001"
            main()
            st_mock.error.assert_called_once()
            call_args = st_mock.error.call_args[0][0]
            self.assertIn("Failed to load", call_args)

    def test_main_handles_invalid_run_data(self) -> None:
        """main() shows error when run data validation fails."""
        from bonoai.dashboard import main

        mock_st = patch("bonoai.dashboard.st")
        mock_resolve = patch(
            "bonoai.dashboard._resolve_artifacts_dir",
            return_value=(Path("backtests/runs"), False),
        )
        mock_list_runs = patch(
            "bonoai.dashboard.list_runs",
            return_value=["run_001"],
        )
        mock_get_info = patch(
            "bonoai.dashboard.get_run_info",
            return_value={"config": {}},
        )
        mock_validate = patch(
            "bonoai.dashboard.validate_run_data",
            return_value=(False, "Invalid data"),
        )

        with mock_st as st_mock, mock_resolve, mock_list_runs, \
             mock_get_info, mock_validate:
            st_mock.selectbox.return_value = "run_001"
            main()
            st_mock.error.assert_called_with("Invalid data")

    def test_fallback_returns_default_when_no_paths_exist(self) -> None:
        """_resolve_artifacts_dir returns default when all paths missing."""
        import os

        with patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "exists", return_value=False):
            path, is_demo = _resolve_artifacts_dir()
            self.assertEqual(path, Path("backtests/runs"))
            self.assertFalse(is_demo)
