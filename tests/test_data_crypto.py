"""Tests for crypto data source."""

from unittest.mock import MagicMock, patch

import pandas as pd

from quant.core.data import OHLCV_COLUMNS
from quant.core.data.crypto import CryptoDataSource


def _mock_candles():
    """Sample ccxt OHLCV response: [timestamp, o, h, l, c, v]"""
    return [
        [1704153600000, 50000000, 51000000, 49000000, 50500000, 100.5],  # 2024-01-02
        [1704240000000, 50500000, 52000000, 50000000, 51500000, 120.3],  # 2024-01-03
        [1704326400000, 51500000, 51500000, 49500000, 50000000, 90.1],   # 2024-01-04
    ]


@patch("quant.core.data.crypto.ccxt")
def test_fetch_ohlcv(mock_ccxt):
    mock_exchange = MagicMock()
    mock_exchange.parse8601.side_effect = lambda x: {
        "2024-01-02T00:00:00Z": 1704153600000,
        "2024-01-04T23:59:59Z": 1704412799000,
    }.get(x, 0)
    mock_exchange.fetch_ohlcv.side_effect = [_mock_candles(), []]
    mock_ccxt.upbit.return_value = mock_exchange

    source = CryptoDataSource("upbit")
    df = source.fetch_ohlcv("BTC-KRW", "2024-01-02", "2024-01-04")

    assert list(df.columns) == OHLCV_COLUMNS
    assert len(df) == 3
    assert df.iloc[0]["date"] == "2024-01-02"


@patch("quant.core.data.crypto.ccxt")
def test_fetch_ohlcv_empty(mock_ccxt):
    mock_exchange = MagicMock()
    mock_exchange.parse8601.return_value = 1704153600000
    mock_exchange.fetch_ohlcv.return_value = []
    mock_ccxt.upbit.return_value = mock_exchange

    source = CryptoDataSource("upbit")
    df = source.fetch_ohlcv("INVALID/KRW", "2024-01-02", "2024-01-04")

    assert df.empty
    assert list(df.columns) == OHLCV_COLUMNS


@patch("quant.core.data.crypto.ccxt")
def test_symbol_normalization(mock_ccxt):
    mock_exchange = MagicMock()
    mock_exchange.parse8601.side_effect = lambda x: {
        "2024-01-02T00:00:00Z": 1704153600000,
        "2024-01-04T23:59:59Z": 1704412799000,
    }.get(x, 0)
    mock_exchange.fetch_ohlcv.return_value = []
    mock_ccxt.upbit.return_value = mock_exchange

    source = CryptoDataSource("upbit")
    source.fetch_ohlcv("BTC-KRW", "2024-01-02", "2024-01-04")

    # Should have been called with "BTC/KRW" (slash, not dash)
    call_args = mock_exchange.fetch_ohlcv.call_args
    assert call_args[0][0] == "BTC/KRW"
