"""KRX (Korean Exchange) data source via pykrx."""

from __future__ import annotations

from datetime import date

import pandas as pd
from pykrx import stock as pykrx_stock

from quant.core.data import OHLCV_COLUMNS


class KrxDataSource:
    """Fetch Korean stock OHLCV from KRX."""

    def fetch_ohlcv(
        self, symbol: str, start: str, end: str | None = None
    ) -> pd.DataFrame:
        """Fetch OHLCV for a KRX stock.

        Args:
            symbol: KRX ticker code (e.g. "005930" for Samsung).
            start: Start date (YYYY-MM-DD).
            end: End date (YYYY-MM-DD). None means today.
        """
        end = end or date.today().isoformat()
        start_fmt = start.replace("-", "")
        end_fmt = end.replace("-", "")

        df = pykrx_stock.get_market_ohlcv_by_date(start_fmt, end_fmt, symbol)

        if df.empty:
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        df = df.reset_index()
        df = df.rename(columns={
            "날짜": "date",
            "시가": "open",
            "고가": "high",
            "저가": "low",
            "종가": "close",
            "거래량": "volume",
        })

        df = df[OHLCV_COLUMNS]
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date").reset_index(drop=True)

        return df
