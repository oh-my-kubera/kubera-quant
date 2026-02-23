"""Data module — OHLCV DataFrame column convention.

All data sources return DataFrames with these columns:
    date   : datetime64[ns] or date string (YYYY-MM-DD)
    open   : float64
    high   : float64
    low    : float64
    close  : float64
    volume : int64
"""

OHLCV_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
