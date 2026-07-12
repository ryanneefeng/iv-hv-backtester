import math

import pandas as pd
import pytest

from core.backtest import simulate_trades
from core.pricing import Option


def _make_closes_and_signals(prices, signal_days, ewma_vol=0.25, ticker="TEST"):
    n = len(prices)
    dates = pd.bdate_range("2024-01-01", periods=n)
    closes = pd.DataFrame({ticker: prices}, index=dates)

    signal = [False] * n
    for i in signal_days:
        signal[i] = True

    sdf = pd.DataFrame({"signal": signal, "ewma_vol": [ewma_vol] * n}, index=dates)
    return closes, {ticker: sdf}, dates


def test_simulate_trades_skips_days_without_signal():
    """No signal ever fires -> no trades."""
    prices = [100.0] * 40
    closes, signals, _ = _make_closes_and_signals(prices, signal_days=[])
    trades = simulate_trades(closes, signals, hold_days=10)
    assert len(trades) == 0


def test_simulate_trades_respects_one_open_position_per_ticker():
    """Signals fire on days 0, 5, 10, and 15 with a 10-day hold. Day 5 and
    day 10 both fall within (or right at the close of) the position opened
    on day 0, so only day 0 and day 15 should actually produce trades."""
    prices = [100.0 + i * 0.1 for i in range(40)]
    closes, signals, dates = _make_closes_and_signals(prices, signal_days=[0, 5, 10, 15])

    trades = simulate_trades(closes, signals, hold_days=10)

    assert len(trades) == 2
    assert list(trades["entry_date"]) == [dates[0], dates[15]]


def test_simulate_trades_skips_signal_too_close_to_end_of_data():
    """A signal that fires without enough future bars to complete the hold
    period should be dropped rather than faked."""
    prices = [100.0] * 12
    # hold_days=10 but signal fires at index 5, so exit_idx=15 is out of range
    closes, signals, _ = _make_closes_and_signals(prices, signal_days=[5])
    trades = simulate_trades(closes, signals, hold_days=10)
    assert len(trades) == 0


def test_simulate_trades_pnl_matches_manual_calculation():
    """Build a fully deterministic single-trade scenario and check the
    reported PnL matches an independently computed short-straddle PnL:
    premium collected minus payoff owed minus transaction costs."""
    prices = [100.0] * 11
    prices[10] = 105.0  # price at the exit bar
    hold_days = 10
    r = 0.05
    cost_per_leg = 0.05
    ewma_vol = 0.25

    closes, signals, dates = _make_closes_and_signals(
        prices, signal_days=[0], ewma_vol=ewma_vol
    )

    trades = simulate_trades(closes, signals, hold_days=hold_days, r=r, cost_per_leg=cost_per_leg)
    assert len(trades) == 1

    row = trades.iloc[0]

    expected_opt = Option(S=100.0, K=100.0, T=hold_days / 365.0, r=r, sigma=ewma_vol)
    expected_premium = expected_opt.call_price() + expected_opt.put_price()
    expected_payoff = max(105.0 - 100.0, 0) + max(100.0 - 105.0, 0)
    expected_cost = 2 * cost_per_leg
    expected_pnl = expected_premium - expected_payoff - expected_cost

    assert row["premium_collected"] == pytest.approx(expected_premium, abs=1e-8)
    assert row["payoff_owed"] == pytest.approx(expected_payoff, abs=1e-8)
    assert row["pnl"] == pytest.approx(expected_pnl, abs=1e-8)