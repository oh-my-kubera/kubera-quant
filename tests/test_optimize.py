"""Tests for parameter optimization."""

import pandas as pd

from quant.core.backtest.optimize import (
    OptimizeResult,
    format_optimize_report,
    parse_param_ranges,
    run_optimization,
)
from quant.core.strategy import get_strategy


def _trending_df(n=200):
    prices = [100 + i * 0.3 for i in range(n)]
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": prices,
        "high": [p + 2 for p in prices],
        "low": [p - 2 for p in prices],
        "close": prices,
        "volume": [1000] * n,
    })


def test_parse_param_ranges_single():
    result = parse_param_ranges("short=3:7:2")
    assert "short" in result
    assert result["short"] == [3.0, 5.0, 7.0]


def test_parse_param_ranges_multiple():
    result = parse_param_ranges("short=3:5:1,long=10:20:5")
    assert result["short"] == [3.0, 4.0, 5.0]
    assert result["long"] == [10.0, 15.0, 20.0]


def test_parse_param_ranges_fixed():
    result = parse_param_ranges("lookback=20")
    assert result["lookback"] == [20.0]


def test_run_optimization():
    df = _trending_df()
    strategy = get_strategy("sma_cross")
    param_ranges = {"short": [3.0, 5.0], "long": [15.0, 20.0]}

    result = run_optimization(df, strategy, param_ranges, top_n=4)

    assert isinstance(result, OptimizeResult)
    assert result.strategy_name == "sma_cross"
    assert len(result.results) == 4  # 2x2 = 4 combinations
    assert "sharpe_ratio" in result.results.columns
    assert "total_return" in result.results.columns


def test_optimization_sorted_by_metric():
    df = _trending_df()
    strategy = get_strategy("sma_cross")
    param_ranges = {"short": [3.0, 5.0, 7.0], "long": [15.0, 20.0]}

    result = run_optimization(df, strategy, param_ranges, metric="total_return")

    returns = result.results["total_return"].tolist()
    assert returns == sorted(returns, reverse=True)


def test_optimization_best_params():
    df = _trending_df()
    strategy = get_strategy("sma_cross")
    param_ranges = {"short": [3.0, 5.0], "long": [15.0, 20.0]}

    result = run_optimization(df, strategy, param_ranges, metric="sharpe_ratio")

    assert "short" in result.best_params
    assert "long" in result.best_params
    assert result.best_params["short"] in [3.0, 5.0]
    assert result.best_params["long"] in [15.0, 20.0]


def test_format_optimize_report():
    df = _trending_df()
    strategy = get_strategy("sma_cross")
    param_ranges = {"short": [3.0, 5.0], "long": [15.0, 20.0]}

    result = run_optimization(df, strategy, param_ranges)
    report = format_optimize_report(result)

    assert "PARAMETER OPTIMIZATION REPORT" in report
    assert "sma_cross" in report
    assert "Best params" in report
    assert "sharpe_ratio" in report
