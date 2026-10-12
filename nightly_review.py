"""
Night Run, Rade.XT step — runs once a night on GitHub Actions, right after
the test suite (see .github/workflows/night-run.yml):

  1. TESTS   — the workflow runs pytest first and passes the outcome in.
  2. DATA    — pulls the last 24h of trades and every agent's current
               state from Supabase: equity, open positions, paused or not,
               whether its 15-minute ticks are still landing.
  3. REFINE  — for the 3 price-pattern agents, re-runs the genetic search on
               the last ~4 months and checks the winner ONCE on the ~2 months
               it never saw (same train/test discipline as genetic_optimize.py).
               If — and only if — it clears every gate in decide() below, the
               new parameters are AUTO-APPLIED to that PAPER agent by writing
               an override row that main.py picks up on its next tick.
  4. REPORT  — POSTs a summary to JARVIS (Daily Status → Night run).

Safety, all enforced in code rather than trusted to the schedule:
  - Never applies anything while PAPER_TRADING is False.
  - The 2 news-sentiment agents are never touched (no historical news).
  - Every override is bounds-checked (strategy_params.validate) on the way
    in AND on the way out (main.py ignores an invalid row).
  - One change per agent per COOLDOWN_DAYS, so a run of noisy nights can't
    whipsaw an agent's settings.
  - previous_params is stored with every change; delete the agent's row in
    agent_overrides to roll straight back to config.py.
  - Every step fails soft: a data or search error is reported, never fatal.

Env: SUPABASE_URL, SUPABASE_KEY (service role), NIGHT_RUN_TOKEN,
     JARVIS_URL (optional), TESTS_OUTCOME (set by the workflow).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np

from config import AGENTS_BY_NAME, PAPER_TRADING
import strategy_params as sp

PRICE_AGENTS = ["asx_bluechip_steady", "asx_smallcap_growth", "crypto_store_of_value"]

NIGHTLY_GENERATIONS = 8         # lighter than the manual 20 — this runs every night
MIN_IMPROVEMENT = 1.0           # held-out fitness points the new params must win by
MAX_TRAIN_TEST_GAP = 10.0       # same overfit line genetic_optimize.py uses
MIN_TEST_TRADES = 3             # a "win" on 0-2 trades is luck, not evidence
COOLDOWN_DAYS = 3
STALE_TICK_MINUTES = 90         # ticks run every 15 min; this long silent = workflow trouble

DEFAULT_JARVIS_URL = "https://jarvis-aio.onrender.com"


# ---------------------------------------------------------------- refine gate

def decide(family, current_params, current_test, candidate_params, candidate_train, candidate_test,
           last_applied_at=None, now=None):
    """Pure decision: should candidate_params replace current_params on a
    paper agent tonight? Returns {"apply": bool, "reason": str}."""
    now = now or datetime.now(timezone.utc)

    if candidate_params == current_params:
        return {"apply": False, "reason": "current settings are still the best found"}
    if not sp.validate(family, candidate_params):
        return {"apply": False, "reason": "candidate outside safe bounds"}
    if last_applied_at is not None and now - last_applied_at < timedelta(days=COOLDOWN_DAYS):
        return {"apply": False, "reason": f"changed less than {COOLDOWN_DAYS} days ago — cooling down"}
    if candidate_test["trades"] < MIN_TEST_TRADES:
        return {"apply": False, "reason": f"only {candidate_test['trades']} trades on held-out data — not enough evidence"}
    gap = candidate_train["return_pct"] - candidate_test["return_pct"]
    if gap >= MAX_TRAIN_TEST_GAP:
        return {"apply": False, "reason": f"likely overfit (train/test gap {gap:.1f} pts)"}
    gain = candidate_test["fitness"] - current_test["fitness"]
    if gain < MIN_IMPROVEMENT:
        return {"apply": False, "reason": f"held-out gain {gain:+.2f} below the {MIN_IMPROVEMENT} bar"}
    return {"apply": True, "reason": f"beat current settings by {gain:+.2f} on unseen data (gap {gap:.1f})"}


def _parse_ts(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def refine_agent(store, agent, rng):
    """Runs the nightly search for one agent. Never raises."""
    from genetic_optimize import (STRATEGY_FAMILIES, evaluate, fetch_full_history,
                                  run_genetic_search, split_train_test)

    family = sp.family_of(agent.strategy)
    ga_family = STRATEGY_FAMILIES.get(type(agent.strategy))
    if family is None or ga_family is None:
        return {"agent": agent.name, "applied": False, "reason": "strategy not tunable"}

    override = store.get_strategy_override(agent.name) if store else None
    live_strategy, source = sp.strategy_with_override(agent.strategy, override)
    current_params = sp.params_of(live_strategy)

    try:
        full = fetch_full_history(agent)
    except Exception as e:
        return {"agent": agent.name, "applied": False, "error": f"history fetch failed: {e}"}

    train, test = {}, {}
    for symbol, df in full.items():
        train[symbol], test[symbol] = split_train_test(df)
    if not any(len(df) >= 40 for df in test.values()):
        return {"agent": agent.name, "applied": False, "error": "not enough held-out candles"}

    current_test = evaluate(agent, test, ga_family, current_params)
    best = run_genetic_search(agent, train, ga_family, rng, generations=NIGHTLY_GENERATIONS, seed_params=current_params)
    candidate = {k: (round(v, 1) if isinstance(v, float) else v) for k, v in best["params"].items()}
    candidate_test = evaluate(agent, test, ga_family, candidate)

    verdict = decide(family, current_params, current_test, candidate, best["result"], candidate_test,
                     last_applied_at=_parse_ts(override.get("applied_at")) if override else None)

    result = {
        "agent": agent.name,
        "params_source": source,
        "current_params": current_params,
        "current_test": current_test,
        "candidate_params": candidate,
        "candidate_train": best["result"],
        "candidate_test": candidate_test,
        "applied": False,
        "reason": verdict["reason"],
    }

    if verdict["apply"]:
        if not PAPER_TRADING:
            result["reason"] = "would apply, but live trading is on — refine never touches live agents"
            return result
        try:
            store.save_strategy_override(
                agent.name, family, candidate, current_params, verdict["reason"],
                {"current_test": current_test, "candidate_train": best["result"], "candidate_test": candidate_test},
            )
            result["applied"] = True
        except Exception as e:
            result["error"] = f"could not save override: {e}"
    return result


# ---------------------------------------------------------------------- data

def agent_snapshot(state_rows, trades, now=None):
    """Turns raw agent_state rows + last-24h trades into one line per agent."""
    now = now or datetime.now(timezone.utc)
    out = []
    for row in sorted(state_rows, key=lambda r: r.get("agent_name", "")):
        name = row.get("agent_name")
        agent = AGENTS_BY_NAME.get(name)
        positions = row.get("positions") or {}
        if isinstance(positions, str):
            positions = json.loads(positions or "{}")
        snapshot = row.get("market_snapshot") or {}
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot or "{}")
        cash = float(row.get("cash") or 0)
        held_value = sum(float(q or 0) * float((snapshot.get(sym) or {}).get("price") or 0) for sym, q in positions.items())
        equity = cash + held_value
        start = agent.starting_balance if agent else None
        updated = _parse_ts(row.get("updated_at"))
        out.append({
            "agent": name,
            "equity": round(equity, 2),
            "return_pct": round((equity / start - 1) * 100, 2) if start else None,
            "open_positions": sorted(sym for sym, q in positions.items() if float(q or 0) > 0),
            "paused": bool(row.get("paused")),
            "trades_24h": sum(1 for t in trades if t.get("agent_name") == name),
            "minutes_since_tick": round((now - updated).total_seconds() / 60) if updated else None,
        })
    return out


# -------------------------------------------------------------------- report

def build_report(tests_outcome, agents, refinements, errors):
    needs = []
    status = "ok"

    if tests_outcome != "success":
        status = "fail"
        needs.append(f"Rade.XT tests {tests_outcome or 'did not run'} — check the Night Run action log")

    stale = [a["agent"] for a in agents
             if a["agent"] in PRICE_AGENTS and (a["minutes_since_tick"] is None or a["minutes_since_tick"] > STALE_TICK_MINUTES)]
    if stale:
        status = "fail" if status == "fail" else "warn"
        needs.append(f"Rade.XT ticks stopped for {', '.join(stale)} — check the Trading Bot action")

    paused = [a["agent"] for a in agents if a["paused"]]
    if paused:
        status = "fail" if status == "fail" else "warn"

    for r in refinements:
        if r.get("error") and "agent_overrides" in r["error"]:
            needs.append("Run the agent_overrides SQL (end of supabase_schema.sql) so refinements can apply")
            break
    if any(r.get("error") for r in refinements) or errors:
        status = "fail" if status == "fail" else "warn"

    applied = [r for r in refinements if r.get("applied")]
    total_trades = sum(a["trades_24h"] for a in agents)
    parts = [f"Tests {'passed' if tests_outcome == 'success' else tests_outcome or 'skipped'}",
             f"{total_trades} paper trade{'s' if total_trades != 1 else ''} in 24h across {len(agents)} agents"]
    if applied:
        parts.append("refined " + ", ".join(f"{r['agent']} → {r['candidate_params']}" for r in applied))
    else:
        parts.append("no settings changed")
    if paused:
        parts.append(f"circuit breaker paused {', '.join(paused)}")

    return {
        "section": "rade",
        "status": status,
        "summary": "; ".join(parts) + ".",
        "needs_you": list(dict.fromkeys(needs)),
        "details": {"agents": agents, "refinements": refinements, "errors": errors},
    }


def post_report(report):
    token = os.getenv("NIGHT_RUN_TOKEN")
    if not token:
        print("NIGHT_RUN_TOKEN not set — report printed only, not sent to JARVIS")
        return False
    url = os.getenv("JARVIS_URL", DEFAULT_JARVIS_URL).rstrip("/") + "/api/nightrun/report"
    data = json.dumps(report, default=str).encode()
    for attempt in (1, 2):  # Render free tier can be asleep — second try after it wakes
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                print(f"Reported to JARVIS: HTTP {resp.status}")
                return True
        except urllib.error.HTTPError as e:
            print(f"JARVIS rejected the report: HTTP {e.code} {e.read()[:300]!r}")
            return False
        except Exception as e:
            print(f"Report attempt {attempt} failed: {e}")
            time.sleep(20)
    return False


def main():
    tests_outcome = os.getenv("TESTS_OUTCOME", "")
    errors = []
    agents, refinements = [], []

    try:
        from state_store import SupabaseStateStore
        store = SupabaseStateStore()
    except Exception as e:
        store = None
        errors.append(f"Supabase unavailable: {e}")

    if store:
        try:
            since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            agents = agent_snapshot(store.all_agent_state(), store.trades_since(since))
        except Exception as e:
            errors.append(f"data pull failed: {e}")

    rng = np.random.default_rng(int(datetime.now(timezone.utc).strftime("%Y%m%d")))
    if store:
        for name in PRICE_AGENTS:
            print(f"\n=== refine {name} ===")
            try:
                refinements.append(refine_agent(store, AGENTS_BY_NAME[name], rng))
            except Exception as e:
                refinements.append({"agent": name, "applied": False, "error": str(e)})
            print(json.dumps(refinements[-1], default=str)[:600])

    report = build_report(tests_outcome, agents, refinements, errors)
    print("\n" + json.dumps(report, indent=2, default=str))
    post_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
