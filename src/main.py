import os

from core.data_pipeline import fetch_price_history
from core.metrics import aggregate_metrics
from strategies.iv_strategies import run_short_straddle, run_long_strangle, run_calendar_spread
from strategies.put_strategies import run_long_put, run_cash_secured_short_put, run_bear_put_spread
from strategies.call_strategies import run_long_call, run_covered_call, run_bull_call_spread
from strategies.combined_strategies import run_long_straddle, run_iron_condor, run_collar
from core.plotting import plot_equity_curve

CATEGORIES = {
    "1": ("Put strategies", ["Long Put", "Cash-Secured Short Put", "Bear Put Spread"],
          [run_long_put, run_cash_secured_short_put, run_bear_put_spread]),
    "2": ("Call strategies", ["Long Call", "Covered Call", "Bull Call Spread"],
          [run_long_call, run_covered_call, run_bull_call_spread]),
    "3": ("Combined strategies", ["Long Straddle", "Iron Condor", "Collar"],
          [run_long_straddle, run_iron_condor, run_collar]),
    "4": ("Implied Volatility strategies",
          ["Short Straddle on Vol Spike", "Long Strangle on Vol Compression", "Calendar Spread"],
          [run_short_straddle, run_long_strangle, run_calendar_spread]),
}

CATEGORY_FOLDERS = {"1": "put", "2": "call", "3": "combined", "4": "iv"}

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main():
    print("Options Strategy Backtester")
    print()
    print("1) Put strategies")
    print("2) Call strategies")
    print("3) Combined strategies")
    print("4) Implied Volatility strategies")
    print()
    category = input("Pick a category (1-4): ").strip()

    if category not in CATEGORIES:
        print("Invalid choice.")
        return

    label, names, runners = CATEGORIES[category]

    if runners is None:
        print(f"\n{label} aren't built yet, check back after the next round of development.")
        return

    print(f"\n{label}:")
    for i, name in enumerate(names, start=1):
        print(f"  {i}) {name}")

    choice = input(f"\nPick a strategy (1-{len(names)}): ").strip()

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(names):
            raise ValueError
    except ValueError:
        print("Invalid choice.")
        return

    strategy_name = names[idx]
    runner = runners[idx]

    confirm = input(f"\nRun '{strategy_name}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    print("\nFetching prices...")
    closes = fetch_price_history()

    print(f"Running backtest: {strategy_name}...")
    trades = runner(closes)

    m = aggregate_metrics(trades)

    print(f"\nResults: {strategy_name}")
    print(f"  Trades: {m['num_trades']}")
    print(f"  Total PnL: {m['total_pnl']}")
    print(f"  Win rate: {m['win_rate']}")
    print(f"  Avg PnL per trade: {m['avg_pnl_per_trade']}")
    print(f"  Sharpe: {m['sharpe']}")
    print(f"  Max drawdown: {m['max_drawdown']}")

    if m["num_trades"] > 0:
        subfolder = CATEGORY_FOLDERS[category]
        target_dir = os.path.join(RESULTS_DIR, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        filename = strategy_name.replace(" ", "_") + ".png"
        save_path = os.path.join(target_dir, filename)
        plot_equity_curve(trades, strategy_name, save_path)
        print(f"\nEquity curve + drawdown saved to: results/{subfolder}/{filename}")
    else:
        print("\nNo trades triggered, nothing to plot.")


if __name__ == "__main__":
    main()