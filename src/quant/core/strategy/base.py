"""Strategy protocol and registry."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class Strategy(Protocol):
    """Interface for trading strategies.

    Implementations must set `name` and `description` class attributes,
    and implement `generate_signal()`.
    """

    name: str
    description: str

    def generate_signal(self, df: pd.DataFrame, **params: float) -> pd.Series:
        """Generate trading signals from OHLCV data.

        Args:
            df: DataFrame with OHLCV columns.
            **params: Strategy-specific parameters.

        Returns:
            Series of signals: 1.0 (buy), -1.0 (sell), 0.0 (hold).
            Index must match df index.
        """
        ...


STRATEGIES: dict[str, Strategy] = {}


def register(cls: type) -> type:
    """Decorator to register a strategy class."""
    instance = cls()
    STRATEGIES[instance.name] = instance
    return cls


def get_strategy(name: str) -> Strategy | None:
    """Get a registered strategy by name."""
    return STRATEGIES.get(name)
