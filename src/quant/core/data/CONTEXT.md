# data

Market data collection, storage, and caching.

```
DataSource (pykrx/ccxt/yfinance) → BigQueryStore → ParquetCache → backtest
```

All sources return `pd.DataFrame` with columns: date, open, high, low, close, volume.

| Module | Role |
|--------|------|
| base.py | DataSource protocol |
| krx.py | Korean stocks via pykrx |
| crypto.py | Crypto via ccxt (Upbit default) |
| us.py | US stocks via yfinance |
| bigquery.py | BigQuery read/write, per-market tables (ohlcv_krx, ohlcv_crypto, ohlcv_us) |
| cache.py | Local Parquet cache at .quant/cache/{market}/{symbol}.parquet |

| Decision | Choice | Reason |
|----------|--------|--------|
| Column convention | Fixed 6 columns | vectorbt/BigQuery/Parquet all compatible |
| BigQuery partitioning | By date, cluster by symbol | Efficient range queries |
| Parquet per symbol | One file per symbol | Incremental merge, fast single-symbol reads |
| ccxt over Upbit SDK | Multi-exchange support | Future-proof for Binance etc. |
