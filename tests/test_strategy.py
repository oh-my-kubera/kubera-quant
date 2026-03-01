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
    assert "dca" in STRATEGIES
    assert "rebalance" in STRATEGIES


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


def test_dca_signal_interval():
    """DCA should generate buy signals at regular intervals."""
    df = _sample_df(40)
    s = get_strategy("dca")
    signal = s.generate_signal(df, interval=10)

    assert len(signal) == 40
    # Buy signals at index 0, 10, 20, 30
    assert signal.iloc[0] == 1.0
    assert signal.iloc[10] == 1.0
    assert signal.iloc[20] == 1.0
    assert signal.iloc[30] == 1.0
    # No sell signals — DCA only buys
    assert (signal[signal != 0.0] == 1.0).all()


def test_dca_no_sell():
    """DCA should never produce sell signals."""
    df = _sample_df(50)
    s = get_strategy("dca")
    signal = s.generate_signal(df)
    assert -1.0 not in signal.values


def test_rebalance_signal_shape():
    df = _sample_df(60)
    s = get_strategy("rebalance")
    signal = s.generate_signal(df, interval=10, window=5)

    assert len(signal) == 60
    assert set(signal.unique()).issubset({-1.0, 0.0, 1.0})


def test_rebalance_only_on_interval_days():
    """Rebalance should only generate signals on interval days."""
    df = _sample_df(50)
    s = get_strategy("rebalance")
    signal = s.generate_signal(df, interval=10, window=5)

    # Non-interval days should all be 0.0
    non_interval = [i for i in range(len(df)) if i % 10 != 0]
    assert (signal.iloc[non_interval] == 0.0).all()


def test_strategy_description():
    for name, strategy in STRATEGIES.items():
        assert hasattr(strategy, "description")
        assert len(strategy.description) > 0
