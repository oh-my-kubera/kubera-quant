"""Tests for CLI."""

import subprocess
import sys

from quant.cli import main


def test_help_exit_code():
    """CLI --help should exit with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "quant.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "kubera-quant" in result.stdout


def test_version_exit_code():
    """CLI --version should print version and exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "quant.cli", "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "kubera-quant" in result.stdout


def test_strategy_list():
    """CLI strategy should list registered strategies."""
    result = subprocess.run(
        [sys.executable, "-m", "quant.cli", "strategy"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "sma_cross" in result.stdout
    assert "momentum" in result.stdout


def test_backtest_missing_args():
    """CLI backtest without required args should fail."""
    result = subprocess.run(
        [sys.executable, "-m", "quant.cli", "backtest"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_unknown_subcommand():
    """CLI with unknown subcommand should exit with error."""
    result = subprocess.run(
        [sys.executable, "-m", "quant.cli", "nonexistent"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
