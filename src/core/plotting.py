import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_equity_curve(trades, title, save_path):
    if len(trades) == 0:
        return None

    trades = trades.sort_values("exit_date")
    equity = trades.set_index("exit_date")["pnl"].cumsum()
    running_max = equity.cummax()
    drawdown = equity - running_max

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    ax1.plot(equity.index, equity.values, linewidth=2, color="#2563eb")
    ax1.axhline(0, linestyle="--", linewidth=1, color="gray")
    ax1.set_title(title)
    ax1.set_ylabel("Cumulative PnL ($)")
    ax1.grid(alpha=0.3)

    ax2.fill_between(drawdown.index, drawdown.values, 0, color="#dc2626", alpha=0.4)
    ax2.set_ylabel("Drawdown ($)")
    ax2.set_xlabel("Date")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    return save_path