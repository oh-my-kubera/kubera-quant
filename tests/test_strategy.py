"""Tests for strategy framework."""

import pandas as pd

from quant.core.strategy import STRATEGIES, get_strategy


def _sample_df(n=30):
    """Generate sample OHLCV with a clear uptrend then downtrend."""
    prices = list(range(100, 100 + n // 2)) + list(range(100 + n // 2, 100, -1))
    prices = prices[:n]
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": prices,
        "high": [p + 2 for p in prices],
        "low": [p - 2 for p in prices],
        "close": prices,
        "volume": [1000] * n,
    })


def test_strategies_registered():
    assert "sma_cross" in STRATEGIES
    assert "momentum" in STRATEGIES


def test_get_strategy():
    s = get_strategy("sma_cross")
    assert s is not None
    assert s.name == "sma_cross"


def test_get_strategy_missing():
    assert get_strategy("nonexistent") is None


def test_sma_cross_signal_shape():
    df = _sample_df(30)
    s = get_strategy("sma_cross")
    signal = s.generate_signal(df, short=3, long=10)

    assert len(signal) == len(df)
    assert set(signal.dropna().unique()).issubset({-1.0, 0.0, 1.0})


def test_sma_cross_custom_params():
    df = _sample_df(50)
    s = get_strategy("sma_cross")
    signal = s.generate_signal(df, short=5, long=20)
    assert len(signal) == 50


def test_momentum_signal_shape():
    df = _sample_df(30)
    s = get_strategy("momentum")
    signal = s.generate_signal(df, lookback=5)

    assert len(signal) == len(df)
    assert set(signal.dropna().unique()).issubset({-1.0, 0.0, 1.0})


def test_momentum_uptrend():
    """In a clear uptrend, momentum should produce buy signals."""
    prices = list(range(100, 130))
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=30).strftime("%Y-%m-%d"),
        "open": prices,
        "high": [p + 1 for p in prices],
        "low": [p - 1 for p in prices],
        "close": prices,
        "volume": [1000] * 30,
    })
    s = get_strategy("momentum")
    signal = s.generate_signal(df, lookback=5)

    # After lookback period, all should be buy signals
    assert (signal.iloc[5:] == 1.0).all()


def test_strategy_description():
    for name, strategy in STRATEGIES.items():
        assert hasattr(strategy, "description")
        assert len(strategy.description) > 0
