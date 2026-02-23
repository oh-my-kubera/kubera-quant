"""Momentum strategy — buy when price is above N-day lookback."""

from __future__ import annotations

import pandas as pd

from quant.core.strategy.base import register


@register
class MomentumStrategy:
    """Buy when current close is above close N days ago."""

    name = "momentum"
    description = "Price momentum (params: lookback)"

    def generate_signal(self, df: pd.DataFrame, **params: float) -> pd.Series:
        lookback = int(params.get("lookback", 20))

        close = df["close"]
        prev_close = close.shift(lookback)

        signal = pd.Series(0.0, index=df.index)
        signal[close > prev_close] = 1.0
        signal[close < prev_close] = -1.0

        return signal
