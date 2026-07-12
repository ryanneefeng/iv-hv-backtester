import math

import numpy as np
import pandas as pd
import pytest

from core.metrics import aggregate_metrics, split_trades


def _trades_from(pnls, exit_dates, entry_dates=None):
    entry_dates = entry_dates or exit_dates
    return pd.DataFrame({
        "entry_date": pd.to_datetime(entry_dates),
        "exit_date": pd.to_datetime(exit_dates),
        "pnl": pnls,
    })


def test_aggregate_metrics_empty_trades():
    empty = pd.DataFrame(columns=["entry_date", "exit_date", "pnl"])
    m = aggregate_metrics(empty)
    assert m == {
        "num_trades": 0, "total_pnl": 0.0, "win_rate": None,
        "avg_pnl_per_trade": None, "sharpe": None, "max_drawdown": None,
    }


def test_aggregate_metrics_total_pnl_and_win_rate():
    pnls = [10.0, -5.0, 20.0, -2.0]
    dates = ["2024-01-05", "2024-01-10", "2024-01-15", "2024-01-20"]
    trades = _trades_from(pnls, dates)

    m = aggregate_metrics(trades)

    assert m["num_trades"] == 4
    assert m["total_pnl"] == pytest.approx(sum(pnls))
    assert m["win_rate"] == pytest.approx(2 / 4)  # 2 of 4 trades positive
    assert m["avg_pnl_per_trade"] == pytest.approx(sum(pnls) / 4)


def test_aggregate_metrics_max_drawdown():
    # cumulative equity: 10, 5, -15, 15 -> running max: 10, 10, 10, 15
    # drawdown: 0, -5, -25, 0 -> max drawdown = -25
    pnls = [10.0, -5.0, -20.0, 30.0]
    dates = ["2024-01-05", "2024-01-10", "2024-01-15", "2024-01-20"]
    trades = _trades_from(pnls, dates)

    m = aggregate_metrics(trades)
    assert m["max_drawdown"] == pytest.approx(-25.0)


def test_aggregate_metrics_sharpe_none_when_fewer_than_six_months():
    """Sharpe requires >=6 resampled monthly buckets; trades confined to a
    couple of months should report sharpe=None rather than a noisy number."""
    pnls = [10.0, -5.0, 3.0]
    dates = ["2024-01-05", "2024-01-20", "2024-02-10"]
    trades = _trades_from(pnls, dates)

    m = aggregate_metrics(trades)
    assert m["sharpe"] is None


def test_aggregate_metrics_sharpe_matches_manual_calculation():
    """8 months of trades with known monthly PnL totals; sharpe should
    match (mean/std)*sqrt(12) computed independently."""
    monthly_pnls = [100.0, -50.0, 20.0, 80.0, -30.0, 60.0, 10.0, -20.0]
    dates = [f"2024-{m:02d}-15" for m in range(1, 9)]
    trades = _trades_from(monthly_pnls, dates)

    m = aggregate_metrics(trades)

    monthly = pd.Series(monthly_pnls)
    expected_sharpe = (monthly.mean() / monthly.std()) * math.sqrt(12)

    assert m["sharpe"] == pytest.approx(expected_sharpe, abs=1e-8)


def test_split_trades_by_entry_date():
    entry_dates = ["2024-01-01", "2024-03-01", "2024-06-01", "2024-09-01"]
    trades = _trades_from([1, 2, 3, 4], entry_dates, entry_dates=entry_dates)

    in_sample, out_sample = split_trades(trades, split_date=pd.Timestamp("2024-06-01"))

    assert list(in_sample["pnl"]) == [1, 2]
    assert list(out_sample["pnl"]) == [3, 4]