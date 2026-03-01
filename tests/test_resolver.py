"""Tests for data resolver."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quant.core.data import OHLCV_COLUMNS
from quant.core.data.cache import ParquetCache
from quant.core.data.resolver import collect_to_local, get_source


def _sample_df(dates):
    return pd.DataFrame({
        "date": dates,
        "open": [100.0] * len(dates),
        "high": [105.0] * len(dates),
        "low": [95.0] * len(dates),
        "close": [102.0] * len(dates),
        "volume": [1000] * len(dates),
    })


def test_get_source_unknown():
    with pytest.raises(ValueError, match="Unknown market"):
        get_source("invalid")


@patch("quant.core.data.resolver.get_source")
def test_collect_to_local_new_data(mock_get_source, tmp_path):
    mock_source = MagicMock()
    mock_source.fetch_ohlcv.return_value = _sample_df(
        ["2024-01-02", "2024-01-03", "2024-01-04"]
    )
    mock_get_source.return_value = mock_source

    cache = ParquetCache(base_dir=tmp_path)
    df = collect_to_local("krx", "005930", "2024-01-01", "2024-01-10", cache)

    assert len(df) == 3
    assert list(df.columns) == OHLCV_COLUMNS
    mock_source.fetch_ohlcv.assert_called_once_with("005930", "2024-01-01", "2024-01-10")


@patch("quant.core.data.resolver.get_source")
def test_collect_to_local_saves_to_cache(mock_get_source, tmp_path):
    mock_source = MagicMock()
    mock_source.fetch_ohlcv.return_value = _sample_df(["2024-01-02", "2024-01-03"])
    mock_get_source.return_value = mock_source

    cache = ParquetCache(base_dir=tmp_path)
    collect_to_local("krx", "005930", "2024-01-01", "2024-01-10", cache)

    # Data should be persisted in cache
    cached = cache.read("krx", "005930")
    assert len(cached) == 2


@patch("quant.core.data.resolver.get_source")
def test_collect_to_local_incremental(mock_get_source, tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    cache.write("krx", "005930", _sample_df(["2024-01-02", "2024-01-03"]))

    mock_source = MagicMock()
    mock_source.fetch_ohlcv.return_value = _sample_df(["2024-01-04", "2024-01-05"])
    mock_get_source.return_value = mock_source

    df = collect_to_local("krx", "005930", "2024-01-01", "2024-01-05", cache)

    assert len(df) == 4  # 2 old + 2 new
    # Should only fetch from day after last cached date
    mock_source.fetch_ohlcv.assert_called_once_with("005930", "2024-01-04", "2024-01-05")


@patch("quant.core.data.resolver.get_source")
def test_collect_to_local_already_up_to_date(mock_get_source, tmp_path):
    cache = ParquetCache(base_dir=tmp_path)
    cache.write("krx", "005930", _sample_df(["2024-01-02", "2024-01-03", "2024-01-04"]))

    df = collect_to_local("krx", "005930", "2024-01-01", "2024-01-04", cache)

    assert len(df) == 3
    # Should NOT call the API at all
    mock_get_source.assert_not_called()


@patch("quant.core.data.resolver.get_source")
def test_collect_to_local_empty_api_response(mock_get_source, tmp_path):
    mock_source = MagicMock()
    mock_source.fetch_ohlcv.return_value = pd.DataFrame(columns=OHLCV_COLUMNS)
    mock_get_source.return_value = mock_source

    cache = ParquetCache(base_dir=tmp_path)
    df = collect_to_local("krx", "UNKNOWN", "2024-01-01", "2024-01-10", cache)

    assert df.empty


@patch("quant.core.data.resolver.get_source")
def test_collect_to_local_date_filter(mock_get_source, tmp_path):
    mock_source = MagicMock()
    mock_source.fetch_ohlcv.return_value = _sample_df(
        ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    )
    mock_get_source.return_value = mock_source

    cache = ParquetCache(base_dir=tmp_path)
    df = collect_to_local("krx", "005930", "2024-01-03", "2024-01-04", cache)

    # Should return only the requested range
    assert len(df) == 2
    assert df["date"].iloc[0] == "2024-01-03"
    assert df["date"].iloc[1] == "2024-01-04"
