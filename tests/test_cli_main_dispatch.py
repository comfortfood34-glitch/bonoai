"""Tests for CLI main function command dispatch."""

import contextlib
import io
import json
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.cli import main
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository


class TestCliMainDispatch(TestCase):
    """Test CLI main command dispatch."""

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

    def _setup_draws(self, count: int = 5) -> None:
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
                provenances=(
                    SourceProvenance(
                        source_name="test",
                        source_url="https://test.local",
                        retrieved_at_utc=retrieved_at,
                        source_sha256="a" * 64,
                        source_type="official",
                        schema_version=2,
                    ),
                ),
            )
            repo.append_validated((record,))

    def test_main_backtest_run_command(self) -> None:
        """Main function dispatches to backtest run command."""
        self._setup_draws(5)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "backtest", "run",
                "--data-dir", str(self.data_dir),
                "--artifacts-dir", str(self.artifacts_dir),
                "--strategy", "uniform_random",
                "--start-date", "2025-01-01",
                "--end-date", "2025-01-05",
                "--training-window", "2",
            ])

        self.assertEqual(result, 0)
        self.assertIn("Backtest:", output.getvalue())

    def test_main_backtest_list_command(self) -> None:
        """Main function dispatches to backtest list command."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "backtest", "list",
                "--artifacts-dir", str(self.artifacts_dir),
            ])

        self.assertEqual(result, 0)
        self.assertIn("Execuções:", output.getvalue())

    def test_main_backtest_verify_command(self) -> None:
        """Main function dispatches to backtest verify command."""
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            result = main([
                "backtest", "verify",
                "--artifacts-dir", str(self.artifacts_dir),
                "nonexistent",
            ])

        self.assertEqual(result, 2)
        self.assertIn("ERROR", error.getvalue())

    def test_main_data_audit_command(self) -> None:
        """Main function dispatches to data audit command."""
        # Create minimal canonical.csv
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "data-audit",
                "--data-dir", str(self.data_dir),
            ])

        self.assertEqual(result, 0)
        self.assertIn("Base canônica", output.getvalue())

    def test_main_data_audit_json_output(self) -> None:
        """Main function data-audit with JSON output."""
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "data-audit",
                "--data-dir", str(self.data_dir),
                "--json",
            ])

        self.assertEqual(result, 0)
        data = json.loads(output.getvalue())
        self.assertIsNotNone(data)

    def test_main_info_command(self) -> None:
        """Main function dispatches to info command."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["info"])

        self.assertEqual(result, 0)
        self.assertIn("Bonoloto", output.getvalue())

    def test_main_data_audit_with_findings(self) -> None:
        """Main function data-audit outputs findings."""
        # Create canonical with date gap to trigger findings
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            # Date gap: 1st then 15th (14 day gap)
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")
            f.write("2,2025-01-15,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-15T00:00:00+00:00,"
                   "b" * 64 + ",official,2\n")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "data-audit",
                "--data-dir", str(self.data_dir),
            ])

        self.assertEqual(result, 0)
        output_str = output.getvalue()
        self.assertIn("Base canônica", output_str)
