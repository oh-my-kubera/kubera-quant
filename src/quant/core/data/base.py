"""DataSource protocol."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class DataSource(Protocol):
    """Interface for market data sources.

    All implementations must return a DataFrame with columns:
    date, open, high, low, close, volume
    """

    def fetch_ohlcv(
        self, symbol: str, start: str, end: str | None = None
    ) -> pd.DataFrame:
        """Fetch OHLCV data for a symbol.

        Args:
            symbol: Ticker/symbol identifier.
            start: Start date (YYYY-MM-DD).
            end: End date (YYYY-MM-DD). None means today.

        Returns:
            DataFrame with OHLCV_COLUMNS, sorted by date ascending.
        """
        ...
