"""Backtest engine wrapping vectorbt."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import vectorbt as vbt


@dataclass
class BacktestResult:
    """Container for backtest results."""

    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    annual_return: float
    portfolio: vbt.Portfolio


def run_backtest(
    df: pd.DataFrame,
    signal: pd.Series,
    init_cash: float = 10_000_000,
    fees: float = 0.0015,
    slippage: float = 0.001,
) -> BacktestResult:
    """Run backtest using vectorbt.

    Args:
        df: OHLCV DataFrame with 'close' column.
        signal: Series of {-1.0, 0.0, 1.0} signals, same index as df.
        init_cash: Initial cash amount.
        fees: Trading fee rate (0.0015 = 0.15%).
        slippage: Slippage rate (0.001 = 0.1%).

    Returns:
        BacktestResult with metrics and the underlying Portfolio object.
    """
    close = df["close"].values.astype(float)
    close_series = pd.Series(close, index=df.index)

    # Convert signal to entries/exits
    entries = signal == 1.0
    exits = signal == -1.0

    # Adjust close for slippage
    adjusted_close = close_series.copy()
    adjusted_close[entries] = close_series[entries] * (1 + slippage)
    adjusted_close[exits] = close_series[exits] * (1 - slippage)

    portfolio = vbt.Portfolio.from_signals(
        close=adjusted_close,
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        fees=fees,
        freq="1D",
    )

    stats = portfolio.stats()
    total_trades = int(stats.get("Total Trades", 0))

    return BacktestResult(
        total_return=float(stats.get("Total Return [%]", 0)) / 100,
        sharpe_ratio=float(stats.get("Sharpe Ratio", 0)),
        max_drawdown=float(stats.get("Max Drawdown [%]", 0)) / 100,
        win_rate=float(stats.get("Win Rate [%]", 0)) / 100 if total_trades > 0 else 0.0,
        total_trades=total_trades,
        annual_return=float(stats.get("Annualized Return [%]", 0)) / 100,
        portfolio=portfolio,
    )
