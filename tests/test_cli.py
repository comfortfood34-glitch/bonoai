import argparse
import contextlib
import io
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli import _decimal, main
from bonoai.domain.data import CanonicalDrawRecord, SourceProvenance
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CsvDrawRepository
from bonoai.infrastructure.selae_rss import SelaeRssSource

FIXTURE = Path(__file__).parent / "fixtures" / "selae_bonoloto.xml"
RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


class CliTests(TestCase):
    def test_info(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["info"])

        self.assertEqual(status, 0)
        self.assertIn("Bonoloto", output.getvalue())

    def test_generate_json(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["generate", "--seed", "42", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["ticket_count"], 10)
        self.assertEqual(payload["cost_eur"], "5.00")

    def test_generate_table(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["generate", "--seed", "42"])

        self.assertEqual(status, 0)
        self.assertIn("10 apostas", output.getvalue())
        self.assertIn("01:", output.getvalue())

    def test_decimal_parser(self) -> None:
        self.assertEqual(_decimal("5.00"), Decimal("5.00"))

    def test_decimal_parser_rejects_invalid_value(self) -> None:
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "invalid decimal"):
            _decimal("not-a-number")

    def test_generate_reports_domain_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["generate", "--budget", "5.10"])

    def test_data_status_reports_empty_repository_as_json(self) -> None:
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-status", "--data-dir", directory, "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["draw_count"], 0)
        self.assertIsNone(payload["first_draw"])

    def test_data_status_table_after_update(self) -> None:
        source = SelaeRssSource(
            transport=lambda _url, _timeout: FIXTURE.read_bytes(),
            clock=lambda: RETRIEVED_AT,
        )
        with TemporaryDirectory() as directory:
            with (
                patch("bonoai.cli.SelaeRssSource", return_value=source),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                main(["data-update", "--data-dir", directory])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-status", "--data-dir", directory])

        self.assertEqual(status, 0)
        self.assertIn("Concursos: 2", output.getvalue())
        self.assertIn("2026-07-27", output.getvalue())

    def test_data_update_json(self) -> None:
        source = SelaeRssSource(
            transport=lambda _url, _timeout: FIXTURE.read_bytes(),
            clock=lambda: RETRIEVED_AT,
        )
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with (
                patch("bonoai.cli.SelaeRssSource", return_value=source),
                contextlib.redirect_stdout(output),
            ):
                status = main(["data-update", "--data-dir", directory, "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["inserted"], 2)
        self.assertEqual(payload["latest_draw"], "2026-07-28")


    def test_data_audit_with_findings_text(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            repo = CsvDrawRepository(data_dir / "processed" / "draws.csv")
            record = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="test:2026-07-27",
                    held_on=date(2026, 7, 27),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(
                    SourceProvenance(
                        source_name="test",
                        source_url="https://example.test",
                        retrieved_at_utc=RETRIEVED_AT,
                        source_sha256="a" * 64,
                        source_type="official",
                        schema_version=2,
                    ),
                ),
            )
            repo.append_validated((record,))

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-audit", "--data-dir", str(data_dir)])

        self.assertEqual(status, 0)
        self.assertIn("Base canônica:", output.getvalue())

    def test_data_audit_with_findings_json(self) -> None:
        with TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            data_dir.mkdir()
            (data_dir / "processed").mkdir()

            repo = CsvDrawRepository(data_dir / "processed" / "draws.csv")
            record = CanonicalDrawRecord(
                draw=Draw(
                    contest_id="test:2026-07-27",
                    held_on=date(2026, 7, 27),
                    numbers=(1, 2, 3, 4, 5, 6),
                    complementary=7,
                    reintegro=8,
                ),
                provenances=(
                    SourceProvenance(
                        source_name="test",
                        source_url="https://example.test",
                        retrieved_at_utc=RETRIEVED_AT,
                        source_sha256="a" * 64,
                        source_type="official",
                        schema_version=2,
                    ),
                ),
            )
            repo.append_validated((record,))

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["data-audit", "--data-dir", str(data_dir), "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["merged_count"], 1)
        self.assertIsInstance(payload["findings"], list)
