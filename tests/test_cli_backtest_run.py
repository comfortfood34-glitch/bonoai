"""Tests for CLI backtest run command execution."""

import argparse
import json
from datetime import UTC, date, datetime
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli_backtest import _run_backtest_run
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository


class TestBacktestRunCommand(TestCase):
    """Test CLI backtest run command execution."""

    def setUp(self) -> None:
        """Set up test directories."""
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name) / "data"
        self.data_dir.mkdir()
        (self.data_dir / "processed").mkdir()
        (self.data_dir / "raw").mkdir()

        self.artifacts_dir = Path(self.tmpdir.name) / "artifacts"
        self.artifacts_dir.mkdir()

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def _add_draw_records(self, count: int = 10) -> None:
        """Add draw records to repository."""
        repo = CsvDrawRepository(self.data_dir / "processed" / "draws.csv")
        retrieved_at = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
        for i in range(count):
            day = (i % 28) + 1
            record = CanonicalDrawRecord(
                draw=Draw(
                    contest_id=f"test:{2025}-01-{day:02d}",
                    held_on=date(2025, 1, day),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=0,
                ),
                provenance=
                    SourceProvenance(
                        source_name="test",
                        source_url="https://test.local",
                        retrieved_at_utc=retrieved_at,
                        source_sha256="a" * 64,
                        
                        
                    ),
                ),
            )
            repo.append_validated((record,))

    def test_backtest_run_success_plain_output(self) -> None:
        """Backtest run succeeds with plain output."""
        self._add_draw_records(10)

        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-10",
            training_window=7,
            seed=42,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_run(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Backtest:", output)
        self.assertIn("uniform_random", output)

    def test_backtest_run_success_json_output(self) -> None:
        """Backtest run succeeds with JSON output."""
        self._add_draw_records(10)

        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-10",
            training_window=7,
            seed=42,
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_run(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["status"], "success")
        self.assertIn("run_id", data)

    def test_backtest_run_empty_repository_error(self) -> None:
        """Backtest run returns error with empty repository."""
        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-10",
            training_window=7,
            seed=42,
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()) as fake_err:
            result = _run_backtest_run(args)
            error = fake_err.getvalue()

        self.assertEqual(result, 2)
        self.assertIn("ERROR", error)
        self.assertIn("vazia", error)

    def test_backtest_run_invalid_config_error(self) -> None:
        """Backtest run returns error with invalid config."""
        self._add_draw_records(10)

        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-10",
            end_date="2025-01-01",  # Invalid: end before start
            training_window=7,
            seed=42,
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()) as fake_err:
            result = _run_backtest_run(args)
            error = fake_err.getvalue()

        self.assertEqual(result, 2)
        self.assertIn("ERROR", error)

    def test_backtest_run_with_metrics_output(self) -> None:
        """Backtest run outputs metrics in plain mode."""
        self._add_draw_records(10)

        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-10",
            training_window=7,
            seed=42,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_run(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Período:", output)
        self.assertIn("→", output)
        self.assertIn("Salvo em:", output)

    def test_backtest_run_creates_artifact(self) -> None:
        """Backtest run creates artifact file."""
        self._add_draw_records(10)

        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-10",
            training_window=7,
            seed=42,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()):
            result = _run_backtest_run(args)

        self.assertEqual(result, 0)
        # Verify some run directory was created
        runs = list(self.artifacts_dir.glob("*"))
        self.assertGreater(len(runs), 0)

    def test_backtest_run_json_contains_file_path(self) -> None:
        """Backtest run JSON output contains file path."""
        self._add_draw_records(10)

        args = argparse.Namespace(
            data_dir=self.data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-10",
            training_window=7,
            seed=42,
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_run(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertIn("file", data)
        self.assertIn("sha256", data)

    def test_backtest_run_different_strategies(self) -> None:
        """Backtest run works with different strategies."""
        self._add_draw_records(10)

        for strategy in ["uniform_random", "frequency_only"]:
            with self.subTest(strategy=strategy):
                args = argparse.Namespace(
                    data_dir=self.data_dir,
                    artifacts_dir=self.artifacts_dir,
                    strategy=strategy,
                    start_date="2025-01-01",
                    end_date="2025-01-10",
                    training_window=7,
                    seed=42,
                    as_json=False,
                )

                with patch("sys.stdout", new=StringIO()):
                    result = _run_backtest_run(args)

                self.assertEqual(result, 0)
