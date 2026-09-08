"""
Computes an honest "range of outcomes" for each agent by replaying its
strategy over REAL historical data in overlapping windows — e.g. what
would have happened if you'd started this strategy on 20 different days
over the last few months, holding for ~2 weeks each time.

This is NOT a forecast. It's history: how spread out results actually
were when this same rule was applied to real market data in the past.
Min/max/median get saved to Supabase for the dashboard to show, framed
explicitly as backward-looking, not a prediction.

Run this occasionally — weekly is plenty, unlike main.py which runs every
30 min. Historical patterns don't meaningfully change tick to tick.

One simplification worth knowing: this uses each agent's own configured
("balanced" profile) settings as the baseline — it does not separately
backtest conservative/aggressive variants. And for agents trading more
than one symbol, results from all of that agent's symbols are pooled into
one combined distribution rather than modeled as a real shared portfolio.
Both are reasonable approximations for "what's the rough spread of
outcomes," not a precise simulation.

Usage:
    python backtest_stats.py
"""

import sys
import numpy as np
import pandas as pd

from config import AGENTS
from data_feed import get_live_ohlcv, get_live_ohlcv_stock
from backtester import run_backtest
from state_store import SupabaseStateStore

WINDOW_DAYS = 14
STEP_DAYS = 3
MIN_BARS_PER_WINDOW = 30


def fetch_history(agent, symbol) -> pd.DataFrame:
    if agent.data_source == "stock":
        return get_live_ohlcv_stock(symbol, interval=agent.timeframe, period="3mo")
    return get_live_ohlcv(agent.exchange_id, symbol, agent.timeframe, limit=2000)


def rolling_returns(df: pd.DataFrame, agent, symbol: str) -> list:
    if df.empty or len(df) < MIN_BARS_PER_WINDOW:
        return []
    window = pd.Timedelta(days=WINDOW_DAYS)
    step = pd.Timedelta(days=STEP_DAYS)
    start = df.index[0]
    end_limit = df.index[-1] - window
    returns = []
    while start <= end_limit:
        chunk = df[(df.index >= start) & (df.index <= start + window)]
        if len(chunk) >= MIN_BARS_PER_WINDOW:
            result = run_backtest(
                chunk, agent, symbol,
                log_path=f"/tmp/rolling_{agent.name}_{symbol.replace('/', '_')}.csv",
            )
            returns.append(result.total_return_pct)
        start += step
    return returns


def main():
    store = SupabaseStateStore()
    for agent in AGENTS:
        all_returns = []
        for symbol in agent.symbols:
            try:
                df = fetch_history(agent, symbol)
            except Exception as e:
                print(f"[{agent.name}/{symbol}] history fetch failed: {e}", file=sys.stderr)
                continue
            rets = rolling_returns(df, agent, symbol)
            print(f"[{agent.name}/{symbol}] {len(rets)} windows computed")
            all_returns.extend(rets)

        if not all_returns:
            print(f"[{agent.name}] no windows computed (not enough history yet?) — skipping")
            continue

        store.save_backtest_stats(
            agent_name=agent.name,
            min_return_pct=round(min(all_returns), 2),
            max_return_pct=round(max(all_returns), 2),
            median_return_pct=round(float(np.median(all_returns)), 2),
            num_windows=len(all_returns),
            window_days=WINDOW_DAYS,
        )
        print(f"[{agent.name}] saved: min={min(all_returns):.2f}% max={max(all_returns):.2f}% "
              f"median={np.median(all_returns):.2f}% (n={len(all_returns)})")


if __name__ == "__main__":
    main()
