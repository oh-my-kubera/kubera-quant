# strategy

Trading strategy definitions.

Strategy protocol: `generate_signal(df, **params) → pd.Series` of {-1, 0, 1}.
Registry: `@register` decorator auto-registers, `get_strategy(name)` retrieves.

| Strategy | Signal logic |
|----------|-------------|
| sma_cross | Buy when short SMA > long SMA, sell when < |
| momentum | Buy when close > close N days ago, sell when < |

To add a new strategy:
1. Create file in this directory
2. Decorate class with `@register`
3. Import in `__init__.py`
