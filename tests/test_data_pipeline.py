import numpy as np
import pandas as pd
import pytest

from core.data_pipeline import compute_rolling_hv, TRADING_DAYS_PER_YEAR


def _gbm_prices(n=400, daily_vol=0.02, seed=7, start=100.0):
    rng = np.random.default_rng(seed)
    log_returns = rng.normal(0, daily_vol, n)
    prices = start * np.exp(np.cumsum(log_returns))
    dates = pd.bdate_range("2023-01-01", periods=n)
    return pd.DataFrame({"TEST": prices}, index=dates)


def test_compute_rolling_hv_nan_before_window():
    """With a 30-day window, the first 30 rows can't have a full window of
    log returns yet and should be NaN; everything after should be defined."""
    closes = _gbm_prices()
    hv = compute_rolling_hv(closes, window=30)

    assert hv["TEST"].iloc[:30].isna().all()
    assert hv["TEST"].iloc[30:].notna().all()


def test_compute_rolling_hv_matches_known_volatility():
    """Generate a price path from a known daily vol, then check the
    average rolling HV estimate over the series is close to the true
    annualized volatility used to generate it."""
    daily_vol = 0.02
    closes = _gbm_prices(n=400, daily_vol=daily_vol, seed=7)
    hv = compute_rolling_hv(closes, window=30)

    true_annualized_vol = daily_vol * np.sqrt(TRADING_DAYS_PER_YEAR)
    avg_estimated_vol = hv["TEST"].dropna().mean()

    assert avg_estimated_vol == pytest.approx(true_annualized_vol, abs=0.03)