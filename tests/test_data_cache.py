"""Tests for Parquet cache."""

import pandas as pd

from quant.core.data import OHLCV_COLUMNS
from quant.core.data.cache import ParquetCache


def _sample_df(dates=None):
    dates = dates or ["2024-01-02", "2024-01-03", "2024-01-04"]
    return pd.DataFrame({
        "date": dates,
        "open": [100.0] * len(dates),
        "high": [105.0] * len(dates),
        "low": [95.0] * len(dates),
        "close": [102.0] * len(dates),
        "volume": [1000] * len(dates),
    })


def test_write_and_read(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    df = _sample_df()
    cache.write("krx", "005930", df)

    result = cache.read("krx", "005930")
    assert list(result.columns) == OHLCV_COLUMNS
    assert len(result) == 3


def test_read_nonexistent(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    result = cache.read("krx", "999999")
    assert result.empty
    assert list(result.columns) == OHLCV_COLUMNS


def test_write_merges_and_deduplicates(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)

    df1 = _sample_df(["2024-01-02", "2024-01-03"])
    cache.write("krx", "005930", df1)

    df2 = _sample_df(["2024-01-03", "2024-01-04"])
    df2["close"] = 999.0  # updated value
    cache.write("krx", "005930", df2)

    result = cache.read("krx", "005930")
    assert len(result) == 3
    # 2024-01-03 should have the newer value
    row = result[result["date"] == "2024-01-03"].iloc[0]
    assert row["close"] == 999.0


def test_read_with_date_filter(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    df = _sample_df(["2024-01-02", "2024-01-03", "2024-01-04"])
    cache.write("krx", "005930", df)

    result = cache.read("krx", "005930", start="2024-01-03")
    assert len(result) == 2

    result = cache.read("krx", "005930", end="2024-01-03")
    assert len(result) == 2

    result = cache.read("krx", "005930", start="2024-01-03", end="2024-01-03")
    assert len(result) == 1


def test_list_symbols(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    cache.write("krx", "005930", _sample_df())
    cache.write("krx", "000660", _sample_df())

    symbols = cache.list_symbols("krx")
    assert symbols == ["000660", "005930"]


def test_list_symbols_empty(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    assert cache.list_symbols("krx") == []


def test_list_markets(tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    cache.write("krx", "005930", _sample_df())
    cache.write("crypto", "BTC-KRW", _sample_df())

    markets = cache.list_markets()
    assert markets == ["crypto", "krx"]
