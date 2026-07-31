"""CLI integration tests for backtest commands."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from bonoai.cli import build_parser
from bonoai.cli_backtest import run_backtest_command


class TestBacktestCliParser(TestCase):
    """Verify backtest CLI parser structure."""

    def test_backtest_command_exists_in_parser(self) -> None:
        """Backtest command is registered in main parser."""
        parser = build_parser()
        args = parser.parse_args(["backtest", "list"])
        self.assertEqual(args.command, "backtest")
        self.assertEqual(args.backtest_command, "list")

    def test_backtest_run_subcommand_exists(self) -> None:
        """'backtest run' subcommand is registered."""
        parser = build_parser()
        args = parser.parse_args([
            "backtest", "run",
            "--strategy", "uniform_random",
            "--start-date", "2025-01-01",
            "--end-date", "2025-01-31"
        ])
        self.assertEqual(args.backtest_command, "run")
        self.assertEqual(args.strategy, "uniform_random")

    def test_backtest_list_subcommand_exists(self) -> None:
        """'backtest list' subcommand is registered."""
        parser = build_parser()
        args = parser.parse_args(["backtest", "list"])
        self.assertEqual(args.backtest_command, "list")

    def test_backtest_show_subcommand_exists(self) -> None:
        """'backtest show' subcommand is registered."""
        parser = build_parser()
        args = parser.parse_args(["backtest", "show", "test_run_id"])
        self.assertEqual(args.backtest_command, "show")
        self.assertEqual(args.run_id, "test_run_id")

    def test_backtest_compare_subcommand_exists(self) -> None:
        """'backtest compare' subcommand is registered."""
        parser = build_parser()
        args = parser.parse_args(["backtest", "compare", "run1", "run2"])
        self.assertEqual(args.backtest_command, "compare")
        self.assertEqual(args.run_id_1, "run1")
        self.assertEqual(args.run_id_2, "run2")

    def test_backtest_verify_subcommand_exists(self) -> None:
        """'backtest verify' subcommand is registered."""
        parser = build_parser()
        args = parser.parse_args(["backtest", "verify", "run_id"])
        self.assertEqual(args.backtest_command, "verify")
        self.assertEqual(args.run_id, "run_id")

    def test_backtest_run_requires_strategy(self) -> None:
        """backtest run requires --strategy argument."""
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["backtest", "run", "--start-date", "2025-01-01"])

    def test_backtest_run_requires_start_date(self) -> None:
        """backtest run requires --start-date argument."""
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "backtest", "run",
                "--strategy", "uniform_random",
                "--end-date", "2025-01-31"
            ])

    def test_backtest_run_requires_end_date(self) -> None:
        """backtest run requires --end-date argument."""
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "backtest", "run",
                "--strategy", "uniform_random",
                "--start-date", "2025-01-01"
            ])


class TestBacktestCommandDispatch(TestCase):
    """Verify backtest command dispatch."""

    def test_run_command_dispatches_to_run_handler(self) -> None:
        """Dispatch recognizes 'run' subcommand."""
        args = MagicMock()
        args.backtest_command = "run"
        with patch('bonoai.cli_backtest._run_backtest_run', return_value=0) as mock_run:
            result = run_backtest_command(args)
            mock_run.assert_called_once_with(args)
            self.assertEqual(result, 0)

    def test_list_command_dispatches_to_list_handler(self) -> None:
        """Dispatch recognizes 'list' subcommand."""
        args = MagicMock()
        args.backtest_command = "list"
        with patch('bonoai.cli_backtest._run_backtest_list', return_value=0) as mock_list:
            result = run_backtest_command(args)
            mock_list.assert_called_once_with(args)
            self.assertEqual(result, 0)

    def test_show_command_dispatches_to_show_handler(self) -> None:
        """Dispatch recognizes 'show' subcommand."""
        args = MagicMock()
        args.backtest_command = "show"
        with patch('bonoai.cli_backtest._run_backtest_show', return_value=0) as mock_show:
            result = run_backtest_command(args)
            mock_show.assert_called_once_with(args)
            self.assertEqual(result, 0)

    def test_compare_command_dispatches_to_compare_handler(self) -> None:
        """Dispatch recognizes 'compare' subcommand."""
        args = MagicMock()
        args.backtest_command = "compare"
        with patch('bonoai.cli_backtest._run_backtest_compare', return_value=0) as mock_cmp:
            result = run_backtest_command(args)
            mock_cmp.assert_called_once_with(args)
            self.assertEqual(result, 0)

    def test_verify_command_dispatches_to_verify_handler(self) -> None:
        """Dispatch recognizes 'verify' subcommand."""
        args = MagicMock()
        args.backtest_command = "verify"
        with patch('bonoai.cli_backtest._run_backtest_verify', return_value=0) as mock_ver:
            result = run_backtest_command(args)
            mock_ver.assert_called_once_with(args)
            self.assertEqual(result, 0)

    def test_invalid_subcommand_returns_error_code(self) -> None:
        """Dispatch returns 2 for unknown subcommand."""
        args = MagicMock()
        args.backtest_command = "invalid"
        result = run_backtest_command(args)
        self.assertEqual(result, 2)


class TestBacktestListCommand(TestCase):
    """Verify backtest list command."""

    def test_list_command_returns_0_on_success(self) -> None:
        """List command returns 0 when no runs exist."""
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.as_json = False
            from bonoai.cli_backtest import _run_backtest_list
            result = _run_backtest_list(args)
            self.assertEqual(result, 0)

    def test_list_command_returns_0_with_json_flag(self) -> None:
        """List command returns 0 with --json flag."""
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.as_json = True
            from bonoai.cli_backtest import _run_backtest_list
            result = _run_backtest_list(args)
            self.assertEqual(result, 0)


class TestBacktestVerifyCommand(TestCase):
    """Verify backtest verify command."""

    def test_verify_missing_run_returns_error(self) -> None:
        """Verify returns 2 when run not found."""
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.artifacts_dir = Path(tmpdir)
            args.run_id = "nonexistent"
            args.as_json = False
            from bonoai.cli_backtest import _run_backtest_verify
            result = _run_backtest_verify(args)
            self.assertEqual(result, 2)
