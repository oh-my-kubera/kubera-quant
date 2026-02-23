"""SMA (Simple Moving Average) crossover strategy."""

from __future__ import annotations

import pandas as pd

from quant.core.strategy.base import register


@register
class SmaCrossStrategy:
    """Buy when short SMA crosses above long SMA, sell on cross below."""

    name = "sma_cross"
    description = "SMA crossover (params: short, long)"

    def generate_signal(self, df: pd.DataFrame, **params: float) -> pd.Series:
        short_window = int(params.get("short", 5))
        long_window = int(params.get("long", 20))

        close = df["close"]
        sma_short = close.rolling(window=short_window).mean()
        sma_long = close.rolling(window=long_window).mean()

        signal = pd.Series(0.0, index=df.index)
        signal[sma_short > sma_long] = 1.0
        signal[sma_short < sma_long] = -1.0

        return signal
