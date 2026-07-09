import pandas as pd
from pricing import Option

HOLD_DAYS = 30
RISK_FREE_RATE = 0.05
COST_PER_LEG = 0.05  # per the spec: $0.05 per contract


def simulate_trades(closes, signals, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    trades = []

    for ticker, sdf in signals.items():
        price_series = closes[ticker]
        dates = sdf.index
        position_open_until = None

        for date in dates:
            # Skip if we're still holding a position on this name
            if position_open_until is not None and date <= position_open_until:
                continue

            if not sdf.loc[date, "signal"]:
                continue

            S = price_series.loc[date]
            sigma = sdf.loc[date, "ewma_vol"]

            # Skip days where inputs aren't usable (NaN early in the series, etc.)
            if pd.isna(S) or pd.isna(sigma) or sigma <= 0:
                continue

            entry_idx = price_series.index.get_loc(date)
            exit_idx = entry_idx + hold_days

            # Not enough future data to hold to expiry, skip rather than fake it
            if exit_idx >= len(price_series):
                continue

            exit_date = price_series.index[exit_idx]
            ST = price_series.iloc[exit_idx]

            if pd.isna(ST):
                continue

            K = S  # at-the-money
            T = hold_days / 365.0

            opt = Option(S=S, K=K, T=T, r=r, sigma=sigma)
            premium_collected = opt.call_price() + opt.put_price()

            payoff_owed = max(ST - K, 0) + max(K - ST, 0)
            transaction_cost = 2 * cost_per_leg  # call leg + put leg

            pnl = premium_collected - payoff_owed - transaction_cost

            trades.append({
                "ticker": ticker,
                "entry_date": date,
                "exit_date": exit_date,
                "entry_price": S,
                "exit_price": ST,
                "strike": K,
                "entry_sigma": sigma,
                "premium_collected": premium_collected,
                "payoff_owed": payoff_owed,
                "transaction_cost": transaction_cost,
                "pnl": pnl,
            })

            position_open_until = exit_date

    return pd.DataFrame(trades)


if __name__ == "__main__":
    from data_pipeline import fetch_price_history
    from signals import generate_signals

    print("Fetching prices...")
    closes = fetch_price_history()

    print("Generating signals...")
    signals = generate_signals(closes)

    print("Simulating trades...")
    trades = simulate_trades(closes, signals)

    print(f"\nTotal completed trades: {len(trades)}")
    print(f"Total PnL: {trades['pnl'].sum():.2f}")
    print(f"Win rate: {(trades['pnl'] > 0).mean()*100:.1f}%")
    print(f"\nPnL by ticker:")
    print(trades.groupby("ticker")["pnl"].sum().sort_values(ascending=False).round(2).to_string())