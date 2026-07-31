"""Tests for CLI backtest JSON output formatting."""

import argparse
import hashlib
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bonoai.cli_backtest import (
    _run_backtest_compare,
    _run_backtest_list,
    _run_backtest_show,
    _run_backtest_verify,
)


class TestCliBacktestJsonOutput(TestCase):
    """Test CLI handler JSON output and formatting."""

    def setUp(self) -> None:
        """Set up test artifacts."""
        self.tmpdir = TemporaryDirectory()
        self.artifacts_dir = Path(self.tmpdir.name)
        self._create_sample_run("run_001", 2.5)

    def tearDown(self) -> None:
        """Clean up."""
        self.tmpdir.cleanup()

    def _create_sample_run(self, run_id: str, avg_hits: float) -> None:
        """Create a sample run with valid hashes."""
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True)

        config = {"strategy_name": "uniform_random", "start_date": "2025-01-01"}
        config_bytes = json.dumps(config, sort_keys=True).encode("utf-8")
        config_hash = hashlib.sha256(config_bytes).hexdigest()
        with open(run_dir / "config.json", "wb") as f:
            f.write(config_bytes)

        metrics = {"average_hits": avg_hits, "hit_distribution": {0: 100}}
        metrics_bytes = json.dumps(metrics, sort_keys=True).encode("utf-8")
        metrics_hash = hashlib.sha256(metrics_bytes).hexdigest()
        with open(run_dir / "metrics.json", "wb") as f:
            f.write(metrics_bytes)

        manifest = {
            "run_id": run_id,
            "status": "success",
            "files": {"config.json": config_hash, "metrics.json": metrics_hash},
        }
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

    def test_list_runs_json_output(self) -> None:
        """Test list runs outputs valid JSON."""
        self._create_sample_run("run_002", 1.5)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_list(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["runs"]), 2)

    def test_list_runs_plain_output(self) -> None:
        """Test list runs outputs plain text."""
        self._create_sample_run("run_002", 1.5)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_list(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Execuções: 2", output)
        self.assertIn("run_001", output)
        self.assertIn("run_002", output)

    def test_show_run_json_output(self) -> None:
        """Test show run outputs valid JSON."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="run_001",
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_show(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["run_id"], "run_001")
        self.assertIsNotNone(data["config"])
        self.assertIsNotNone(data["metrics"])

    def test_show_run_plain_output(self) -> None:
        """Test show run outputs plain text."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="run_001",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_show(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Run ID: run_001", output)
        self.assertIn("uniform_random", output)

    def test_show_run_missing_error(self) -> None:
        """Test show run with missing run returns error."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="nonexistent",
            as_json=False,
        )

        with patch("sys.stderr", new=StringIO()):
            result = _run_backtest_show(args)

        self.assertEqual(result, 2)

    def test_compare_runs_json_output(self) -> None:
        """Test compare runs outputs valid JSON."""
        self._create_sample_run("run_002", 1.0)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id_1="run_001",
            run_id_2="run_002",
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_compare(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["run_1"], "run_001")
        self.assertEqual(data["run_2"], "run_002")
        self.assertAlmostEqual(abs(data["avg_diff"]), 1.5, places=1)

    def test_compare_runs_plain_output(self) -> None:
        """Test compare runs outputs plain text."""
        self._create_sample_run("run_002", 1.0)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id_1="run_001",
            run_id_2="run_002",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_compare(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Comparação", output)
        self.assertIn("Diferença média", output)

    def test_verify_run_valid_json_output(self) -> None:
        """Test verify valid run outputs JSON."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="run_001",
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_verify(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        data = json.loads(output)
        self.assertEqual(data["run_id"], "run_001")
        self.assertTrue(data["valid"])
        self.assertEqual(data["files_checked"], 2)

    def test_verify_run_valid_plain_output(self) -> None:
        """Test verify valid run outputs plain text."""
        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="run_001",
            as_json=False,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_verify(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 0)
        self.assertIn("Verificação", output)
        self.assertIn("✓ válido", output)

    def test_verify_run_invalid_json_output(self) -> None:
        """Test verify invalid run returns exit code 1."""
        # Create run with bad hash
        run_dir = self.artifacts_dir / "bad_run"
        run_dir.mkdir(parents=True)
        with open(run_dir / "config.json", "w") as f:
            json.dump({"strategy_name": "test"}, f)
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"average_hits": 1.0}, f)
        with open(run_dir / "manifest.json", "w") as f:
            json.dump({
                "run_id": "bad_run",
                "status": "success",
                "files": {"config.json": "0" * 64, "metrics.json": "1" * 64},
            }, f)

        args = argparse.Namespace(
            artifacts_dir=self.artifacts_dir,
            run_id="bad_run",
            as_json=True,
        )

        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = _run_backtest_verify(args)
            output = fake_out.getvalue()

        self.assertEqual(result, 1)
        data = json.loads(output)
        self.assertFalse(data["valid"])
