"""
Single-tick agent runner — this is what a scheduler (GitHub Actions cron)
calls repeatedly. Each invocation:
  1. loads the named agent's saved state AND current risk profile from
     Supabase (profile is set from the dashboard, read fresh every tick)
  2. fetches the latest candles for each of its symbols (or just its
     primary symbol, if the profile is "aggressive" — see concentrate)
  3. checks stop-loss/take-profit on any open position
  4. asks the strategy for a fresh signal and trades on it (paper or, once
     deliberately enabled, real — see broker.py)
  5. checks the daily-loss circuit breaker (threshold depends on profile)
  6. saves the updated state + a market snapshot back to Supabase, then exits

No infinite loop, no long-running process, no server to keep on.

Usage:
    python main.py --agent trend_majors
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from config import AGENTS_BY_NAME, PAPER_TRADING, LIVE_SANDBOX, MAX_LIVE_ORDER_USD, API_KEY, API_SECRET, RISK_PROFILES
from data_feed import get_live_ohlcv, get_live_ohlcv_stock
from risk_manager import RiskManager
from broker import PaperBroker, build_live_broker
from state_store import SupabaseStateStore


def run_agent(agent_name: str) -> int:
    agent = AGENTS_BY_NAME.get(agent_name)
    if agent is None:
        print(f"Unknown agent '{agent_name}'. Known agents: {list(AGENTS_BY_NAME)}", file=sys.stderr)
        return 1

    store = SupabaseStateStore()
    existing = store.load_state(agent.name)
    today = datetime.now(timezone.utc).date().isoformat()
    live = not PAPER_TRADING

    # --- Risk profile: read fresh every tick, apply on top of the agent's own config ---
    profile_name = store.get_risk_profile(agent.name)
    profile = RISK_PROFILES.get(profile_name, RISK_PROFILES["balanced"])

    effective_risk_per_trade = agent.risk_per_trade * profile["risk_multiplier"]
    effective_stop_loss_pct = agent.stop_loss_pct * profile["stop_loss_multiplier"]
    effective_take_profit_pct = agent.take_profit_pct * profile["take_profit_multiplier"]
    effective_max_daily_loss_pct = profile["max_daily_loss_pct"] if profile["max_daily_loss_pct"] is not None else agent.max_daily_loss_pct
    symbols_to_trade = [agent.symbols[0]] if profile["concentrate"] else agent.symbols

    print(f"[{agent.name}] risk profile: {profile_name} (symbols this tick: {symbols_to_trade})")

    if live:
        if agent.data_source != "crypto":
            print(f"[{agent.name}] refusing: live execution is only wired up for data_source='crypto' agents (see broker.py). This agent trades {agent.data_source} data — stays paper-only.", file=sys.stderr)
            return 1

    live_broker = None
    paper_broker = None
    if live:
        try:
            live_broker = build_live_broker(agent.exchange_id, API_KEY, API_SECRET, PAPER_TRADING, LIVE_SANDBOX)
        except Exception as e:
            print(f"[{agent.name}] refusing/failing to start live broker: {e}", file=sys.stderr)
            return 1
        print(f"[{agent.name}] LIVE mode (sandbox={LIVE_SANDBOX}) — real orders {'(testnet, no real funds)' if LIVE_SANDBOX else 'WILL be sent with real funds'}")
    else:
        paper_broker = PaperBroker(
            starting_balance=agent.starting_balance,
            fee_pct=agent.fee_pct,
            state_store=store,
            agent_name=agent.name,
        )

    entry_prices = {}
    if existing and existing.get("entry_prices"):
        raw = existing["entry_prices"]
        entry_prices = json.loads(raw) if isinstance(raw, str) else raw

    paused = bool(existing["paused"]) if existing else False
    stored_day = existing.get("day") if existing else None
    day_start_equity = float(existing["day_start_equity"]) if existing and existing.get("day_start_equity") else None

    if stored_day != today:
        day_start_equity = None
        paused = False

    risk = RiskManager(effective_risk_per_trade, effective_stop_loss_pct, effective_take_profit_pct)

    last_prices = {}
    market_snapshot = {}
    market_note = None

    for symbol in symbols_to_trade:
        try:
            if agent.data_source == "stock":
                df = get_live_ohlcv_stock(symbol, interval=agent.timeframe)
            else:
                df = get_live_ohlcv(agent.exchange_id, symbol, agent.timeframe)
        except Exception as e:
            print(f"[{agent.name}/{symbol}] data fetch failed: {e}", file=sys.stderr)
            continue

        price = df["close"].iloc[-1]
        last_prices[symbol] = price

        # Market snapshot: current price + % change over the visible window,
        # so the dashboard can show something honest about current conditions
        # without pretending to predict anything.
        first_price = df["close"].iloc[0]
        change_pct = ((price / first_price) - 1) * 100 if first_price else 0.0
        market_snapshot[symbol] = {"price": round(float(price), 6), "change_pct": round(change_pct, 2)}

        if agent.data_source == "stock":
            market_note = "ASX trades ~10am-4pm AEST weekdays — outside those hours this is just the last traded price."

        if paused:
            print(f"[{agent.name}/{symbol}] paused (circuit breaker tripped today) — skipping")
            continue

        held = live_broker.base_holding(symbol) if live else paper_broker.positions.get(symbol, 0.0)

        # Stop-loss / take-profit on any open position
        if held > 0 and symbol in entry_prices:
            sl = risk.stop_loss_price(entry_prices[symbol], "BUY")
            tp = risk.take_profit_price(entry_prices[symbol], "BUY")
            if price <= sl or price >= tp:
                try:
                    if live:
                        order = live_broker.execute(symbol, "SELL", held)
                        filled = order.get("filled") or held
                        store.log_trade(agent.name, symbol, "SELL", filled, price, 0.0, 0.0)
                    else:
                        paper_broker.execute(df.index[-1], symbol, "SELL", held, price)
                    entry_prices.pop(symbol, None)
                    print(f"[{agent.name}/{symbol}] stop/target hit -> SELL {held:.6f} @ {price:.2f}")
                    held = 0.0
                except Exception as e:
                    print(f"[{agent.name}/{symbol}] SELL (stop/target) failed: {e}", file=sys.stderr)

        signal = agent.strategy.generate_signal(df)

        if signal == "BUY" and held == 0:
            equity = live_broker.equity(symbols_to_trade) if live else paper_broker.equity(last_prices)
            qty = risk.position_size(equity, price)
            if live and qty * price > MAX_LIVE_ORDER_USD:
                qty = MAX_LIVE_ORDER_USD / price  # hard ceiling, independent of risk_per_trade or profile
            try:
                if live:
                    order = live_broker.execute(symbol, "BUY", qty)
                    filled = order.get("filled") or qty
                    store.log_trade(agent.name, symbol, "BUY", filled, price, 0.0, 0.0)
                else:
                    paper_broker.execute(df.index[-1], symbol, "BUY", qty, price)
                entry_prices[symbol] = price
                print(f"[{agent.name}/{symbol}] BUY {qty:.6f} @ {price:.2f}")
            except Exception as e:
                print(f"[{agent.name}/{symbol}] BUY failed: {e}", file=sys.stderr)

        elif signal == "SELL" and held > 0:
            try:
                if live:
                    order = live_broker.execute(symbol, "SELL", held)
                    filled = order.get("filled") or held
                    store.log_trade(agent.name, symbol, "SELL", filled, price, 0.0, 0.0)
                else:
                    paper_broker.execute(df.index[-1], symbol, "SELL", held, price)
                entry_prices.pop(symbol, None)
                print(f"[{agent.name}/{symbol}] SELL {held:.6f} @ {price:.2f}")
            except Exception as e:
                print(f"[{agent.name}/{symbol}] SELL failed: {e}", file=sys.stderr)
        else:
            print(f"[{agent.name}/{symbol}] signal={signal}, no action")

    if live:
        equity = live_broker.equity(symbols_to_trade) if last_prices else (float(existing["cash"]) if existing else agent.starting_balance)
        cash = live_broker.fetch_free_balance().get("USDT", 0.0)
        positions = {s: live_broker.base_holding(s) for s in agent.symbols}
    else:
        equity = paper_broker.equity(last_prices) if last_prices else (float(existing["cash"]) if existing else agent.starting_balance)
        cash = paper_broker.cash
        positions = paper_broker.positions

    if day_start_equity is None:
        day_start_equity = equity

    drawdown_today = (equity / day_start_equity) - 1
    if drawdown_today <= -effective_max_daily_loss_pct:
        paused = True
        print(f"[{agent.name}] CIRCUIT BREAKER TRIPPED ({profile_name} profile, {effective_max_daily_loss_pct:.0%} threshold): down {drawdown_today:.1%} today. Pausing until tomorrow (UTC).")

    store.save_state(
        agent_name=agent.name,
        cash=cash,
        positions=positions,
        entry_prices=entry_prices,
        paused=paused,
        day=today,
        day_start_equity=day_start_equity,
        market_snapshot=market_snapshot,
        market_note=market_note,
    )

    print(f"[{agent.name}] equity=${equity:,.2f} cash=${cash:,.2f} positions={positions} paused={paused}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, help="Agent name from config.AGENTS")
    args = parser.parse_args()
    sys.exit(run_agent(args.agent))
