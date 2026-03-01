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


@dataclass
class PortfolioResult:
    """Container for multi-symbol portfolio backtest results."""

    symbols: list[str]
    per_symbol: dict[str, BacktestResult]
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
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


def run_portfolio_backtest(
    dfs: dict[str, pd.DataFrame],
    signals: dict[str, pd.Series],
    init_cash: float = 10_000_000,
    fees: float = 0.0015,
    slippage: float = 0.001,
) -> PortfolioResult:
    """Run multi-symbol portfolio backtest.

    Cash is split equally across symbols. Each symbol is traded independently.

    Args:
        dfs: {symbol: OHLCV DataFrame} — all must share the same date range.
        signals: {symbol: signal Series} matching each df's index.
        init_cash: Total initial cash (split equally across symbols).
        fees: Trading fee rate.
        slippage: Slippage rate.
    """
    symbols = sorted(dfs.keys())
    per_symbol_cash = init_cash / len(symbols)

    # Run individual backtests
    per_symbol: dict[str, BacktestResult] = {}
    for sym in symbols:
        per_symbol[sym] = run_backtest(
            dfs[sym], signals[sym], per_symbol_cash, fees, slippage
        )

    # Build combined portfolio via multi-column vectorbt
    close_dict = {}
    entries_dict = {}
    exits_dict = {}
    for sym in symbols:
        df = dfs[sym]
        close = df["close"].values.astype(float)
        sig = signals[sym]
        close_dict[sym] = pd.Series(close, index=df.index)
        entries_dict[sym] = sig == 1.0
        exits_dict[sym] = sig == -1.0

    close_df = pd.DataFrame(close_dict)
    entries_df = pd.DataFrame(entries_dict)
    exits_df = pd.DataFrame(exits_dict)

    combined = vbt.Portfolio.from_signals(
        close=close_df,
        entries=entries_df,
        exits=exits_df,
        init_cash=[per_symbol_cash] * len(symbols),
        fees=fees,
        freq="1D",
        cash_sharing=False,
    )

    # Aggregate metrics from per-symbol results and combined value series
    total_value = combined.value().sum(axis=1)
    overall_return = (total_value.iloc[-1] / init_cash) - 1

    total_trades_sum = sum(r.total_trades for r in per_symbol.values())

    # Portfolio-level drawdown
    peak = total_value.cummax()
    drawdown = ((total_value - peak) / peak).min()

    # Annualized return
    n_days = len(total_value)
    annual_factor = 252 / max(n_days, 1)
    annual_return = (1 + overall_return) ** annual_factor - 1

    # Portfolio Sharpe (daily returns)
    daily_returns = total_value.pct_change().dropna()
    sharpe = 0.0
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = float(daily_returns.mean() / daily_returns.std() * np.sqrt(252))

    return PortfolioResult(
        symbols=symbols,
        per_symbol=per_symbol,
        total_return=float(overall_return),
        sharpe_ratio=sharpe,
        max_drawdown=float(abs(drawdown)),
        total_trades=total_trades_sum,
        annual_return=float(annual_return),
        portfolio=combined,
    )
