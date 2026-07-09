import numpy as np
import pandas as pd

from pricing import Option
from data_pipeline import compute_rolling_hv
from signals import compute_ewma_vol, generate_signals
from backtest import simulate_trades

RISK_FREE_RATE = 0.05
COST_PER_LEG = 0.05
HOLD_DAYS = 30


def compute_spread(closes, hv_window=30, lam=0.94):
    hv = compute_rolling_hv(closes, window=hv_window)
    ewma = compute_ewma_vol(closes, lam=lam)
    spread = ewma / hv
    return hv, ewma, spread


def run_short_straddle(closes, threshold=1.3):
    signals = generate_signals(closes, threshold=threshold)
    return simulate_trades(closes, signals)


def run_long_strangle(closes, threshold=0.8, otm_pct=0.05, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    hv, ewma, spread = compute_spread(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        spread_series = spread[ticker]
        ewma_series = ewma[ticker]
        dates = price_series.index
        position_open_until = None

        for date in dates:
            if position_open_until is not None and date <= position_open_until:
                continue

            sp = spread_series.loc[date]
            if pd.isna(sp) or sp >= threshold:
                continue

            S = price_series.loc[date]
            sigma = ewma_series.loc[date]
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

            K_call = S * (1 + otm_pct)
            K_put = S * (1 - otm_pct)
            T = hold_days / 365.0

            call_opt = Option(S=S, K=K_call, T=T, r=r, sigma=sigma)
            put_opt = Option(S=S, K=K_put, T=T, r=r, sigma=sigma)
            premium_paid = call_opt.call_price() + put_opt.put_price()

            payoff = max(ST - K_call, 0) + max(K_put - ST, 0)
            transaction_cost = 2 * cost_per_leg
            pnl = payoff - premium_paid - transaction_cost

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike_call": K_call,
                "strike_put": K_put, "entry_sigma": sigma,
                "premium_paid": premium_paid, "payoff": payoff,
                "transaction_cost": transaction_cost, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)


def run_calendar_spread(closes, lookback=90, drop_pct=0.9, near_days=30, far_days=60, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    hv, ewma, spread = compute_spread(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        ewma_series = ewma[ticker]
        rolling_avg = ewma_series.rolling(lookback).mean()
        dates = price_series.index
        position_open_until = None

        for date in dates:
            if position_open_until is not None and date <= position_open_until:
                continue

            e = ewma_series.loc[date]
            ravg = rolling_avg.loc[date]
            if pd.isna(e) or pd.isna(ravg) or ravg <= 0:
                continue
            if not (e < ravg * drop_pct):
                continue

            S0 = price_series.loc[date]
            sigma0 = e
            if pd.isna(S0) or sigma0 <= 0:
                continue

            entry_idx = price_series.index.get_loc(date)
            exit_idx = entry_idx + near_days
            if exit_idx >= len(price_series):
                continue

            exit_date = price_series.index[exit_idx]
            S1 = price_series.iloc[exit_idx]
            sigma1 = ewma_series.iloc[exit_idx]
            if pd.isna(S1) or pd.isna(sigma1) or sigma1 <= 0:
                continue

            K = S0
            T_near = near_days / 365.0
            T_far = far_days / 365.0
            T_remaining = (far_days - near_days) / 365.0

            short_leg_entry = Option(S=S0, K=K, T=T_near, r=r, sigma=sigma0).call_price()
            long_leg_entry = Option(S=S0, K=K, T=T_far, r=r, sigma=sigma0).call_price()
            short_leg_payoff = max(S1 - K, 0)
            long_leg_exit = Option(S=S1, K=K, T=T_remaining, r=r, sigma=sigma1).call_price()

            transaction_cost = 2 * cost_per_leg
            pnl = (short_leg_entry - short_leg_payoff) + (long_leg_exit - long_leg_entry) - transaction_cost

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S0, "exit_price": S1, "strike": K,
                "entry_sigma": sigma0, "exit_sigma": sigma1,
                "short_leg_entry": short_leg_entry, "long_leg_entry": long_leg_entry,
                "short_leg_payoff": short_leg_payoff, "long_leg_exit": long_leg_exit,
                "transaction_cost": transaction_cost, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)