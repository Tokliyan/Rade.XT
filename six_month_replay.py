"""
Closed-box replay: takes each eligible agent's strategy and replays it
against ~6 months of REAL historical price data, once per risk profile,
producing a standalone results table.

Deliberately separate from the live paper-trading system: this writes
nothing to Supabase, touches no live state, and has zero effect on the
agents actually running every 15/30 minutes on schedule. It's a what-if
tool, not part of the live pipeline — run it whenever, as often as you
like, with no consequences for the real thing.

Only the 3 price-pattern agents are eligible — news_sentiment_asx and
news_sentiment_crypto can't be replayed this way. They read TODAY's live
news to decide; there's no way to "see" what a headline said 6 months
ago, so testing them against historical data would just be asking "what
does Claude think of today's news" 6 months in a row, which is exactly
the same broken idea backtest_stats.py already rejects for them (see
their backtestable=False flag in config.py).

Every scenario reuses the exact same PaperBroker (same fees) and
RiskManager already used everywhere else in this project, via the same
run_backtest() function backtest_stats.py calls — nothing new about the
trading mechanics, only the time span (6 months instead of 14 days) and
the profile grid (3 risk profiles instead of 1).

One simplification worth knowing: for an agent trading more than one
symbol, this splits its starting balance evenly across those symbols and
backtests each independently, then sums the results — a reasonable
approximation of a shared portfolio, not a precise simulation of one
(the underlying single-symbol backtester has no concept of two symbols
competing for the same pool of cash mid-simulation).

Usage:
    python six_month_replay.py
"""

import sys
import numpy as np
import pandas as pd
from dataclasses import dataclass

from config import AGENTS_BY_NAME, RISK_PROFILES
from data_feed import get_live_ohlcv_stock, get_live_ohlcv_paginated
from backtester import run_backtest

REPLAY_MONTHS = 6
REPLAY_DAYS = REPLAY_MONTHS * 30
ELIGIBLE_AGENTS = ["asx_bluechip_steady", "asx_smallcap_growth", "crypto_store_of_value"]


@dataclass
class _EffectiveConfig:
    """Mimics an AgentConfig with one profile's multipliers already
    applied — run_backtest() only reads these specific fields."""
    strategy: object
    starting_balance: float
    fee_pct: float
    risk_per_trade: float
    stop_loss_pct: float
    take_profit_pct: float


def fetch_six_months(agent) -> dict:
    """Returns {symbol: dataframe} for every symbol this agent trades."""
    data = {}
    for symbol in agent.symbols:
        if agent.data_source == "stock":
            data[symbol] = get_live_ohlcv_stock(symbol, interval=agent.timeframe, period="6mo")
        else:
            data[symbol] = get_live_ohlcv_paginated(agent.exchange_id, symbol, agent.timeframe, days=REPLAY_DAYS)
    return data


def run_one_scenario(agent, symbol_data: dict, profile_name: str) -> dict:
    """Runs the backtester once per symbol for one (agent, profile)
    combination and returns one flat, combined result row."""
    profile = RISK_PROFILES[profile_name]
    symbols = [agent.symbols[0]] if profile["concentrate"] else agent.symbols
    per_symbol_balance = agent.starting_balance / len(symbols)

    combined_final = 0.0
    combined_start = 0.0
    total_trades = 0
    worst_drawdown = 0.0

    for symbol in symbols:
        eff = _EffectiveConfig(
            strategy=agent.strategy,
            starting_balance=per_symbol_balance,
            fee_pct=agent.fee_pct,
            risk_per_trade=agent.risk_per_trade * profile["risk_multiplier"],
            stop_loss_pct=agent.stop_loss_pct * profile["stop_loss_multiplier"],
            take_profit_pct=agent.take_profit_pct * profile["take_profit_multiplier"],
        )
        log_path = f"/tmp/replay_{agent.name}_{profile_name}_{symbol.replace('/', '_')}.csv"
        result = run_backtest(symbol_data[symbol], eff, symbol, log_path=log_path)
        combined_final += result.final_equity
        combined_start += result.starting_equity
        total_trades += result.num_trades
        worst_drawdown = max(worst_drawdown, result.max_drawdown_pct)

    return {
        "agent": agent.name,
        "profile": profile_name,
        "symbols_used": ", ".join(symbols),
        "start_usd": round(combined_start, 2),
        "final_usd": round(combined_final, 2),
        "return_pct": round((combined_final / combined_start - 1) * 100, 2),
        "trades": total_trades,
        "max_drawdown_pct": round(worst_drawdown, 2),
    }


def main():
    rows = []
    for agent_name in ELIGIBLE_AGENTS:
        agent = AGENTS_BY_NAME[agent_name]
        print(f"\nFetching ~{REPLAY_MONTHS} months of real data for {agent.name} ({agent.symbols})...")
        try:
            symbol_data = fetch_six_months(agent)
        except Exception as e:
            print(f"  FAILED to fetch history for {agent.name}: {e}", file=sys.stderr)
            continue

        for symbol, df in symbol_data.items():
            print(f"  {symbol}: {len(df)} candles, {df.index[0].date()} to {df.index[-1].date()}")

        for profile_name in RISK_PROFILES:
            row = run_one_scenario(agent, symbol_data, profile_name)
            rows.append(row)
            print(f"  [{profile_name:12s}] "
                  f"${row['start_usd']:.2f} -> ${row['final_usd']:.2f} "
                  f"({row['return_pct']:+.2f}%) "
                  f"trades={row['trades']} max_dd={row['max_drawdown_pct']:.2f}%")

    if not rows:
        print("\nNo results produced — check the errors above.", file=sys.stderr)
        sys.exit(1)

    df_results = pd.DataFrame(rows)
    print("\n" + "=" * 78)
    print(f"SUMMARY — {REPLAY_MONTHS}-month real-data replay (real history, NOT a forecast)")
    print("=" * 78)
    print(df_results.to_string(index=False))

    df_results.to_csv("six_month_replay_results.csv", index=False)
    print("\nSaved: six_month_replay_results.csv")


if __name__ == "__main__":
    main()
