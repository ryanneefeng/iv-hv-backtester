# Options Strategy Backtester

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Complete-success.svg)]()

A systematic backtesting framework for 12 well-documented options strategies
across put, call, combined, and implied-volatility categories, tested against
a 25-ticker S&P 500 basket over a 5-year window (2021-2026).

Extends [OptionsPricingEngine](https://github.com/ryaneefeng/OptionsPricingEngine)
(Black-Scholes pricing, Greeks, Newton-Raphson implied vol solver) with a data
pipeline, signal generation, a pluggable multi-strategy backtest engine, and
performance analysis.

**Full analysis, honest findings, and all 12 equity curves: see [ANALYSIS.md](ANALYSIS.md)**

## Quick start
```bash
pip install -r requirements.txt
cd src
python main.py
```
Pick a category (Put / Call / Combined / Implied Volatility), pick a strategy,
confirm, and it fetches live prices, runs the backtest, prints performance
metrics, and saves an equity curve + drawdown chart to `results/<category>/`.

## Project structure
```
iv-hv-backtester/
├── data/
├── notebooks/
│   ├── check_long_put.py
│   ├── check_worst_trade.py
├── results/
│   ├── put/
│   ├── call/
│   ├── combined/
│   └── iv/
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── data_pipeline.py
│   │   ├── pricing.py
│   │   ├── signals.py
│   │   ├── backtest.py
│   │   ├── metrics.py
│   │   └── plotting.py
│   └── strategies/
│       ├── put_strategies.py
│       ├── call_strategies.py
│       ├── combined_strategies.py
│       └── iv_strategies.py
├── tests/
│   ├── conftest.py
│   ├── test_backtest.py
│   ├── test_data_pipeline.py
│   ├── test_metrics.py
│   ├── test_pricing.py
│   └── test_signals.py
├── requirements.txt
├── README.md
└── ANALYSIS.md
```

## The 12 strategies

| Category | Strategies |
|---|---|
| Put | Long Put, Cash-Secured Short Put, Bear Put Spread |
| Call | Long Call, Covered Call, Bull Call Spread |
| Combined | Long Straddle, Iron Condor, Collar |
| Implied Volatility | Short Straddle (vol spike), Long Strangle (vol compression), Calendar Spread |

## Results summary (ranked by Sharpe)

| Rank | Strategy | Trades | Total PnL | Sharpe | Max Drawdown |
|---|---|---|---|---|---|
| 1 | Long Straddle | 475 | +2301.35 | 1.72 | -54.02 |
| 2 | Collar | 616 | +1080.90 | 1.28 | -293.42 |
| 3 | Long Call | 90 | +194.32 | 1.07 | -43.57 |
| 4 | Covered Call | 616 | +614.22 | 0.43 | -782.65 |
| 5 | Bull Call Spread | 90 | +35.15 | 0.33 | -62.74 |
| 6 | Long Strangle | 128 | +51.53 | 0.17 | -126.39 |
| 7 | Short Straddle | 86 | -307.36 | -0.52 | -463.57 |
| 8 | Cash-Secured Short Put | 613 | -539.49 | -0.76 | -592.72 |
| 9 | Calendar Spread | 544 | -140.02 | -0.82 | -181.94 |
| 10 | Long Put | 86 | -116.65 | -0.93 | -112.86 |
| 11 | Bear Put Spread | 86 | -112.87 | -1.00 | -120.01 |
| 12 | Iron Condor | 86 | -116.81 | -1.03 | -138.37 |

**The headline finding isn't any single strategy's number, it's the pattern
across all 12: every pure long-options strategy was profitable, every pure
short-options strategy lost money.** Full explanation, case studies, and
equity curve charts in [ANALYSIS.md](ANALYSIS.md).

Top performer (Long Straddle) vs. bottom performer (Iron Condor):

<table>
<tr>
<td><img src="results/combined/Long_Straddle.png" alt="Long Straddle equity curve" width="420"></td>
<td><img src="results/combined/Iron_Condor.png" alt="Iron Condor equity curve" width="420"></td>
</tr>
</table>

## Methodology
- **Universe**: 25 liquid S&P 500 names across 10 sectors, 5 years of daily
  closes (2021-2026).
- **Vol proxy**: no free source of historical single-name options data exists,
  so a RiskMetrics-style EWMA volatility (λ=0.94) stands in for market-implied
  vol, compared against 30-day trailing realized volatility. This choice
  materially shapes the results, see ANALYSIS.md.
- **Trend signal**: 50/200-day moving average crossover (golden cross / death
  cross) for directional strategies.
- **Hold period**: 30 trading days per position, one open position per ticker
  at a time.
- **Costs**: $0.05 per option leg.

## Author

**Ryan Feng**
Cornell University | B.A. Mathematics, Minor: Computer Science | Class of 2029

- LinkedIn: [linkedin.com/in/ryanneefeng](https://linkedin.com/in/ryanneefeng)
- Email: ryanneefeng@gmail.com
- GitHub: [@ryanneefeng](https://github.com/ryanneefeng)

## License

This project is licensed under the MIT License - see the LICENSE file for details.