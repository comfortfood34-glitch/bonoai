"""Tests for CLI exception handling."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

from bonoai.cli import main


class CliExceptionTests(TestCase):
    def test_cli_main_with_data_contract_error(self) -> None:
        """Verify main() catches DataContractError from bootstrap."""
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            csv_file = Path(directory) / "bad.csv"
            csv_file.write_text("bad", encoding="utf-8")

            argv = [
                "data-bootstrap",
                "--file",
                str(csv_file),
                "--source-name",
                "test",
                "--data-dir",
                str(data_dir),
            ]

            with self.assertRaises(SystemExit):
                main(argv)

    def test_cli_main_with_runtime_error(self) -> None:
        """Verify main() catches RuntimeError."""
        with (
            mock.patch("bonoai.cli._run_info", side_effect=RuntimeError("test error")),
            self.assertRaises(SystemExit),
        ):
            main(["info"])

    def test_cli_main_with_value_error(self) -> None:
        """Verify main() catches ValueError."""
        with (
            mock.patch("bonoai.cli._run_info", side_effect=ValueError("test error")),
            self.assertRaises(SystemExit),
        ):
            main(["info"])
