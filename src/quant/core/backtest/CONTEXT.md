# backtest

vectorbt-based backtesting engine.

| Module | Role |
|--------|------|
| engine.py | `run_backtest()` — signal → vectorbt Portfolio → BacktestResult |
| report.py | Format/print BacktestResult as text report |

BacktestResult contains: total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, annual_return, and the raw vectorbt Portfolio for custom analysis.

| Decision | Choice | Reason |
|----------|--------|--------|
| vectorbt wrapping | Thin wrapper | Expose Portfolio for advanced users |
| Slippage model | Adjust close price | Simple, sufficient for daily bars |
| Default fees | 0.15% | Korean stock commission baseline |
