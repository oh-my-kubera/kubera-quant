"""Tests for US data source."""

from unittest.mock import MagicMock, patch

import pandas as pd

from quant.core.data import OHLCV_COLUMNS
from quant.core.data.us import UsDataSource


def _mock_history():
    """Sample yfinance response DataFrame."""
    return pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        "Open": [185.0, 186.0, 184.5],
        "High": [187.0, 188.0, 186.0],
        "Low": [184.0, 185.0, 183.0],
        "Close": [186.5, 187.5, 183.5],
        "Volume": [50000000, 55000000, 48000000],
    })


@patch("quant.core.data.us.yf")
def test_fetch_ohlcv(mock_yf):
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = _mock_history()
    mock_yf.Ticker.return_value = mock_ticker

    source = UsDataSource()
    df = source.fetch_ohlcv("AAPL", "2024-01-02", "2024-01-04")

    assert list(df.columns) == OHLCV_COLUMNS
    assert len(df) == 3
    assert df.iloc[0]["date"] == "2024-01-02"
    assert df.iloc[0]["close"] == 186.5
    mock_yf.Ticker.assert_called_once_with("AAPL")


@patch("quant.core.data.us.yf")
def test_fetch_ohlcv_end_exclusive(mock_yf):
    """yfinance end date should be +1 day (exclusive)."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = _mock_history()
    mock_yf.Ticker.return_value = mock_ticker

    source = UsDataSource()
    source.fetch_ohlcv("AAPL", "2024-01-02", "2024-01-04")

    call_kwargs = mock_ticker.history.call_args[1]
    assert call_kwargs["end"] == "2024-01-05"


@patch("quant.core.data.us.yf")
def test_fetch_ohlcv_no_end(mock_yf):
    """When end is None, yfinance end should be None."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = _mock_history()
    mock_yf.Ticker.return_value = mock_ticker

    source = UsDataSource()
    source.fetch_ohlcv("AAPL", "2024-01-02")

    call_kwargs = mock_ticker.history.call_args[1]
    assert call_kwargs["end"] is None


@patch("quant.core.data.us.yf")
def test_fetch_ohlcv_empty(mock_yf):
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    mock_yf.Ticker.return_value = mock_ticker

    source = UsDataSource()
    df = source.fetch_ohlcv("INVALID", "2024-01-02", "2024-01-04")

    assert df.empty
    assert list(df.columns) == OHLCV_COLUMNS


@patch("quant.core.data.us.yf")
def test_fetch_ohlcv_sorted(mock_yf):
    """Result should be sorted by date."""
    reversed_df = _mock_history().iloc[::-1].reset_index(drop=True)
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = reversed_df
    mock_yf.Ticker.return_value = mock_ticker

    source = UsDataSource()
    df = source.fetch_ohlcv("AAPL", "2024-01-02", "2024-01-04")

    dates = df["date"].tolist()
    assert dates == sorted(dates)
