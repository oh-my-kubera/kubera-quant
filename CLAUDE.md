# kubera-quant

Quantitative backtesting and trading for the kubera ecosystem.

## Build & Test
- Package manager: uv
- Run tests: `uv run pytest`
- Run single test: `uv run pytest tests/test_xxx.py`
- Dev run: `uv run kubera-quant --help`

## Architecture
- backtest/ and trading/ never import each other
- Both depend on strategy/ and data/ only
- Strategy signals: pd.Series of {-1.0, 0.0, 1.0}
- OHLCV data: pd.DataFrame with columns (date, open, high, low, close, volume)

## Data Pipeline
- Data sources → BigQuery (source of truth) → local Parquet cache (backtest execution)
- BigQuery: per-market tables (ohlcv_krx, ohlcv_crypto, ohlcv_us)
- Cache: .quant/cache/{market}/{symbol}.parquet

## Security
- Credential keys: CLI only for input. Never log API keys.
- BigQuery service account key: stored in .quant/credentials.json
