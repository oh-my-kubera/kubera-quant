"""Tests for backtest engine."""

import pandas as pd

from quant.core.backtest.engine import BacktestResult, PortfolioResult, run_backtest, run_portfolio_backtest
from quant.core.backtest.report import format_report, format_portfolio_report


def _trending_df(n=100):
    """Generate uptrending OHLCV data."""
    prices = [100 + i * 0.5 for i in range(n)]
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": prices,
        "high": [p + 2 for p in prices],
        "low": [p - 2 for p in prices],
        "close": prices,
        "volume": [1000] * n,
    })


def _buy_and_hold_signal(n=100):
    """Always-buy signal."""
    signal = pd.Series(0.0, index=range(n))
    signal.iloc[0] = 1.0  # buy on first day
    return signal


def test_run_backtest_returns_result():
    df = _trending_df()
    signal = _buy_and_hold_signal()
    result = run_backtest(df, signal)

    assert isinstance(result, BacktestResult)
    assert result.portfolio is not None


def test_backtest_uptrend_positive_return():
    df = _trending_df()
    signal = _buy_and_hold_signal()
    result = run_backtest(df, signal)

    assert result.total_return > 0


def test_backtest_with_strategy():
    """Integration test: strategy + backtest engine."""
    from quant.core.strategy import get_strategy

    df = _trending_df(200)
    strategy = get_strategy("sma_cross")
    signal = strategy.generate_signal(df, short=5, long=20)
    result = run_backtest(df, signal)

    assert isinstance(result, BacktestResult)
    assert result.total_trades >= 0


def test_backtest_custom_params():
    df = _trending_df()
    signal = _buy_and_hold_signal()
    result = run_backtest(df, signal, init_cash=1_000_000, fees=0.001)

    assert isinstance(result, BacktestResult)


def test_format_report():
    df = _trending_df()
    signal = _buy_and_hold_signal()
    result = run_backtest(df, signal)

    report = format_report(result, strategy_name="test", symbol="005930")
    assert "BACKTEST REPORT" in report
    assert "test" in report
    assert "005930" in report
    assert "Total Return" in report
    assert "Sharpe Ratio" in report


def _trending_df_offset(n=100, base=100, step=0.5):
    """Generate uptrending OHLCV with configurable base/step."""
    prices = [base + i * step for i in range(n)]
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": prices,
        "high": [p + 2 for p in prices],
        "low": [p - 2 for p in prices],
        "close": prices,
        "volume": [1000] * n,
    })


def test_portfolio_backtest_returns_result():
    dfs = {
        "A": _trending_df_offset(100, 100, 0.5),
        "B": _trending_df_offset(100, 200, 1.0),
    }
    signals = {
        "A": _buy_and_hold_signal(100),
        "B": _buy_and_hold_signal(100),
    }
    result = run_portfolio_backtest(dfs, signals)

    assert isinstance(result, PortfolioResult)
    assert result.symbols == ["A", "B"]
    assert "A" in result.per_symbol
    assert "B" in result.per_symbol


def test_portfolio_backtest_positive_return():
    dfs = {
        "A": _trending_df_offset(100, 100, 0.5),
        "B": _trending_df_offset(100, 200, 1.0),
    }
    signals = {
        "A": _buy_and_hold_signal(100),
        "B": _buy_and_hold_signal(100),
    }
    result = run_portfolio_backtest(dfs, signals)

    assert result.total_return > 0
    assert result.per_symbol["A"].total_return > 0
    assert result.per_symbol["B"].total_return > 0


def test_portfolio_backtest_with_strategy():
    from quant.core.strategy import get_strategy

    dfs = {
        "A": _trending_df_offset(200, 100, 0.3),
        "B": _trending_df_offset(200, 150, 0.5),
    }
    strategy = get_strategy("sma_cross")
    signals = {sym: strategy.generate_signal(df, short=5, long=20) for sym, df in dfs.items()}
    result = run_portfolio_backtest(dfs, signals)

    assert isinstance(result, PortfolioResult)
    assert result.total_trades >= 0


def test_format_portfolio_report():
    dfs = {
        "A": _trending_df_offset(100, 100, 0.5),
        "B": _trending_df_offset(100, 200, 1.0),
    }
    signals = {
        "A": _buy_and_hold_signal(100),
        "B": _buy_and_hold_signal(100),
    }
    result = run_portfolio_backtest(dfs, signals)
    report = format_portfolio_report(result, strategy_name="test")

    assert "PORTFOLIO BACKTEST REPORT" in report
    assert "test" in report
    assert "A" in report
    assert "B" in report
    assert "Per Symbol" in report
