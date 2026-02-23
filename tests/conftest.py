"""Shared test fixtures."""

import pytest


@pytest.fixture()
def quant_dir(tmp_path, monkeypatch):
    """Set up a temporary .quant directory."""
    monkeypatch.chdir(tmp_path)
    d = tmp_path / ".quant"
    d.mkdir()
    (d / "cache").mkdir()
    return d
