"""Crypto data source via ccxt (supports Upbit and other exchanges)."""

from __future__ import annotations

from datetime import date

import ccxt
import pandas as pd

from quant.core.data import OHLCV_COLUMNS


class CryptoDataSource:
    """Fetch crypto OHLCV via ccxt.

    Default exchange is Upbit. Supports any ccxt-compatible exchange.
    """

    def __init__(self, exchange_id: str = "upbit") -> None:
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({"enableRateLimit": True})

    def fetch_ohlcv(
        self, symbol: str, start: str, end: str | None = None
    ) -> pd.DataFrame:
        """Fetch OHLCV for a crypto pair.

        Args:
            symbol: Trading pair (e.g. "BTC/KRW" or "BTC-KRW").
                    Dash format is auto-converted to slash.
            start: Start date (YYYY-MM-DD).
            end: End date (YYYY-MM-DD). None means today.
        """
        # Normalize symbol: "BTC-KRW" → "BTC/KRW"
        symbol = symbol.replace("-", "/")
        end = end or date.today().isoformat()

        since = self.exchange.parse8601(f"{start}T00:00:00Z")
        end_ts = self.exchange.parse8601(f"{end}T23:59:59Z")

        all_candles = []
        while since < end_ts:
            candles = self.exchange.fetch_ohlcv(
                symbol, timeframe="1d", since=since, limit=200
            )
            if not candles:
                break
            all_candles.extend(candles)
            since = candles[-1][0] + 86400000  # next day in ms

        if not all_candles:
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
        df = df[OHLCV_COLUMNS]
        df = df[df["date"] <= end]
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)

        return df
