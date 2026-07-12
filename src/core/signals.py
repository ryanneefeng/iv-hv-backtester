import math
import numpy as np
import pandas as pd

from core.data_pipeline import HV_WINDOW, TRADING_DAYS_PER_YEAR, compute_rolling_hv

EWMA_LAMBDA = 0.94  # RiskMetrics standard, ~11-day half-life
SIGNAL_THRESHOLD = 1.3  # fire when EWMA vol exceeds HV by this multiple


def compute_ewma_vol(closes, lam=EWMA_LAMBDA):
    log_returns = np.log(closes / closes.shift(1))
    ewma_var = log_returns.pow(2).ewm(alpha=1 - lam, adjust=False).mean()
    ewma_vol = np.sqrt(ewma_var) * math.sqrt(TRADING_DAYS_PER_YEAR)
    return ewma_vol


def generate_signals(closes, hv_window=HV_WINDOW, lam=EWMA_LAMBDA, threshold=SIGNAL_THRESHOLD):
    hv = compute_rolling_hv(closes, window=hv_window)
    ewma_vol = compute_ewma_vol(closes, lam=lam)

    results = {}
    for ticker in closes.columns:
        df = pd.DataFrame({
            "hv": hv[ticker],
            "ewma_vol": ewma_vol[ticker],
        })
        df["spread"] = df["ewma_vol"] / df["hv"]
        df["signal"] = df["spread"] > threshold
        results[ticker] = df

    return results


if __name__ == "__main__":
    from core.data_pipeline import fetch_price_history

    print("Fetching prices...")
    closes = fetch_price_history()

    print("Generating signals...")
    signals = generate_signals(closes)

    print(f"\nSignal counts per ticker (threshold={SIGNAL_THRESHOLD}):")
    counts = {t: int(df["signal"].sum()) for t, df in signals.items()}
    for ticker, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {ticker:6s} {count} signal days")