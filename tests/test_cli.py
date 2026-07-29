import argparse
import contextlib
import io
import json
from decimal import Decimal
from unittest import TestCase

from bonoai.cli import _decimal, main


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
