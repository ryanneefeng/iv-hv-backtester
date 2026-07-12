from core.data_pipeline import fetch_price_history
from core.signals import generate_signals
from core.backtest import simulate_trades
from core.metrics import split_trades, aggregate_metrics

closes = fetch_price_history()
total_start, total_end = closes.index[0], closes.index[-1]
split_date = total_start + (total_end - total_start) * 0.6

signals = generate_signals(closes, threshold=1.3)
trades = simulate_trades(closes, signals)
in_sample, out_sample = split_trades(trades, split_date)

worst = out_sample.sort_values('pnl').iloc[0]
print('worst out-of-sample trade:')
print(worst[['ticker','entry_date','exit_date','pnl']])

out_sample_excl = out_sample[~((out_sample['ticker']=='UNH') & (out_sample['entry_date']==worst['entry_date']))]
m_excl = aggregate_metrics(out_sample_excl)
print()
print('out-of-sample WITHOUT that one trade:')
for k,v in m_excl.items():
    print(f'  {k}: {v}')