"""Tests for CLI backtest branch coverage."""

import argparse
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli_backtest import _run_backtest_run, _run_backtest_show


class TestCliBacktestBranches(TestCase):
    """Test branch coverage in CLI backtest handlers."""

    def setUp(self) -> None:
        """Set up test directories."""
        self.tmpdir = TemporaryDirectory()
        self.artifacts_dir = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def test_show_run_without_config_plain(self) -> None:
        """Show run with empty config dict outputs correct format."""
        # Create run with empty config (falsy dict)
        run_dir = self.artifacts_dir / "config_empty"
        run_dir.mkdir()
        with open(run_dir / "config.json", "w") as f:
            json.dump({}, f)  # Empty config dict
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"average_hits": 2.5}, f)
        with open(run_dir / "manifest.json", "w") as f:
            json.dump({
                "run_id": "config_empty",
                "status": "success",
                "files": {},
            }, f)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="config_empty",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_show(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Run ID:", output)

    def test_show_run_without_config_json(self) -> None:
        """Show run with empty config dict outputs JSON format."""
        # Create run with empty config (falsy dict)
        run_dir = self.artifacts_dir / "config_empty"
        run_dir.mkdir()
        with open(run_dir / "config.json", "w") as f:
            json.dump({}, f)  # Empty config dict
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"average_hits": 2.5}, f)
        with open(run_dir / "manifest.json", "w") as f:
            json.dump({
                "run_id": "config_empty",
                "status": "success",
                "files": {},
            }, f)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="config_empty",
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_show(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["config"], {})

    def test_show_run_with_metrics_but_no_average_hits_plain(self) -> None:
        """Show run with metrics missing average_hits field."""
        # Create run with metrics but no average_hits
        run_dir = self.artifacts_dir / "no_avg_hits"
        run_dir.mkdir()
        with open(run_dir / "config.json", "w") as f:
            json.dump({"strategy_name": "test"}, f)
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"hit_distribution": {0: 100}}, f)
        with open(run_dir / "manifest.json", "w") as f:
            json.dump({
                "run_id": "no_avg_hits",
                "status": "success",
                "files": {},
            }, f)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="no_avg_hits",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_show(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Run ID:", output)
        self.assertIn("Estratégia:", output)

    def test_backtest_run_with_invalid_strategy_error(self) -> None:
        """Backtest run fails with invalid strategy name."""
        from datetime import UTC, date, datetime

        from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
        from bonoai.domain.models import Draw
        from bonoai.infrastructure.csv_repository import CsvDrawRepository

        data_dir = Path(self.tmpdir.name) / "data"
        data_dir.mkdir()
        (data_dir / "processed").mkdir()

        # Add one draw record
        repo = CsvDrawRepository(data_dir / "processed" / "draws.csv")
        retrieved_at = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
        record = CanonicalDrawRecord(
            draw=Draw(
                contest_id="test:2025-01-01",
                held_on=date(2025, 1, 1),
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

        args = argparse.Namespace(
            data_dir=data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="nonexistent_strategy",  # Invalid strategy
            start_date="2025-01-01",
            end_date="2025-01-01",
            training_window=1,
            seed=42,
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()) as fake_err:
            result = _run_backtest_run(args)
            error = fake_err.getvalue()

        self.assertEqual(result, 2)
        self.assertIn("ERROR", error)

    def test_backtest_run_success_json_includes_sha(self) -> None:
        """Backtest run JSON output includes SHA-256."""
        from datetime import UTC, date, datetime

        from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
        from bonoai.domain.models import Draw
        from bonoai.infrastructure.csv_repository import CsvDrawRepository

        data_dir = Path(self.tmpdir.name) / "data"
        data_dir.mkdir()
        (data_dir / "processed").mkdir()

        repo = CsvDrawRepository(data_dir / "processed" / "draws.csv")
        retrieved_at = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
        for day in range(1, 6):
            record = CanonicalDrawRecord(
                draw=Draw(
                    contest_id=f"test:2025-01-{day:02d}",
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

        args = argparse.Namespace(
            data_dir=data_dir,
            artifacts_dir=self.artifacts_dir,
            strategy="uniform_random",
            start_date="2025-01-01",
            end_date="2025-01-05",
            training_window=2,
            seed=42,
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_run(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["status"], "success")
        self.assertIn("sha256", data)
        self.assertIsNotNone(data["sha256"])
