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
    starting_balance: float = 100.0  # bigger numbers, same underlying math
    risk_per_trade: float = 0.02    # fraction of equity risked per trade
    stop_loss_pct: float = 0.03
    take_profit_pct: float = 0.06
    fee_pct: float = 0.001
    max_daily_loss_pct: float = 0.08  # circuit breaker: auto-pause for the day past this
    backtestable: bool = True  # False for strategies that can't meaningfully replay
                                 # historical data (e.g. anything reading LIVE news —
                                 # there's no way to "see" what a headline said months
                                 # ago, so a rolling-window backtest of it is meaningless,
                                 # not just unavailable yet)


# Safety switch: while True, no real orders are ever sent, no matter what
# broker credentials exist. Applies to every agent.
PAPER_TRADING: bool = True

# Real broker/exchange API credentials — only read from environment
# variables, only used if PAPER_TRADING is False (crypto agents only —
# see broker.py; stock agents have no live-execution path built yet).
API_KEY: str = os.getenv("EXCHANGE_API_KEY", "")
API_SECRET: str = os.getenv("EXCHANGE_API_SECRET", "")

# Only needed by the 2 news-sentiment agents below — costs real money per
# call (Claude API), unlike everything else in this project. See README.
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# --- Live-trading specific settings (only relevant once PAPER_TRADING=False) ---
LIVE_SANDBOX: bool = True
MAX_LIVE_ORDER_USD: float = 20.0

# --- Switchable risk profiles ---
# Chosen per-agent from the dashboard (via the set-risk-profile Edge
# Function), read fresh at the start of every tick. "balanced" is each
# agent's own configured values above, left untouched. The other two
# scale those values — including "aggressive", which concentrates into
# a single symbol and risks much more per trade. One thing that does NOT
# change with profile: a circuit breaker always exists. Aggressive gets a
# higher ceiling (still real risk tolerance), never an unlimited one.
RISK_PROFILES = {
    "conservative": {
        "risk_multiplier": 0.5,     # half the agent's normal risk_per_trade
        "stop_loss_multiplier": 0.7,   # tighter stop
        "take_profit_multiplier": 0.7,
        "max_daily_loss_pct": 0.04,     # lower ceiling than default
        "concentrate": False,
    },
    "balanced": {
        "risk_multiplier": 1.0,
        "stop_loss_multiplier": 1.0,
        "take_profit_multiplier": 1.0,
        "max_daily_loss_pct": None,     # use the agent's own configured value
        "concentrate": False,
    },
    "aggressive": {
        "risk_multiplier": 5.0,     # much bigger bets
        "stop_loss_multiplier": 1.5,   # wider stop, more room to move
        "take_profit_multiplier": 2.5,
        "max_daily_loss_pct": 0.20,     # higher ceiling — still a real cap, not disabled
        "concentrate": True,        # only trades the first symbol in the agent's list
    },
}


def _build_agents() -> List[AgentConfig]:
    # Imported here (not at module top) to avoid a circular import with strategy.py
    from strategy import SmaCrossStrategy, RsiMeanReversionStrategy, NewsSentimentStrategy

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
        # News-sentiment experiment (COSTS MONEY — see README). Price and
        # execution stay on the normal free rails; only the buy/sell
        # decision itself comes from a Claude sentiment call on real
        # headlines instead of a price-pattern rule.
        AgentConfig(
            name="news_sentiment_asx",
            symbols=["WES.AX"],
            strategy=NewsSentimentStrategy(news_symbol="WES.AX"),
            data_source="stock",
            timeframe="1h",
            backtestable=False,  # always reads TODAY's news — a rolling-window
                                  # backtest of it would just be asking "what
                                  # does Claude think of today" repeatedly
        ),
        AgentConfig(
            name="news_sentiment_crypto",
            symbols=["BTC/USDT"],
            strategy=NewsSentimentStrategy(news_symbol="BTC-USD"),  # yfinance ticker for news only; price/execution still via Binance above
            data_source="crypto",
            exchange_id="binance",
            timeframe="1h",
            backtestable=False,
        ),
    ]


AGENTS: List[AgentConfig] = _build_agents()
AGENTS_BY_NAME = {a.name: a for a in AGENTS}
