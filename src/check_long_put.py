from data_pipeline import fetch_price_history
from put_strategies import run_long_put

closes = fetch_price_history()
trades = run_long_put(closes)

worst = trades.sort_values('pnl').head(8)
print(worst[['ticker','entry_date','exit_date','entry_price','exit_price','pnl']].to_string())