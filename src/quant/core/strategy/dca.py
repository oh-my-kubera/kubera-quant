"""Dollar Cost Averaging — buy at fixed intervals."""

from __future__ import annotations

import pandas as pd

from quant.core.strategy.base import register


@register
class DcaStrategy:
    """Buy every N-th trading day regardless of price."""

    name = "dca"
    description = "Dollar cost averaging (params: interval)"

    def generate_signal(self, df: pd.DataFrame, **params: float) -> pd.Series:
        interval = int(params.get("interval", 20))

        signal = pd.Series(0.0, index=df.index)
        signal.iloc[::interval] = 1.0

        return signal
