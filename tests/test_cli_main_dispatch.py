"""Tests for CLI main function command dispatch."""

import contextlib
import io
from unittest import TestCase

from bonoai.cli import main


class TestCliMainDispatch(TestCase):
    """Test CLI main command dispatch."""

    def test_main_info_command(self) -> None:
        """Main function dispatches to info command."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["info"])

        self.assertEqual(result, 0)
        self.assertIn("Bonoloto", output.getvalue())
