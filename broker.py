"""
Broker layer: places orders and tracks the account.

PaperBroker simulates fills against whatever price it's given, with a
simple fee model. It supports two persistence modes:
  - CSV mode (default): writes trade_log.csv locally — used by the
    backtester and demo_backtest.py, where everything runs in one process.
  - Supabase mode: pass state_store + agent_name, and it loads prior
    cash/positions from Supabase on start and pushes every update back —
    used by main.py, where each run is a fresh, disposable process.

LiveBroker executes real orders through ccxt, defaulting to the exchange's
sandbox/testnet (see its own docstring below for the full safety story —
three separate switches have to be deliberately cleared before it will
ever touch real funds).
"""

import csv
import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PaperBroker:
    starting_balance: float
    fee_pct: float
    cash: float = field(init=False)
    positions: Dict[str, float] = field(default_factory=dict)  # symbol -> qty
    log_path: Optional[str] = "trade_log.csv"   # used only in CSV mode
    state_store: Optional[object] = None         # SupabaseStateStore, for persistent mode
    agent_name: Optional[str] = None

    def __post_init__(self):
        self.cash = self.starting_balance

        if self.state_store and self.agent_name:
            existing = self.state_store.load_state(self.agent_name)
            if existing:
                import json
                self.cash = float(existing["cash"])
                raw_positions = existing.get("positions") or "{}"
                self.positions = json.loads(raw_positions) if isinstance(raw_positions, str) else raw_positions
        elif self.log_path and not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "symbol", "side", "qty", "price", "fee", "cash_after"]
                )

    def equity(self, last_prices: Dict[str, float]) -> float:
        value = self.cash
        for symbol, qty in self.positions.items():
            value += qty * last_prices.get(symbol, 0.0)
        return value

    def execute(self, timestamp, symbol: str, side: str, qty: float, price: float):
        if qty <= 0:
            return
        cost = qty * price
        fee = cost * self.fee_pct

        if side == "BUY":
            total_cost = cost + fee
            if total_cost > self.cash:
                qty = self.cash / (price * (1 + self.fee_pct))
                total_cost = qty * price * (1 + self.fee_pct)
            self.cash -= total_cost
            self.positions[symbol] = self.positions.get(symbol, 0.0) + qty
        elif side == "SELL":
            held = self.positions.get(symbol, 0.0)
            qty = min(qty, held)
            proceeds = qty * price - fee
            self.cash += proceeds
            self.positions[symbol] = held - qty
        else:
            return

        if self.state_store and self.agent_name:
            self.state_store.log_trade(self.agent_name, symbol, side, round(qty, 8), price, round(fee, 4), round(self.cash, 2))
            # Note: save_state() for cash/positions/pause/day is called by main.py
            # after all of this tick's trades are done, not per-trade.
        elif self.log_path:
            with open(self.log_path, "a", newline="") as f:
                csv.writer(f).writerow([timestamp, symbol, side, round(qty, 8), price, round(fee, 4), round(self.cash, 2)])


class LiveBroker:
    """
    Executes real orders through ccxt. Defaults to the exchange's
    sandbox/testnet endpoint (fake balance, real exchange mechanics) so the
    whole automated pipeline can be proven end to end without real money or
    identity verification — see config.LIVE_SANDBOX.

    Going properly live (real funds) requires clearing three separate,
    deliberate switches, on purpose: PAPER_TRADING=False, LIVE_SANDBOX=False,
    and the CONFIRM_LIVE_TRADING environment variable set exactly to
    "YES-I-UNDERSTAND". Missing any one of them refuses to start. Even then:
    only ever give the API key TRADE permissions, never WITHDRAWAL — so even
    if a key ever leaked, the worst case is someone trading your balance
    badly, not draining it out.
    """

    def __init__(self, exchange_id: str, api_key: str, api_secret: str, sandbox: bool):
        import ccxt
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        })
        if sandbox:
            self.exchange.set_sandbox_mode(True)
        self.sandbox = sandbox

    def fetch_free_balance(self) -> Dict[str, float]:
        balance = self.exchange.fetch_balance()
        return balance.get("free", {}) or {}

    def equity(self, symbols, quote: str = "USDT") -> float:
        """Free quote-currency balance plus the mark-to-market value of any
        held base assets across the given symbols."""
        free = self.fetch_free_balance()
        total = float(free.get(quote, 0.0))
        for symbol in symbols:
            base = symbol.split("/")[0]
            held = float(free.get(base, 0.0))
            if held > 0:
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    total += held * ticker["last"]
                except Exception:
                    pass  # if a price fetch fails, that holding just isn't counted this tick
        return total

    def base_holding(self, symbol: str) -> float:
        free = self.fetch_free_balance()
        return float(free.get(symbol.split("/")[0], 0.0))

    def execute(self, symbol: str, side: str, qty: float):
        """Places a real market order. Raises on failure (insufficient
        funds, below the exchange's minimum order size, network error,
        etc.) — the caller decides how to handle that, it's not swallowed
        here."""
        order_side = "buy" if side == "BUY" else "sell"
        return self.exchange.create_order(symbol, type="market", side=order_side, amount=qty)


def build_live_broker(exchange_id: str, api_key: str, api_secret: str,
                       paper_trading: bool, live_sandbox: bool) -> "LiveBroker":
    """The three-switch guard described in LiveBroker's docstring."""
    if paper_trading:
        raise RuntimeError("build_live_broker called but PAPER_TRADING is True.")
    if not api_key or not api_secret:
        raise RuntimeError(
            "No API credentials found (EXCHANGE_API_KEY / EXCHANGE_API_SECRET env vars). "
            "Refusing to start a live broker without them."
        )
    if not live_sandbox and os.environ.get("CONFIRM_LIVE_TRADING") != "YES-I-UNDERSTAND":
        raise RuntimeError(
            "Refusing to trade with real funds: LIVE_SANDBOX is False but the "
            "CONFIRM_LIVE_TRADING environment variable isn't set to exactly "
            "'YES-I-UNDERSTAND'. This is a deliberate extra step, not a bug."
        )
    return LiveBroker(exchange_id, api_key, api_secret, sandbox=live_sandbox)
