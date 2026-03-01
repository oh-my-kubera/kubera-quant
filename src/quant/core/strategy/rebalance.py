"""Periodic rebalancing — review position at fixed intervals."""

from __future__ import annotations

import pandas as pd

from quant.core.strategy.base import register


@register
class RebalanceStrategy:
    """Review position every N-th trading day using SMA as target.

    On rebalance days: buy if close < SMA (underweight), sell if close > SMA
    (overweight). Hold on non-rebalance days.

    Full multi-asset portfolio rebalancing requires multi-symbol support (#7).
    """

    name = "rebalance"
    description = "Periodic SMA rebalancing (params: interval, window)"

    def generate_signal(self, df: pd.DataFrame, **params: float) -> pd.Series:
        interval = int(params.get("interval", 20))
        window = int(params.get("window", 50))

        close = df["close"]
        sma = close.rolling(window=window).mean()

        signal = pd.Series(0.0, index=df.index)

        for i in range(0, len(df), interval):
            if pd.notna(sma.iloc[i]):
                signal.iloc[i] = 1.0 if close.iloc[i] < sma.iloc[i] else -1.0

        return signal
