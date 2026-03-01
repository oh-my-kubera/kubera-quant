"""Local Parquet cache for OHLCV data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant.core.config import cache_dir
from quant.core.data import OHLCV_COLUMNS


class ParquetCache:
    """Read/write OHLCV Parquet files.

    Layout: .quant/cache/{market}/{symbol}.parquet
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or cache_dir()

    def _path(self, market: str, symbol: str) -> Path:
        market_dir = self.base_dir / market
        market_dir.mkdir(parents=True, exist_ok=True)
        return market_dir / f"{symbol}.parquet"

    def write(self, market: str, symbol: str, df: pd.DataFrame) -> Path:
        """Write OHLCV DataFrame to Parquet, merging with existing data."""
        path = self._path(market, symbol)

        if path.exists():
            existing = pd.read_parquet(path)
            df = pd.concat([existing, df], ignore_index=True)
            df = df.drop_duplicates(subset=["date"], keep="last")

        df = df.sort_values("date").reset_index(drop=True)
        df.to_parquet(path, index=False)
        return path

    def read(
        self,
        market: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Read OHLCV from Parquet cache."""
        path = self._path(market, symbol)

        if not path.exists():
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        df = pd.read_parquet(path)

        if start:
            df = df[df["date"] >= start]
        if end:
            df = df[df["date"] <= end]

        return df.reset_index(drop=True)

    def last_date(self, market: str, symbol: str) -> str | None:
        """Get the last date in the cache for a symbol."""
        path = self._path(market, symbol)
        if not path.exists():
            return None
        df = pd.read_parquet(path, columns=["date"])
        if df.empty:
            return None
        return str(df["date"].max())

    def list_symbols(self, market: str) -> list[str]:
        """List cached symbols for a market."""
        market_dir = self.base_dir / market
        if not market_dir.exists():
            return []
        return sorted(p.stem for p in market_dir.glob("*.parquet"))

    def list_markets(self) -> list[str]:
        """List markets that have cached data."""
        return sorted(
            d.name for d in self.base_dir.iterdir()
            if d.is_dir() and any(d.glob("*.parquet"))
        )
