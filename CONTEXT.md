# kubera-quant

Quantitative backtesting and automated trading for the kubera ecosystem.

```
data → strategy → backtest    (backtest reads data, applies strategy)
data → strategy → trading     (trading reads data, applies strategy, executes orders)
```

| Package | Role |
|---------|------|
| data/ | Market data collection, BigQuery storage, local Parquet cache |
| strategy/ | Strategy interface and implementations |
| backtest/ | vectorbt-based backtesting engine |
| trading/ | (placeholder) Automated order execution |

Data flows through BigQuery as source of truth. Backtesting uses local Parquet cache for performance.

| Decision | Choice | Reason |
|----------|--------|--------|
| Framework | vectorbt | Fast vectorized backtesting, pandas-native |
| Data backend | BigQuery | GCP free tier, shareable across repos |
| Local cache | Parquet | Columnar, fast reads, pandas-native |
| Config pattern | kubera-intel style | CLI tool, no API server |
| Strategy signal | {-1, 0, 1} Series | Direct vectorbt compatibility |
