"""
Defines the trading agents. Each AgentConfig is one independent bot:
its own asset class, symbols, strategy, risk settings, its own slice
of money — and (via Supabase) its own persisted state between runs.

Add a new agent by adding a new AgentConfig to AGENTS below. "More
agents" is just adding entries here — no new plumbing needed.
"""

import os
from dataclasses import dataclass
from typing import List, Protocol


class Strategy(Protocol):
    def generate_signal(self, df) -> str: ...


@dataclass
class AgentConfig:
    name: str                       # unique id — used as the Supabase row key
    symbols: List[str]
    strategy: Strategy
    data_source: str = "crypto"     # "crypto" (ccxt/Binance) or "stock" (yfinance, free ASX/US data)
    exchange_id: str = "binance"    # only used when data_source == "crypto"
    timeframe: str = "1h"           # candle size; for data_source="stock" this is passed to yfinance as interval
    starting_balance: float = 10.0  # deliberately tiny — easy to actually watch it move
    risk_per_trade: float = 0.02    # fraction of equity risked per trade
    stop_loss_pct: float = 0.03
    take_profit_pct: float = 0.06
    fee_pct: float = 0.001
    max_daily_loss_pct: float = 0.08  # circuit breaker: auto-pause for the day past this


# Safety switch: while True, no real orders are ever sent, no matter what
# broker credentials exist. Applies to every agent.
PAPER_TRADING: bool = True

# Real broker/exchange API credentials — only read from environment
# variables, only used if PAPER_TRADING is False (crypto agents only —
# see broker.py; stock agents have no live-execution path built yet).
API_KEY: str = os.getenv("EXCHANGE_API_KEY", "")
API_SECRET: str = os.getenv("EXCHANGE_API_SECRET", "")

# --- Live-trading specific settings (only relevant once PAPER_TRADING=False) ---
LIVE_SANDBOX: bool = True
MAX_LIVE_ORDER_USD: float = 20.0


def _build_agents() -> List[AgentConfig]:
    # Imported here (not at module top) to avoid a circular import with strategy.py
    from strategy import SmaCrossStrategy, RsiMeanReversionStrategy

    return [
        # Steady bucket: large, established ASX blue chips. Trend-following —
        # ride the wave once a stock is clearly moving.
        AgentConfig(
            name="asx_bluechip_steady",
            symbols=["CBA.AX", "BHP.AX"],
            strategy=SmaCrossStrategy(fast_period=10, slow_period=30),
            data_source="stock",
            timeframe="1h",
        ),
        # High-growth bucket: small, volatile ASX lithium miners — the
        # closest honest stand-in for "IPO-style" risk, since literal
        # pre-listing IPOs have no price history to trade on.
        AgentConfig(
            name="asx_smallcap_growth",
            symbols=["PLS.AX", "LTR.AX"],
            strategy=RsiMeanReversionStrategy(period=14, oversold=30, overbought=70),
            data_source="stock",
            timeframe="1h",
            risk_per_trade=0.015,
        ),
        # Reliability / store-of-value bucket: Bitcoin plus PAXG, a token
        # backed 1:1 by physical gold — real digital "value" assets, both
        # tradeable on the same crypto pipeline as everything else.
        AgentConfig(
            name="crypto_store_of_value",
            symbols=["BTC/USDT", "PAXG/USDT"],
            strategy=SmaCrossStrategy(fast_period=10, slow_period=30),
            data_source="crypto",
            exchange_id="binance",
            timeframe="1h",
        ),
    ]


AGENTS: List[AgentConfig] = _build_agents()
AGENTS_BY_NAME = {a.name: a for a in AGENTS}
