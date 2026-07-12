import pandas as pd

from core.pricing import Option
from core.signals import compute_ewma_vol, generate_signals
from core.data_pipeline import compute_rolling_hv
from strategies.put_strategies import compute_trend_signals

RISK_FREE_RATE = 0.05
COST_PER_LEG = 0.05
HOLD_DAYS = 30
QUARTER_DAYS = 63


def run_long_straddle(closes, hold_days=HOLD_DAYS, entry_spacing=QUARTER_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    ewma = compute_ewma_vol(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        sigma_series = ewma[ticker]
        dates = price_series.index

        for entry_idx in range(0, len(dates), entry_spacing):
            date = dates[entry_idx]
            S = price_series.iloc[entry_idx]
            sigma = sigma_series.iloc[entry_idx]
            if pd.isna(S) or pd.isna(sigma) or sigma <= 0:
                continue

            exit_idx = entry_idx + hold_days
            if exit_idx >= len(price_series):
                continue

            exit_date = dates[exit_idx]
            ST = price_series.iloc[exit_idx]
            if pd.isna(ST):
                continue

            K = S
            T = hold_days / 365.0

            call_premium = Option(S=S, K=K, T=T, r=r, sigma=sigma).call_price()
            put_premium = Option(S=S, K=K, T=T, r=r, sigma=sigma).put_price()
            premium_paid = call_premium + put_premium

            payoff = max(ST - K, 0) + max(K - ST, 0)
            transaction_cost = 2 * cost_per_leg
            pnl = payoff - premium_paid - transaction_cost

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike": K,
                "entry_sigma": sigma, "premium_paid": premium_paid,
                "payoff": payoff, "transaction_cost": transaction_cost, "pnl": pnl,
            })

    return pd.DataFrame(trades)


def run_iron_condor(closes, threshold=1.3, wing_pct=0.05, wing_width_pct=0.05, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    signals = generate_signals(closes, threshold=threshold)
    ewma = compute_ewma_vol(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        sigma_series = ewma[ticker]
        sdf = signals[ticker]
        dates = sdf.index
        position_open_until = None

        for date in dates:
            if position_open_until is not None and date <= position_open_until:
                continue
            if not sdf.loc[date, "signal"]:
                continue

            S = price_series.loc[date]
            sigma = sigma_series.loc[date]
            if pd.isna(S) or pd.isna(sigma) or sigma <= 0:
                continue

            entry_idx = price_series.index.get_loc(date)
            exit_idx = entry_idx + hold_days
            if exit_idx >= len(price_series):
                continue

            exit_date = price_series.index[exit_idx]
            ST = price_series.iloc[exit_idx]
            if pd.isna(ST):
                continue

            K_short_call = S * (1 + wing_pct)
            K_long_call = S * (1 + wing_pct + wing_width_pct)
            K_short_put = S * (1 - wing_pct)
            K_long_put = S * (1 - wing_pct - wing_width_pct)
            T = hold_days / 365.0

            short_call = Option(S=S, K=K_short_call, T=T, r=r, sigma=sigma).call_price()
            long_call = Option(S=S, K=K_long_call, T=T, r=r, sigma=sigma).call_price()
            short_put = Option(S=S, K=K_short_put, T=T, r=r, sigma=sigma).put_price()
            long_put = Option(S=S, K=K_long_put, T=T, r=r, sigma=sigma).put_price()

            net_credit = (short_call - long_call) + (short_put - long_put)

            call_payoff = max(ST - K_short_call, 0) - max(ST - K_long_call, 0)
            put_payoff = max(K_short_put - ST, 0) - max(K_long_put - ST, 0)
            payoff_owed = call_payoff + put_payoff

            transaction_cost = 4 * cost_per_leg
            pnl = net_credit - payoff_owed - transaction_cost

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike_short_call": K_short_call,
                "strike_long_call": K_long_call, "strike_short_put": K_short_put,
                "strike_long_put": K_long_put, "entry_sigma": sigma, "net_credit": net_credit,
                "payoff_owed": payoff_owed, "transaction_cost": transaction_cost, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)


def run_collar(closes, put_otm_pct=0.05, call_otm_pct=0.05, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    ewma = compute_ewma_vol(closes)
    ma_short, ma_long, death_cross, above_long_ma = compute_trend_signals(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        sigma_series = ewma[ticker]
        signal_series = above_long_ma[ticker]
        dates = price_series.index
        position_open_until = None

        for date in dates:
            if position_open_until is not None and date <= position_open_until:
                continue
            if not signal_series.loc[date]:
                continue

            S = price_series.loc[date]
            sigma = sigma_series.loc[date]
            if pd.isna(S) or pd.isna(sigma) or sigma <= 0:
                continue

            entry_idx = price_series.index.get_loc(date)
            exit_idx = entry_idx + hold_days
            if exit_idx >= len(price_series):
                continue

            exit_date = price_series.index[exit_idx]
            ST = price_series.iloc[exit_idx]
            if pd.isna(ST):
                continue

            K_put = S * (1 - put_otm_pct)
            K_call = S * (1 + call_otm_pct)
            T = hold_days / 365.0

            put_premium_paid = Option(S=S, K=K_put, T=T, r=r, sigma=sigma).put_price()
            call_premium_received = Option(S=S, K=K_call, T=T, r=r, sigma=sigma).call_price()
            net_cost = put_premium_paid - call_premium_received

            value_at_exit = max(min(ST, K_call), K_put)

            transaction_cost = 2 * cost_per_leg
            pnl = value_at_exit - S - net_cost - transaction_cost

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike_put": K_put,
                "strike_call": K_call, "entry_sigma": sigma, "net_cost": net_cost,
                "value_at_exit": value_at_exit, "transaction_cost": transaction_cost, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)