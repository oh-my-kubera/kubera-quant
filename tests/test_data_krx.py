"""Tests for KRX data source."""

from unittest.mock import patch

import pandas as pd

from quant.core.data import OHLCV_COLUMNS
from quant.core.data.krx import KrxDataSource


def _mock_ohlcv():
    """Sample pykrx response DataFrame."""
    return pd.DataFrame({
        "날짜": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        "시가": [71000, 72000, 71500],
        "고가": [72000, 73000, 72500],
        "저가": [70500, 71000, 70000],
        "종가": [71500, 72500, 70500],
        "거래량": [1000000, 1200000, 900000],
    }).set_index("날짜")


@patch("quant.core.data.krx.pykrx_stock.get_market_ohlcv_by_date")
def test_fetch_ohlcv(mock_get):
    mock_get.return_value = _mock_ohlcv()
    source = KrxDataSource()
    df = source.fetch_ohlcv("005930", "2024-01-02", "2024-01-04")

    assert list(df.columns) == OHLCV_COLUMNS
    assert len(df) == 3
    assert df.iloc[0]["date"] == "2024-01-02"
    assert df.iloc[0]["close"] == 71500
    mock_get.assert_called_once_with("20240102", "20240104", "005930")


@patch("quant.core.data.krx.pykrx_stock.get_market_ohlcv_by_date")
def test_fetch_ohlcv_empty(mock_get):
    mock_get.return_value = pd.DataFrame()
    source = KrxDataSource()
    df = source.fetch_ohlcv("999999", "2024-01-02", "2024-01-04")

    assert list(df.columns) == OHLCV_COLUMNS
    assert df.empty


@patch("quant.core.data.krx.pykrx_stock.get_market_ohlcv_by_date")
def test_fetch_ohlcv_sorted(mock_get):
    # Return in reverse order
    reversed_df = _mock_ohlcv().iloc[::-1]
    mock_get.return_value = reversed_df
    source = KrxDataSource()
    df = source.fetch_ohlcv("005930", "2024-01-02", "2024-01-04")

    dates = df["date"].tolist()
    assert dates == sorted(dates)
