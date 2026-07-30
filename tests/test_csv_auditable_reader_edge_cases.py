"""Edge case tests for auditable CSV reader."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.infrastructure.csv_auditable_reader import read_csv_auditable


class CsvAuditableReaderEdgeCasesTests(TestCase):
    """Edge case and boundary condition tests for CSV reader."""

    def test_missing_held_on_generates_error(self) -> None:
        """CSV with missing held_on generates error."""
        sha = "5" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "no_held_on.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test,, 1;2;3;4;5;6,7,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)

    def test_missing_numbers_generates_error(self) -> None:
        """CSV with missing numbers generates error."""
        sha = "6" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "no_numbers.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test,2026-01-01,,7,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)

    def test_completely_empty_csv_file(self) -> None:
        """Completely empty CSV file (no header) generates error."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "empty.csv"
            path.write_text("", encoding="utf-8")

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.errors[0].code, "invalid_record")
