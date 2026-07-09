import numpy as np
import pandas as pd

from pricing import Option
from signals import compute_ewma_vol

RISK_FREE_RATE = 0.05
COST_PER_LEG = 0.05
HOLD_DAYS = 30
MA_SHORT = 50
MA_LONG = 200


def compute_trend_signals(closes):
    ma_short = closes.rolling(MA_SHORT).mean()
    ma_long = closes.rolling(MA_LONG).mean()
    death_cross = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))
    above_long_ma = closes > ma_long
    return ma_short, ma_long, death_cross, above_long_ma


def run_long_put(closes, otm_pct=0.05, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    ewma = compute_ewma_vol(closes)
    ma_short, ma_long, death_cross, above_long_ma = compute_trend_signals(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        sigma_series = ewma[ticker]
        signal_series = death_cross[ticker]
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

            K = S * (1 - otm_pct)
            T = hold_days / 365.0

            premium_paid = Option(S=S, K=K, T=T, r=r, sigma=sigma).put_price()
            payoff = max(K - ST, 0)
            pnl = payoff - premium_paid - cost_per_leg

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike": K,
                "entry_sigma": sigma, "premium_paid": premium_paid,
                "payoff": payoff, "transaction_cost": cost_per_leg, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)


def run_cash_secured_short_put(closes, otm_pct=0.05, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
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

            K = S * (1 - otm_pct)
            T = hold_days / 365.0

            premium_received = Option(S=S, K=K, T=T, r=r, sigma=sigma).put_price()
            payoff_owed = max(K - ST, 0)
            pnl = premium_received - payoff_owed - cost_per_leg

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike": K,
                "entry_sigma": sigma, "premium_received": premium_received,
                "payoff_owed": payoff_owed, "transaction_cost": cost_per_leg, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)


def run_bear_put_spread(closes, long_otm_pct=0.02, short_otm_pct=0.08, hold_days=HOLD_DAYS, r=RISK_FREE_RATE, cost_per_leg=COST_PER_LEG):
    ewma = compute_ewma_vol(closes)
    ma_short, ma_long, death_cross, above_long_ma = compute_trend_signals(closes)
    trades = []

    for ticker in closes.columns:
        price_series = closes[ticker]
        sigma_series = ewma[ticker]
        signal_series = death_cross[ticker]
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

            K_long = S * (1 - long_otm_pct)
            K_short = S * (1 - short_otm_pct)
            T = hold_days / 365.0

            long_leg_premium = Option(S=S, K=K_long, T=T, r=r, sigma=sigma).put_price()
            short_leg_premium = Option(S=S, K=K_short, T=T, r=r, sigma=sigma).put_price()
            net_debit = long_leg_premium - short_leg_premium

            long_payoff = max(K_long - ST, 0)
            short_payoff = max(K_short - ST, 0)
            net_payoff = long_payoff - short_payoff

            transaction_cost = 2 * cost_per_leg
            pnl = net_payoff - net_debit - transaction_cost

            trades.append({
                "ticker": ticker, "entry_date": date, "exit_date": exit_date,
                "entry_price": S, "exit_price": ST, "strike_long": K_long,
                "strike_short": K_short, "entry_sigma": sigma, "net_debit": net_debit,
                "net_payoff": net_payoff, "transaction_cost": transaction_cost, "pnl": pnl,
            })
            position_open_until = exit_date

    return pd.DataFrame(trades)