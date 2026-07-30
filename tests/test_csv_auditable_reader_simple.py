"""Simple tests for auditable CSV reader."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.infrastructure.csv_auditable_reader import read_csv_auditable


class CsvAuditableReaderSimpleTests(TestCase):
    """Basic CSV reader functionality tests."""

    def test_missing_csv_file_generates_error(self) -> None:
        """Missing CSV file generates error."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nonexistent.csv"

            result = read_csv_auditable(path)

            self.assertEqual(len(result.records), 0)
            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.errors[0].code, "invalid_record")

    def test_header_only_csv(self) -> None:
        """CSV with only header produces no records and no errors."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "header.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertEqual(len(result.records), 0)
            self.assertEqual(len(result.errors), 0)

    def test_result_has_tuples(self) -> None:
        """Result contains records and errors as tuples."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "test.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertIsInstance(result.records, tuple)
            self.assertIsInstance(result.errors, tuple)

    def test_csv_with_missing_field_generates_error(self) -> None:
        """CSV row with empty required field generates error."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing_field.csv"
            # Create a minimal valid CSV with one field missing (contest_id)
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                ",2026-01-01,1;2;3;4;5;6,7,8,src,https://ex.com,a,official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.errors[0].code, "invalid_record")
            self.assertIn("contest_id", result.errors[0].message.lower())


    def test_csv_with_valid_data_creates_record(self) -> None:
        """CSV with valid row creates a record."""
        sha = "a" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "valid.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test2026,2026-01-01,1;2;3;4;5;6,7,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            msg = f"Errors: {[e.message for e in result.errors]}"
            self.assertGreater(len(result.records), 0, msg)
            self.assertEqual(result.records[0].draw.contest_id, "test2026")

    def test_csv_with_invalid_numbers_generates_error(self) -> None:
        """CSV with invalid numbers format generates error."""
        sha = "b" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "bad_numbers.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test2026,2026-01-01,invalid,7,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.errors[0].code, "invalid_record")

    def test_csv_missing_source_url_generates_error(self) -> None:
        """CSV with missing source_url generates error."""
        sha = "c" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing_url.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test2026,2026-01-01,1;2;3;4;5;6,7,8,src,,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.errors[0].code, "invalid_record")

    def test_csv_two_rows_mixed_valid_invalid(self) -> None:
        """CSV with one valid and one invalid row."""
        sha1 = "d" * 64
        sha2 = "e" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "mixed.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test2026,2026-01-01,1;2;3;4;5;6,7,8,src,https://ex.com,{sha1},official\n"
                f"test2027,2026-01-02,1;2;3;4;5;6,,8,src,https://ex.com,{sha2},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertEqual(len(result.records), 1)
            self.assertEqual(len(result.errors), 1)
            self.assertEqual(result.records[0].draw.contest_id, "test2026")

    def test_csv_missing_complementary_error(self) -> None:
        """CSV with missing complementary generates error."""
        sha = "f" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "no_complementary.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test2026,2026-01-01,1;2;3;4;5;6,,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)

    def test_csv_missing_reintegro_error(self) -> None:
        """CSV with missing reintegro generates error."""
        sha = "f" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "no_reintegro.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test2026,2026-01-01,1;2;3;4;5;6,7,,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)

    def test_three_rows_two_valid_one_invalid(self) -> None:
        """CSV with three rows - valid, invalid, valid."""
        sha1, sha2, sha3 = "a" * 64, "b" * 64, "c" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "three.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"id1,2026-01-01,1;2;3;4;5;6,7,8,src,https://ex.com,{sha1},official\n"
                f"id2,2026-01-02,1;2;3;4;5;6,,8,src,https://ex.com,{sha2},official\n"
                f"id3,2026-01-03,1;2;3;4;5;6,7,8,src,https://ex.com,{sha3},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertEqual(len(result.records), 2)
            self.assertEqual(len(result.errors), 1)
            self.assertEqual(result.records[0].draw.contest_id, "id1")
            self.assertEqual(result.records[1].draw.contest_id, "id3")

    def test_invalid_date_format_error(self) -> None:
        """CSV with invalid date format generates error."""
        sha = "1" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "bad_date.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test,bad-date,1;2;3;4;5;6,7,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)

    def test_invalid_numbers_format_int_error(self) -> None:
        """CSV with non-integer numbers generates error."""
        sha = "2" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "bad_nums.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test,2026-01-01,a;b;c;d;e;f,7,8,src,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)

    def test_missing_source_name_error_code(self) -> None:
        """CSV with missing source_name generates invalid_provenance error."""
        sha = "3" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "no_name.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"test,2026-01-01,1;2;3;4;5;6,7,8,,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.errors[0].code, "invalid_provenance")

    def test_valid_record_with_numbers(self) -> None:
        """Valid record is created with correct numbers tuple."""
        sha = "4" * 64
        with TemporaryDirectory() as directory:
            path = Path(directory) / "valid_num.csv"
            path.write_text(
                "contest_id,held_on,numbers,complementary,reintegro,"
                "source_name,source_url,source_sha256,source_type\n"
                f"nums_test,2026-01-01,1;2;3;4;5;6,9,8,n,https://ex.com,{sha},official\n",
                encoding="utf-8",
            )

            result = read_csv_auditable(path)

            self.assertEqual(len(result.records), 1)
            self.assertEqual(result.records[0].draw.numbers, (1, 2, 3, 4, 5, 6))
