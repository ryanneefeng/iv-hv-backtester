import numpy as np
import pandas as pd

from data_pipeline import fetch_price_history
from signals import generate_signals
from backtest import simulate_trades

THRESHOLD_GRID = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0]


def aggregate_metrics(trades):
    if len(trades) == 0:
        return {
            "num_trades": 0, "total_pnl": 0.0, "win_rate": None,
            "avg_pnl_per_trade": None, "sharpe": None, "max_drawdown": None,
        }

    trades = trades.sort_values("exit_date")

    equity = trades.set_index("exit_date")["pnl"].cumsum()
    running_max = equity.cummax()
    drawdown = equity - running_max
    max_dd = drawdown.min()

    monthly_pnl = trades.set_index("exit_date")["pnl"].resample("ME").sum()
    if len(monthly_pnl) >= 6 and monthly_pnl.std() > 0:
        sharpe = (monthly_pnl.mean() / monthly_pnl.std()) * np.sqrt(12)
    else:
        sharpe = None

    return {
        "num_trades": len(trades),
        "total_pnl": trades["pnl"].sum(),
        "win_rate": (trades["pnl"] > 0).mean(),
        "avg_pnl_per_trade": trades["pnl"].mean(),
        "sharpe": sharpe,
        "max_drawdown": max_dd,
    }


def split_trades(trades, split_date):
    if len(trades) == 0:
        return trades, trades
    in_sample = trades[trades["entry_date"] < split_date]
    out_sample = trades[trades["entry_date"] >= split_date]
    return in_sample, out_sample


def find_best_threshold(closes, split_date, threshold_grid=THRESHOLD_GRID):
    results = {}
    for threshold in threshold_grid:
        signals = generate_signals(closes, threshold=threshold)
        trades = simulate_trades(closes, signals)
        in_sample, _ = split_trades(trades, split_date)
        results[threshold] = aggregate_metrics(in_sample)

    def score(m):
        if m["sharpe"] is not None:
            return m["sharpe"]
        return -np.inf if m["num_trades"] == 0 else m["total_pnl"] / 1000.0

    best_threshold = max(results, key=lambda t: score(results[t]))
    return best_threshold, results


if __name__ == "__main__":
    print("Fetching prices...")
    closes = fetch_price_history()

    total_start, total_end = closes.index[0], closes.index[-1]
    split_date = total_start + (total_end - total_start) * 0.6
    print(f"Data range: {total_start.date()} to {total_end.date()}")
    print(f"In-sample / out-of-sample split at: {split_date.date()}")

    print("\nGrid searching threshold on in-sample data only...")
    best_threshold, grid_results = find_best_threshold(closes, split_date)

    print("\nIn-sample results by threshold:")
    for threshold, m in sorted(grid_results.items()):
        sharpe_str = f"{m['sharpe']:.2f}" if m["sharpe"] is not None else "N/A"
        print(f"  threshold={threshold:.1f}  trades={m['num_trades']:3d}  "
              f"total_pnl={m['total_pnl']:8.2f}  sharpe={sharpe_str}")

    print(f"\nBest threshold (by in-sample Sharpe): {best_threshold}")

    signals = generate_signals(closes, threshold=best_threshold)
    trades = simulate_trades(closes, signals)
    in_sample, out_sample = split_trades(trades, split_date)

    in_metrics = aggregate_metrics(in_sample)
    out_metrics = aggregate_metrics(out_sample)

    print(f"\n--- In-sample (threshold={best_threshold}) ---")
    for k, v in in_metrics.items():
        print(f"  {k}: {v}")

    print(f"\n--- Out-of-sample (same threshold, unseen data) ---")
    for k, v in out_metrics.items():
        print(f"  {k}: {v}")