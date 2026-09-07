"""
Demo: runs every configured agent against synthetic (fake) price data,
just to prove the pipeline works end to end for both crypto and stock
data sources.

This is NOT a real backtest — get_synthetic_ohlcv() makes up random-walk
prices regardless of asset class. Swap in real historical data (via
data_feed.get_live_ohlcv / get_live_ohlcv_stock, or a CSV you already
have) before drawing any conclusions about a strategy.
"""

from config import AGENTS
from data_feed import get_synthetic_ohlcv
from backtester import run_backtest

if __name__ == "__main__":
    for agent in AGENTS:
        print(f"\n########## agent: {agent.name} ({type(agent.strategy).__name__}, {agent.data_source}) ##########")
        for symbol in agent.symbols:
            # Stock tickers (e.g. "CBA.AX") often start around tens of AUD;
            # crypto pairs vary hugely — just a reasonable starting point
            # for the fake random walk, not a real price.
            start_price = 50.0 if agent.data_source == "stock" else 100.0
            df = get_synthetic_ohlcv(symbol, periods=1500, start_price=start_price)
            result = run_backtest(df, agent, symbol, log_path=f"backtest_{agent.name}_{symbol.replace('/', '_')}.csv")
            print(f"\n=== {symbol} (synthetic data demo) ===")
            print(result.summary())
