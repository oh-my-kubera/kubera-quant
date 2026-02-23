# core

Business logic. No CLI awareness.

```
data/ → strategy/ → backtest/
data/ → strategy/ → trading/   (future)
```

| Package | Role |
|---------|------|
| data/ | OHLCV collection (pykrx, ccxt, yfinance), BigQuery storage, Parquet cache |
| strategy/ | Strategy protocol, registry, built-in implementations |
| backtest/ | vectorbt-based backtesting engine + metrics |
| trading/ | (placeholder) Order execution, position management |

config.py: pydantic-settings, QUANT_ prefix, .quant/ directory.
credentials.py: JSON CRUD for BigQuery and exchange keys.

| Decision | Choice | Reason |
|----------|--------|--------|
| No DB for config | JSON files | CLI tool, no API server |
| Service-less | Functions + classes | No session management needed |
