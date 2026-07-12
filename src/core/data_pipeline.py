import math
import numpy as np
import pandas as pd
import yfinance as yf

# 25 liquid S&P 500 names spread across sectors, so the backtest isn't
# dominated by one industry's vol regime (e.g. all tech in a rate-hike year)
TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META",    # Tech
    "JPM", "GS", "BAC",                         # Financials
    "UNH", "JNJ", "PFE",                        # Healthcare
    "PG", "KO", "MCD", "NKE",                   # Consumer
    "CAT", "BA", "HON",                         # Industrials
    "XOM", "CVX",                               # Energy
    "DIS", "NFLX",                              # Communication
    "NEE",                                      # Utilities
    "LIN",                                      # Materials
    "PLD",                                      # Real estate
]

TRADING_DAYS_PER_YEAR = 252
HV_WINDOW = 30  # trading days


def fetch_price_history(tickers=None, period="5y"):
    tickers = tickers or TICKERS
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)

    # yf.download returns MultiIndex columns when given a list of tickers
    closes = raw["Close"]

    # Drop any ticker that failed to download rather than letting one bad
    # ticker (delisting, typo, temporary Yahoo outage) kill the whole basket
    closes = closes.dropna(axis=1, how="all")
    missing = set(tickers) - set(closes.columns)
    if missing:
        print(f"Warning: no data returned for {sorted(missing)}, dropping from basket")

    return closes


def compute_rolling_hv(closes, window=HV_WINDOW):
    log_returns = np.log(closes / closes.shift(1))
    rolling_std = log_returns.rolling(window=window).std()
    annualized_hv = rolling_std * math.sqrt(TRADING_DAYS_PER_YEAR)
    return annualized_hv


if __name__ == "__main__":
    print(f"Fetching {len(TICKERS)} tickers, 5y daily history...")
    closes = fetch_price_history()
    print(f"Got {closes.shape[0]} trading days for {closes.shape[1]} tickers")

    hv = compute_rolling_hv(closes)
    print("\nMost recent 30-day HV by ticker:")
    print((hv.iloc[-1] * 100).round(2).sort_values(ascending=False).to_string())
