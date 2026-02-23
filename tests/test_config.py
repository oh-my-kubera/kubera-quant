"""Tests for config module."""

from quant.core.config import Settings, quant_dir, cache_dir


def test_settings_defaults():
    settings = Settings()
    assert settings.bigquery_project == ""
    assert settings.bigquery_dataset == "kubera_market"
    assert settings.default_start_date == "2020-01-01"
    assert settings.backtest_init_cash == 10_000_000
    assert settings.backtest_fees == 0.0015
    assert settings.backtest_slippage == 0.001
    assert settings.debug is False


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("QUANT_BIGQUERY_PROJECT", "my-project")
    monkeypatch.setenv("QUANT_DEBUG", "true")
    settings = Settings()
    assert settings.bigquery_project == "my-project"
    assert settings.debug is True


def test_quant_dir_creates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = quant_dir()
    assert d.exists()
    assert d.name == ".quant"


def test_cache_dir_creates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = cache_dir()
    assert d.exists()
    assert d.parent.name == ".quant"
