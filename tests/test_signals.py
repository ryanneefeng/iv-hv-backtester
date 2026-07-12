import numpy as np
import pandas as pd
import pytest

from core.signals import compute_ewma_vol, generate_signals


def _flat_price_series(n=60, price=100.0):
    dates = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame({"TEST": [price] * n}, index=dates)


def _shock_price_series(n=80, calm_price=100.0):
    """First half: flat (zero realized vol). Second half: alternating
    +/-5% daily moves, i.e. an obvious vol regime change."""
    dates = pd.bdate_range("2024-01-01", periods=n)
    calm = [calm_price] * (n // 2)
    shocked = [calm_price]
    for i in range(1, n - n // 2):
        move = 1.05 if i % 2 == 1 else 1 / 1.05
        shocked.append(shocked[-1] * move)
    prices = calm + shocked
    return pd.DataFrame({"TEST": prices}, index=dates)


def test_compute_ewma_vol_zero_for_constant_price():
    """A flat price series has zero log returns, so EWMA vol should be
    (numerically) zero everywhere it's defined."""
    closes = _flat_price_series()
    ewma_vol = compute_ewma_vol(closes)
    valid = ewma_vol["TEST"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-8).all()


def test_compute_ewma_vol_reacts_to_vol_shock():
    """EWMA vol should be materially higher once the series enters the
    high-volatility regime than it was during the calm period."""
    closes = _shock_price_series()
    ewma_vol = compute_ewma_vol(closes)["TEST"]
    calm_vol = ewma_vol.iloc[:20].mean()
    shocked_vol = ewma_vol.iloc[-10:].mean()
    assert shocked_vol > calm_vol


def test_generate_signals_fires_when_spread_exceeds_threshold():
    """generate_signals should flag signal=True exactly where
    ewma_vol / hv > threshold, and the returned frame should carry
    hv/ewma_vol/spread columns for inspection."""
    closes = _shock_price_series(n=100)
    results = generate_signals(closes, hv_window=30, threshold=1.3)

    df = results["TEST"]
    assert {"hv", "ewma_vol", "spread", "signal"}.issubset(df.columns)

    valid = df.dropna(subset=["spread"])
    assert len(valid) > 0
    # signal should agree exactly with the spread/threshold definition
    expected = valid["spread"] > 1.3
    assert (valid["signal"] == expected).all()
    # the shock we constructed should actually trip the signal at least once
    assert valid["signal"].any()