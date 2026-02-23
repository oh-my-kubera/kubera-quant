"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def quant_dir() -> Path:
    """Return the .quant data directory, creating it if needed."""
    d = Path(".quant")
    d.mkdir(exist_ok=True)
    return d


def cache_dir() -> Path:
    """Return the .quant/cache directory for Parquet files."""
    d = quant_dir() / "cache"
    d.mkdir(exist_ok=True)
    return d


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="QUANT_",
        env_file=".quant/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bigquery_project: str = ""
    bigquery_dataset: str = "kubera_market"
    default_start_date: str = "2020-01-01"
    backtest_init_cash: float = 10_000_000
    backtest_fees: float = 0.0015
    backtest_slippage: float = 0.001
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
