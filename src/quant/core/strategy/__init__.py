"""Strategy module — auto-registers all built-in strategies on import."""

from quant.core.strategy.base import STRATEGIES, get_strategy, register  # noqa: F401

# Import strategy modules to trigger registration
from quant.core.strategy import sma_cross, momentum, dca, rebalance  # noqa: F401
