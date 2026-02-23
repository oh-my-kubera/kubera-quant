"""Backtest report formatting."""

from __future__ import annotations

from quant.core.backtest.engine import BacktestResult


def format_report(
    result: BacktestResult,
    strategy_name: str = "",
    symbol: str = "",
) -> str:
    """Format backtest result as a text report."""
    lines = []
    lines.append("=" * 50)
    lines.append("  BACKTEST REPORT")
    lines.append("=" * 50)

    if strategy_name:
        lines.append(f"  Strategy:        {strategy_name}")
    if symbol:
        lines.append(f"  Symbol:          {symbol}")

    lines.append(f"  Total Return:    {result.total_return:+.2%}")
    lines.append(f"  Annual Return:   {result.annual_return:+.2%}")
    lines.append(f"  Sharpe Ratio:    {result.sharpe_ratio:.4f}")
    lines.append(f"  Max Drawdown:    {result.max_drawdown:.2%}")
    lines.append(f"  Win Rate:        {result.win_rate:.2%}")
    lines.append(f"  Total Trades:    {result.total_trades}")
    lines.append("=" * 50)

    return "\n".join(lines)


def print_report(
    result: BacktestResult,
    strategy_name: str = "",
    symbol: str = "",
) -> None:
    """Print backtest report to stdout."""
    print(format_report(result, strategy_name, symbol))
