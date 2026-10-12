"""
Fundamentals snapshot for the stock (ASX) symbols the agents trade.

Pulls a handful of plain company numbers from Yahoo Finance via yfinance
(already a dependency — free, no key) and stores them in the
`fundamentals` table so the dashboard can show them under each agent.

Display-only: no strategy reads these numbers. Any missing field is simply
left out; one symbol failing never stops the others, and the script exits 0
either way so a Yahoo hiccup can't turn the daily workflow red.

Run:  python fundamentals.py
"""

import json
import math
from datetime import datetime, timezone

from config import AGENTS


def _num(x):
    """Return a clean float, or None for missing / NaN / non-numeric values."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def extract_fundamentals(info: dict) -> dict:
    """Pick the few fields we show, from a yfinance `.info` dict."""
    info = info or {}
    price = _num(info.get("currentPrice")) or _num(info.get("regularMarketPrice")) or _num(info.get("previousClose"))
    div_rate = _num(info.get("dividendRate"))
    # Yahoo has changed whether `dividendYield` is a fraction or a percent
    # between versions, so work it out from dividend per share / price instead.
    div_yield_pct = round(div_rate / price * 100, 2) if (div_rate and price) else None
    low, high = _num(info.get("fiftyTwoWeekLow")), _num(info.get("fiftyTwoWeekHigh"))
    pos_52w = None
    if price and low is not None and high is not None and high > low:
        pos_52w = round(max(0.0, min(1.0, (price - low) / (high - low))), 3)
    margin = _num(info.get("profitMargins"))

    out = {
        "name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "price": price,
        "market_cap": _num(info.get("marketCap")),
        "pe_trailing": _num(info.get("trailingPE")),
        "pe_forward": _num(info.get("forwardPE")),
        "eps": _num(info.get("trailingEps")),
        "dividend_yield_pct": div_yield_pct,
        "profit_margin_pct": round(margin * 100, 1) if margin is not None else None,
        "beta": _num(info.get("beta")),
        "low_52w": low,
        "high_52w": high,
        "pos_52w": pos_52w,
    }
    return {k: v for k, v in out.items() if v is not None}


def stock_symbols() -> list:
    seen, out = set(), []
    for a in AGENTS:
        if a.data_source != "stock":
            continue
        for s in a.symbols:
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


def main() -> int:
    import yfinance as yf
    from state_store import SupabaseStateStore

    store = SupabaseStateStore()
    ok = 0
    for sym in stock_symbols():
        try:
            data = extract_fundamentals(yf.Ticker(sym).info)
            if not data:
                print(f"[fundamentals] {sym}: nothing returned, skipping")
                continue
            store.client.table("fundamentals").upsert({
                "symbol": sym,
                "data": json.dumps(data),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, on_conflict="symbol").execute()
            ok += 1
            print(f"[fundamentals] {sym}: saved {sorted(data)}")
        except Exception as e:
            print(f"[fundamentals] {sym}: failed, skipping ({e})")
    print(f"[fundamentals] done, {ok} symbol(s) saved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
