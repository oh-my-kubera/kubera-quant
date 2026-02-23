# trading

(Placeholder) Automated order execution for live trading.

Planned components:
- executor.py: 1 account = 1 Executor = 1 strategy
- manager.py: Config-driven multi-executor management
- Risk management: daily loss limit, position size cap

Depends on strategy/ and data/ only. Never imports backtest/.

Not yet implemented. See project plan for Phase 4-5.
