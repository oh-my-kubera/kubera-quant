"""kubera-quant CLI entry point."""

from __future__ import annotations

import argparse

from importlib.metadata import version as get_version


def main() -> None:
    parser = argparse.ArgumentParser(prog="kubera-quant", description="Quantitative backtesting and trading")
    parser.add_argument("-V", "--version", action="version", version=f"kubera-quant {get_version('kubera-quant')}")
    subparsers = parser.add_subparsers(dest="command")

    # kubera-quant credential
    cred_parser = subparsers.add_parser("credential", help="Manage credentials")
    cred_sub = cred_parser.add_subparsers(dest="cred_command")

    cred_add = cred_sub.add_parser("add", help="Add a credential")
    cred_add.add_argument("provider", type=str, help="Provider name (bigquery, upbit, kis)")

    cred_sub.add_parser("list", help="List credentials")

    cred_remove = cred_sub.add_parser("remove", help="Remove a credential")
    cred_remove.add_argument("provider", type=str, help="Provider name")

    # kubera-quant collect
    collect_parser = subparsers.add_parser("collect", help="Collect market data to BigQuery")
    collect_sub = collect_parser.add_subparsers(dest="collect_command")

    for market in ("krx", "crypto", "us"):
        p = collect_sub.add_parser(market, help=f"Collect {market.upper()} market data")
        p.add_argument("--symbols", type=str, required=True, help="Comma-separated symbols")
        p.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
        p.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")

    # kubera-quant sync
    sync_parser = subparsers.add_parser("sync", help="Sync BigQuery to local Parquet cache")
    sync_parser.add_argument("market", type=str, nargs="?", help="Market (krx, crypto, us)")
    sync_parser.add_argument("--all", action="store_true", help="Sync all markets")

    # kubera-quant backtest
    bt_parser = subparsers.add_parser("backtest", help="Run backtest")
    bt_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    symbol_group = bt_parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument("--symbol", type=str, help="Single symbol")
    symbol_group.add_argument("--symbols", type=str, help="Comma-separated symbols for portfolio backtest")
    bt_parser.add_argument("--market", type=str, required=True, help="Market (krx, crypto, us)")
    bt_parser.add_argument("--start", type=str, default=None, help="Start date")
    bt_parser.add_argument("--end", type=str, default=None, help="End date")
    bt_parser.add_argument("--params", type=str, default=None, help="Strategy params (k1=v1,k2=v2)")

    # kubera-quant optimize
    opt_parser = subparsers.add_parser("optimize", help="Grid search parameter optimization")
    opt_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    opt_parser.add_argument("--symbol", type=str, required=True, help="Symbol")
    opt_parser.add_argument("--market", type=str, required=True, help="Market (krx, crypto, us)")
    opt_parser.add_argument("--params", type=str, required=True, help="Param ranges (short=3:10:1,long=10:50:5)")
    opt_parser.add_argument("--start", type=str, default=None, help="Start date")
    opt_parser.add_argument("--end", type=str, default=None, help="End date")
    opt_parser.add_argument("--metric", type=str, default="sharpe_ratio", help="Metric to optimize (sharpe_ratio, total_return, max_drawdown)")
    opt_parser.add_argument("--top", type=int, default=10, help="Show top N results")

    # kubera-quant strategy
    subparsers.add_parser("strategy", help="List available strategies")

    args = parser.parse_args()

    if args.command == "credential":
        from quant.cli.commands import cmd_credential
        cmd_credential(args)
    elif args.command == "collect":
        from quant.cli.commands import cmd_collect
        cmd_collect(args)
    elif args.command == "sync":
        from quant.cli.commands import cmd_sync
        cmd_sync(args)
    elif args.command == "backtest":
        from quant.cli.commands import cmd_backtest
        cmd_backtest(args)
    elif args.command == "optimize":
        from quant.cli.commands import cmd_optimize
        cmd_optimize(args)
    elif args.command == "strategy":
        from quant.cli.commands import cmd_strategy
        cmd_strategy(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
