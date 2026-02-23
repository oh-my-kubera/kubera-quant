"""US stock data source via yfinance."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from quant.core.data import OHLCV_COLUMNS


class UsDataSource:
    """Fetch US stock OHLCV from Yahoo Finance."""

    def fetch_ohlcv(
        self, symbol: str, start: str, end: str | None = None
    ) -> pd.DataFrame:
        """Fetch OHLCV for a US stock.

        Args:
            symbol: Ticker symbol (e.g. "AAPL", "MSFT").
            start: Start date (YYYY-MM-DD).
            end: End date (YYYY-MM-DD). None means today.
        """
        # yfinance end date is exclusive, so add 1 day
        if end:
            end_dt = date.fromisoformat(end) + timedelta(days=1)
            end_str = end_dt.isoformat()
        else:
            end_str = None

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end_str)

        if df.empty:
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })

        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df[OHLCV_COLUMNS]
        df = df.sort_values("date").reset_index(drop=True)

        return df
