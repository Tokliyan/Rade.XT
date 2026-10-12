"""
Daily AI digest — one short plain-English summary of how the agents did.

Runs once a day from GitHub Actions. It gathers hard numbers from Supabase
(equity per agent, trades in the last 24h), then asks Claude (Haiku, a
fraction of a cent per run) to write 3-5 sentences about them. Claude is
told to use ONLY the numbers given and to give no advice.

If there is no ANTHROPIC_API_KEY, or the API call fails, a plain templated
summary is saved instead — the dashboard always gets a digest, and the
script exits 0 so a hiccup never turns the workflow red.

Run:  python daily_digest.py
"""

import json
from datetime import datetime, timedelta, timezone

from config import AGENTS_BY_NAME


def _loads(x):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return {}
    return x or {}


def agent_equity(state: dict) -> float:
    cash = float(state.get("cash") or 0)
    positions = _loads(state.get("positions"))
    snap = _loads(state.get("market_snapshot"))
    value = 0.0
    for sym, qty in positions.items():
        price = float((snap.get(sym) or {}).get("price") or 0)
        value += float(qty) * price
    return cash + value


def build_stats(states: list, trades_24h: list) -> dict:
    agents = []
    for s in sorted(states, key=lambda r: r["agent_name"]):
        name = s["agent_name"]
        cfg = AGENTS_BY_NAME.get(name)
        start = cfg.starting_balance if cfg else 100.0
        eq = agent_equity(s)
        agents.append({
            "agent": name,
            "equity": round(eq, 2),
            "start": start,
            "return_pct": round((eq / start - 1) * 100, 2) if start else 0.0,
            "paused": bool(s.get("paused")),
            "trades_24h": sum(1 for t in trades_24h if t["agent_name"] == name),
        })
    total_eq = sum(a["equity"] for a in agents)
    total_start = sum(a["start"] for a in agents)
    return {
        "agents": agents,
        "total_equity": round(total_eq, 2),
        "total_start": round(total_start, 2),
        "total_return_pct": round((total_eq / total_start - 1) * 100, 2) if total_start else 0.0,
        "trades_24h": len(trades_24h),
    }


def template_summary(stats: dict) -> str:
    ags = stats["agents"]
    if not ags:
        return "No agents have reported in yet."
    best = max(ags, key=lambda a: a["return_pct"])
    worst = min(ags, key=lambda a: a["return_pct"])
    paused = [a["agent"] for a in ags if a["paused"]]
    parts = [
        f"Combined paper equity is ${stats['total_equity']:,.2f} "
        f"({stats['total_return_pct']:+.2f}% since the start), with {stats['trades_24h']} trade(s) in the last 24 hours.",
        f"Best so far: {best['agent']} ({best['return_pct']:+.2f}%). Weakest: {worst['agent']} ({worst['return_pct']:+.2f}%).",
    ]
    if paused:
        parts.append("Paused by the daily-loss circuit breaker: " + ", ".join(paused) + ".")
    return " ".join(parts)


def ai_summary(stats: dict) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    prompt = (
        "You write the daily note for a paper-trading dashboard (fake money, real prices). "
        "Using ONLY the JSON below, write 3 to 5 plain-English sentences for a teenager: "
        "how the whole group is doing, which agent is best and worst, whether anything traded "
        "or is paused. Be honest, not hype. Do not give investment advice, do not predict "
        "the future, and do not mention anything that is not in the data.\n\n"
        + json.dumps(stats)
    )
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    if not text:
        raise ValueError("empty response")
    return text


def main() -> int:
    from state_store import SupabaseStateStore

    store = SupabaseStateStore()
    states = store.client.table("agent_state").select("*").execute().data or []
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    trades = store.client.table("trades").select("agent_name,symbol,side,timestamp").gte("timestamp", since).execute().data or []

    stats = build_stats(states, trades)
    source = "template"
    try:
        summary = ai_summary(stats)
        source = "claude"
    except Exception as e:
        print(f"[digest] AI summary unavailable, using plain template: {e}")
        summary = template_summary(stats)

    today = datetime.now(timezone.utc).date().isoformat()
    store.client.table("daily_digests").upsert({
        "day": today,
        "summary": summary,
        "source": source,
        "stats": json.dumps(stats),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="day").execute()
    print(f"[digest] saved for {today} ({source}): {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
