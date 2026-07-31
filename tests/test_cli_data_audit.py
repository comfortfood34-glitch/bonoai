"""Tests for CLI data audit command output."""

import argparse
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli import _run_data_audit


class TestCliDataAudit(TestCase):
    """Test CLI data audit command."""

    def setUp(self) -> None:
        """Set up test directory."""
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name)
        (self.data_dir / "processed").mkdir()
        (self.data_dir / "raw").mkdir()

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def test_data_audit_json_output(self) -> None:
        """Test data audit with JSON output."""
        # Create minimal canonical.csv
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")

        args = argparse.Namespace(
            data_dir=self.data_dir,
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_data_audit(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        # JSON output should be valid
        try:
            data = json.loads(output)
            self.assertIsNotNone(data)
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")

    def test_data_audit_plain_output(self) -> None:
        """Test data audit with plain text output."""
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")

        args = argparse.Namespace(
            data_dir=self.data_dir,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_data_audit(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Base canônica", output)

    def test_data_audit_no_conflicts_plain(self) -> None:
        """Test data audit when no conflicts found."""
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")

        args = argparse.Namespace(
            data_dir=self.data_dir,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_data_audit(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Nenhum conflito", output)

    def test_data_audit_with_findings(self) -> None:
        """Test data audit with findings in output."""
        # Create CSV with data
        canonical = self.data_dir / "processed" / "canonical.csv"
        with open(canonical, "w") as f:
            f.write("contest_id,held_on,numbers,complementary,reintegro,"
                   "source_name,source_url,retrieved_at_utc,source_sha256,"
                   "source_type,schema_version\n")
            # Valid row
            f.write("1,2025-01-01,\"1,2,3,4,5,6\",7,0,"
                   "selae,https://selae.gov.br,2025-01-01T00:00:00+00:00,"
                   "a" * 64 + ",official,2\n")

        args = argparse.Namespace(
            data_dir=self.data_dir,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_data_audit(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        # Should show canonical data loaded
        self.assertIn("Base canônica", output)
