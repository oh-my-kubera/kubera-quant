"""Grid search parameter optimization using vectorbt."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import pandas as pd
import vectorbt as vbt

from quant.core.strategy.base import Strategy


@dataclass
class OptimizeResult:
    """Container for optimization results."""

    strategy_name: str
    param_names: list[str]
    results: pd.DataFrame  # columns: param cols + metric cols
    best_params: dict[str, float]
    best_metric: float
    metric_name: str


def parse_param_ranges(param_str: str) -> dict[str, list[float]]:
    """Parse parameter range string.

    Format: "short=3:10:1,long=10:50:5"
    Returns: {"short": [3,4,5,...,10], "long": [10,15,20,...,50]}
    """
    params = {}
    for pair in param_str.split(","):
        name, range_str = pair.split("=")
        name = name.strip()
        parts = range_str.strip().split(":")
        if len(parts) == 3:
            start, end, step = float(parts[0]), float(parts[1]), float(parts[2])
            values = []
            v = start
            while v <= end + 1e-9:
                values.append(v)
                v += step
            params[name] = values
        elif len(parts) == 1:
            params[name] = [float(parts[0])]
        else:
            raise ValueError(f"Invalid range format: {range_str}")
    return params


def run_optimization(
    df: pd.DataFrame,
    strategy: Strategy,
    param_ranges: dict[str, list[float]],
    init_cash: float = 10_000_000,
    fees: float = 0.0015,
    slippage: float = 0.001,
    metric: str = "sharpe_ratio",
    top_n: int = 10,
) -> OptimizeResult:
    """Run grid search optimization over parameter space.

    Uses vectorbt broadcasting to evaluate all combinations efficiently.

    Args:
        df: OHLCV DataFrame.
        strategy: Strategy instance.
        param_ranges: {param_name: [values]} from parse_param_ranges().
        init_cash: Initial cash.
        fees: Fee rate.
        slippage: Slippage rate.
        metric: Metric to optimize ("sharpe_ratio", "total_return", "max_drawdown").
        top_n: Number of top results to keep.
    """
    param_names = sorted(param_ranges.keys())
    param_values = [param_ranges[name] for name in param_names]
    combinations = list(itertools.product(*param_values))

    close = df["close"].values.astype(float)
    close_series = pd.Series(close, index=df.index)

    # Generate signals for all combinations
    all_entries = []
    all_exits = []
    for combo in combinations:
        params = dict(zip(param_names, combo))
        signal = strategy.generate_signal(df, **params)
        all_entries.append((signal == 1.0).values)
        all_exits.append((signal == -1.0).values)

    entries_arr = np.column_stack(all_entries)
    exits_arr = np.column_stack(all_exits)
    close_arr = np.tile(close, (len(combinations), 1)).T

    # Run all backtests at once via vectorbt
    portfolio = vbt.Portfolio.from_signals(
        close=close_arr,
        entries=entries_arr,
        exits=exits_arr,
        init_cash=init_cash,
        fees=fees,
        freq="1D",
    )

    # Extract metrics per combination
    total_returns = portfolio.total_return().values
    try:
        sharpe_ratios = portfolio.sharpe_ratio().values
    except Exception:
        sharpe_ratios = np.zeros(len(combinations))
    max_drawdowns = portfolio.max_drawdown().values
    total_trades_arr = portfolio.trades.count().values

    rows = []
    for i, combo in enumerate(combinations):
        row = {name: combo[j] for j, name in enumerate(param_names)}
        row["total_return"] = float(total_returns[i])
        row["sharpe_ratio"] = float(sharpe_ratios[i]) if not np.isnan(sharpe_ratios[i]) else 0.0
        row["max_drawdown"] = float(abs(max_drawdowns[i]))
        row["total_trades"] = int(total_trades_arr[i])
        rows.append(row)

    results_df = pd.DataFrame(rows)

    # Sort by metric
    ascending = metric == "max_drawdown"
    results_df = results_df.sort_values(metric, ascending=ascending).reset_index(drop=True)

    best_row = results_df.iloc[0]
    best_params = {name: float(best_row[name]) for name in param_names}

    return OptimizeResult(
        strategy_name=strategy.name,
        param_names=param_names,
        results=results_df.head(top_n),
        best_params=best_params,
        best_metric=float(best_row[metric]),
        metric_name=metric,
    )


def format_optimize_report(result: OptimizeResult) -> str:
    """Format optimization results as text."""
    lines = []
    lines.append("=" * 70)
    lines.append("  PARAMETER OPTIMIZATION REPORT")
    lines.append("=" * 70)
    lines.append(f"  Strategy:      {result.strategy_name}")
    lines.append(f"  Optimize for:  {result.metric_name}")
    lines.append(f"  Combinations:  {len(result.results)} shown")
    lines.append("")

    # Best params
    param_str = ", ".join(f"{k}={v:g}" for k, v in result.best_params.items())
    lines.append(f"  Best params:   {param_str}")
    lines.append(f"  Best {result.metric_name}: {result.best_metric:.4f}")
    lines.append("")

    # Results table
    df = result.results
    header = "  " + "  ".join(f"{col:>12}" for col in df.columns)
    lines.append(header)
    lines.append("  " + "-" * (13 * len(df.columns)))
    for _, row in df.iterrows():
        vals = []
        for col in df.columns:
            v = row[col]
            if isinstance(v, float):
                vals.append(f"{v:>12.4f}")
            else:
                vals.append(f"{v:>12}")
        lines.append("  " + "  ".join(vals))

    lines.append("=" * 70)
    return "\n".join(lines)
