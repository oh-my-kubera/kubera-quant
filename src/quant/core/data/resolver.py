"""Data resolver — centralized data fetching with local cache."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from quant.core.data.cache import ParquetCache


def get_source(market: str):
    """Get the appropriate DataSource for a market.

    Lazy imports to avoid requiring all data source dependencies.
    """
    if market == "krx":
        from quant.core.data.krx import KrxDataSource

        return KrxDataSource()
    elif market == "crypto":
        from quant.core.data.crypto import CryptoDataSource

        return CryptoDataSource()
    elif market == "us":
        from quant.core.data.us import UsDataSource

        return UsDataSource()
    else:
        raise ValueError(f"Unknown market: {market}")


def collect_to_local(
    market: str,
    symbol: str,
    start: str,
    end: str | None = None,
    cache: ParquetCache | None = None,
) -> pd.DataFrame:
    """Fetch from source API and save to local Parquet.

    Supports incremental collection: only fetches data after
    the last date already cached.

    Returns the full cached data for the requested range.
    """
    cache = cache or ParquetCache()
    end = end or date.today().isoformat()

    # Incremental: skip dates already cached
    fetch_start = start
    last = cache.last_date(market, symbol)
    if last and last >= start:
        next_day = (date.fromisoformat(last) + timedelta(days=1)).isoformat()
        if next_day > end:
            return cache.read(market, symbol, start=start, end=end)
        fetch_start = next_day

    source = get_source(market)
    df = source.fetch_ohlcv(symbol, fetch_start, end)

    if not df.empty:
        cache.write(market, symbol, df)

    return cache.read(market, symbol, start=start, end=end)
