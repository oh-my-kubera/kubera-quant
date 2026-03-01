"""CLI subcommands."""

from __future__ import annotations

import argparse
import sys

PROVIDER_FIELDS: dict[str, list[dict]] = {
    "bigquery": [
        {"name": "project_id", "required": True, "prompt": "GCP Project ID"},
        {"name": "key_path", "required": False, "prompt": "Service Account Key Path (leave empty for ADC)"},
    ],
    "upbit": [
        {"name": "access_key", "required": True, "prompt": "Access Key", "secret": True},
        {"name": "secret_key", "required": True, "prompt": "Secret Key", "secret": True},
    ],
    "kis": [
        {"name": "app_key", "required": True, "prompt": "App Key", "secret": True},
        {"name": "app_secret", "required": True, "prompt": "App Secret", "secret": True},
        {"name": "account_no", "required": True, "prompt": "Account No (e.g. 12345678-01)"},
    ],
}


def cmd_credential(args: argparse.Namespace) -> None:
    """Manage credentials."""
    if args.cred_command == "add":
        _cmd_credential_add(args)
    elif args.cred_command == "list":
        _cmd_credential_list()
    elif args.cred_command == "remove":
        _cmd_credential_remove(args)
    else:
        print("Usage: kubera-quant credential {add,list,remove}")


def _cmd_credential_add(args: argparse.Namespace) -> None:
    import getpass

    provider = args.provider
    if provider not in PROVIDER_FIELDS:
        print(f"Error: unsupported provider '{provider}'. Supported: {', '.join(PROVIDER_FIELDS)}")
        sys.exit(1)

    fields = PROVIDER_FIELDS[provider]
    credential: dict[str, str] = {"provider": provider}

    for field in fields:
        prompt = field["prompt"] + ": "
        if field.get("secret"):
            value = getpass.getpass(prompt)
            if value:
                print(f"  -> {len(value)} chars")
        else:
            value = input(prompt)
        if field["required"] and not value:
            print(f"Error: '{field['name']}' is required.")
            sys.exit(1)
        if value:
            credential[field["name"]] = value

    from quant.core.credentials import save_credential
    save_credential(credential)
    print(f"\nCredential for '{provider}' saved.")


def _cmd_credential_list() -> None:
    from quant.core.credentials import load_credentials

    credentials = load_credentials()
    if not credentials:
        print("No credentials stored.")
        return

    secret_fields = set()
    for fields in PROVIDER_FIELDS.values():
        for f in fields:
            if f.get("secret"):
                secret_fields.add(f["name"])

    print(f"{'Provider':<12} {'Key':<20} {'Value'}")
    print("-" * 50)
    for cred in credentials:
        provider = cred.get("provider", "")
        for key, value in cred.items():
            if key == "provider":
                continue
            display = "***" if key in secret_fields else value
            print(f"{provider:<12} {key:<20} {display}")
            provider = ""


def _cmd_credential_remove(args: argparse.Namespace) -> None:
    from quant.core.credentials import remove_credential

    provider = args.provider
    if not remove_credential(provider):
        print(f"No credential found for provider '{provider}'.")
        sys.exit(1)
    print(f"Credential for '{provider}' removed.")


def cmd_collect(args: argparse.Namespace) -> None:
    """Collect market data."""
    market = args.collect_command
    if market not in ("krx", "crypto", "us"):
        print("Usage: kubera-quant collect {krx,crypto,us}")
        return

    from quant.core.config import get_settings
    from quant.core.credentials import get_credential

    settings = get_settings()
    symbols = [s.strip() for s in args.symbols.split(",")]
    start = args.start or settings.default_start_date
    end = args.end

    bq_cred = get_credential("bigquery")
    if bq_cred:
        _cmd_collect_bigquery(market, symbols, start, end, bq_cred, settings)
    else:
        _cmd_collect_local(market, symbols, start, end)


def _cmd_collect_local(market, symbols, start, end):
    from quant.core.data.resolver import collect_to_local

    for symbol in symbols:
        print(f"Collecting {symbol}...", end=" ", flush=True)
        df = collect_to_local(market, symbol, start, end)
        if df.empty:
            print("no data")
            continue
        print(f"{len(df)} rows")

    print("Done.")


def _cmd_collect_bigquery(market, symbols, start, end, bq_cred, settings):
    from quant.core.data.bigquery import BigQueryStore
    from quant.core.data.resolver import get_source

    source = get_source(market)
    store = BigQueryStore(
        project_id=bq_cred["project_id"],
        dataset_id=settings.bigquery_dataset,
        key_path=bq_cred.get("key_path"),
    )

    for symbol in symbols:
        print(f"Collecting {symbol}...", end=" ", flush=True)
        df = source.fetch_ohlcv(symbol, start, end)
        if df.empty:
            print("no data")
            continue
        store.upsert_ohlcv(df, market=market, symbol=symbol)
        print(f"{len(df)} rows")

    print("Done.")


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync BigQuery data to local Parquet cache."""
    from quant.core.config import get_settings
    from quant.core.credentials import get_credential
    from quant.core.data.bigquery import BigQueryStore
    from quant.core.data.cache import ParquetCache

    bq_cred = get_credential("bigquery")
    if not bq_cred:
        print("Error: no BigQuery credential. Run 'kubera-quant credential add bigquery' first.")
        sys.exit(1)

    settings = get_settings()
    store = BigQueryStore(
        project_id=bq_cred["project_id"],
        dataset_id=settings.bigquery_dataset,
        key_path=bq_cred.get("key_path"),
    )
    cache = ParquetCache()

    markets = ["krx", "crypto", "us"] if args.all else [args.market]

    for market in markets:
        symbols = store.list_symbols(market)
        print(f"Syncing {market}: {len(symbols)} symbols")
        for symbol in symbols:
            df = store.query_ohlcv(market=market, symbol=symbol)
            if df.empty:
                continue
            cache.write(market=market, symbol=symbol, df=df)
            print(f"  {symbol}: {len(df)} rows")

    print("Done.")


def cmd_backtest(args: argparse.Namespace) -> None:
    """Run backtest."""
    from quant.core.data.cache import ParquetCache
    from quant.core.strategy.base import get_strategy

    strategy = get_strategy(args.strategy)
    if not strategy:
        print(f"Error: unknown strategy '{args.strategy}'.")
        sys.exit(1)

    cache = ParquetCache()

    params = {}
    if args.params:
        for pair in args.params.split(","):
            k, v = pair.split("=")
            params[k.strip()] = float(v.strip())

    if args.symbols:
        _cmd_backtest_portfolio(args, strategy, cache, params)
    else:
        _cmd_backtest_single(args, strategy, cache, params)


def _ensure_data(cache, market, symbol, start=None, end=None):
    """Read from cache; auto-fetch from source API if empty."""
    df = cache.read(market=market, symbol=symbol, start=start, end=end)
    if not df.empty:
        return df

    from quant.core.config import get_settings
    from quant.core.data.resolver import collect_to_local

    fetch_start = start or get_settings().default_start_date
    print(f"Fetching {symbol}...", end=" ", flush=True)
    df = collect_to_local(market, symbol, fetch_start, end, cache)
    print(f"{len(df)} rows" if not df.empty else "no data")
    return df


def _cmd_backtest_single(args, strategy, cache, params):
    from quant.core.backtest.engine import run_backtest
    from quant.core.backtest.report import print_report

    df = _ensure_data(cache, args.market, args.symbol, args.start, args.end)
    if df.empty:
        print(f"Error: no data available for {args.market}/{args.symbol}.")
        sys.exit(1)

    signal = strategy.generate_signal(df, **params)
    result = run_backtest(df, signal)
    print_report(result, strategy_name=args.strategy, symbol=args.symbol)


def _cmd_backtest_portfolio(args, strategy, cache, params):
    from quant.core.backtest.engine import run_portfolio_backtest
    from quant.core.backtest.report import print_portfolio_report

    symbols = [s.strip() for s in args.symbols.split(",")]

    dfs = {}
    for sym in symbols:
        df = _ensure_data(cache, args.market, sym, args.start, args.end)
        if df.empty:
            print(f"Error: no data available for {args.market}/{sym}.")
            sys.exit(1)
        dfs[sym] = df.reset_index(drop=True)

    signals = {sym: strategy.generate_signal(dfs[sym], **params) for sym in symbols}
    result = run_portfolio_backtest(dfs, signals)
    print_portfolio_report(result, strategy_name=args.strategy)


def cmd_optimize(args: argparse.Namespace) -> None:
    """Run parameter optimization."""
    from quant.core.backtest.optimize import (
        format_optimize_report,
        parse_param_ranges,
        run_optimization,
    )
    from quant.core.data.cache import ParquetCache
    from quant.core.strategy.base import get_strategy

    strategy = get_strategy(args.strategy)
    if not strategy:
        print(f"Error: unknown strategy '{args.strategy}'.")
        sys.exit(1)

    cache = ParquetCache()
    df = _ensure_data(cache, args.market, args.symbol, args.start, args.end)
    if df.empty:
        print(f"Error: no data available for {args.market}/{args.symbol}.")
        sys.exit(1)

    param_ranges = parse_param_ranges(args.params)
    result = run_optimization(
        df, strategy, param_ranges,
        metric=args.metric, top_n=args.top,
    )
    print(format_optimize_report(result))


def cmd_strategy(args: argparse.Namespace) -> None:
    """List available strategies."""
    from quant.core.strategy.base import STRATEGIES

    if not STRATEGIES:
        print("No strategies registered.")
        return

    print(f"{'Name':<20} {'Description'}")
    print("-" * 50)
    for name, cls in STRATEGIES.items():
        desc = getattr(cls, "description", "")
        print(f"{name:<20} {desc}")
