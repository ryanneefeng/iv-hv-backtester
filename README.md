# IV/HV Volatility Risk Premium Backtester

A systematic backtest of the volatility risk premium: selling at-the-money
straddles when a stock's implied (or implied-proxy) volatility trades well
above its realized historical volatility, across a basket of liquid S&P 500
names over a 5-year window.

Extends [OptionsPricingEngine](https://github.com/ryaneefeng/options-pricing-engine)
(Black-Scholes pricing, Greeks, Newton-Raphson implied vol solver) by adding
a data pipeline, signal generation, trade simulation, and performance
analysis on top of the existing pricing core.

**Status: in progress.**

## Project structure
```
iv-hv-backtester/
├── data/           # cached price/vol data (gitignored)
├── src/
│   ├── data_pipeline.py   # price history + rolling historical volatility
│   ├── signals.py         # IV proxy + threshold-based entry signal
│   ├── backtest.py        # straddle simulation loop
│   ├── metrics.py         # Sharpe, max drawdown, win rate
│   └── pricing.py         # Black-Scholes engine (from OptionsPricingEngine)
├── notebooks/      # exploratory analysis
├── results/        # output metrics/plots (gitignored)
├── tests/          # pytest suite
├── requirements.txt
└── README.md
```

## Setup
```bash
pip install -r requirements.txt
```

## Methodology
1. Pull 5 years of daily prices for 25 liquid S&P 500 names across sectors.
2. Compute rolling 30-day historical volatility per name.
3. Flag a signal when the vol proxy exceeds realized vol by a set threshold.
4. Simulate selling an at-the-money straddle on signal, hold 30 days, mark
   PnL against transaction costs.
5. Evaluate on an in-sample / out-of-sample split to avoid curve-fitting.

## Results
_(to be filled in after the backtest is complete)_

## Author
Ryan Feng Cornell University | B.A. Mathematics, Minor: Computer Science | Class of 2029

- LinkedIn: linkedin.com/in/ryanneefeng
- Email: ryanneefeng@gmail.com
- GitHub: @ryanneefeng