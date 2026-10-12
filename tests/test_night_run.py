"""Nightly refine gate, override plumbing and report building."""
from datetime import datetime, timedelta, timezone

import nightly_review as nr
import strategy_params as sp
from config import AGENTS_BY_NAME
from strategy import NewsSentimentStrategy, RsiMeanReversionStrategy, SmaCrossStrategy

NOW = datetime(2026, 10, 13, 17, 30, tzinfo=timezone.utc)
CUR = {"fast_period": 10, "slow_period": 30}
NEW = {"fast_period": 8, "slow_period": 34}


def res(ret, fit, trades=10):
    return {"return_pct": ret, "fitness": fit, "trades": trades, "max_drawdown_pct": 2.0}


# --- strategy_params ----------------------------------------------------

def test_validate_bounds():
    assert sp.validate("sma", {"fast_period": 5, "slow_period": 30})
    assert not sp.validate("sma", {"fast_period": 1, "slow_period": 30})        # too fast
    assert not sp.validate("sma", {"fast_period": 20, "slow_period": 22})       # slow too close
    assert not sp.validate("sma", {"fast_period": 5})                           # missing key
    assert not sp.validate("sma", {"fast_period": True, "slow_period": 30})     # bool isn't a number
    assert sp.validate("rsi", {"period": 14, "oversold": 30.0, "overbought": 70.0})
    assert not sp.validate("rsi", {"period": 14, "oversold": 5.0, "overbought": 70.0})
    assert not sp.validate("news", {"x": 1})


def test_override_used_only_when_valid_and_matching():
    base = SmaCrossStrategy(10, 30)
    s, src = sp.strategy_with_override(base, {"family": "sma", "params": NEW})
    assert src == "override" and (s.fast_period, s.slow_period) == (8, 34)
    assert sp.strategy_with_override(base, None)[1] == "config"
    assert sp.strategy_with_override(base, {"family": "rsi", "params": {"period": 14, "oversold": 30, "overbought": 70}})[1] == "config"
    assert sp.strategy_with_override(base, {"family": "sma", "params": {"fast_period": 1, "slow_period": 2}})[1] == "config"
    news = NewsSentimentStrategy(news_symbol="X")
    assert sp.strategy_with_override(news, {"family": "sma", "params": NEW})[0] is news


def test_params_round_trip():
    for strat in (SmaCrossStrategy(7, 40), RsiMeanReversionStrategy(12, 25.0, 75.0)):
        fam = sp.family_of(strat)
        assert sp.params_of(sp.build(fam, sp.params_of(strat))) == sp.params_of(strat)


# --- decide() gate -------------------------------------------------------

def test_decide_applies_a_clear_held_out_win():
    d = nr.decide("sma", CUR, res(1, 0.5), NEW, res(6, 5), res(4, 3.0), now=NOW)
    assert d["apply"], d


def test_decide_blocks_each_failure_mode():
    base = dict(family="sma", current_params=CUR, current_test=res(1, 0.5), candidate_params=NEW,
                candidate_train=res(6, 5), candidate_test=res(4, 3.0), now=NOW)
    cases = {
        "same params": dict(candidate_params=CUR),
        "out of bounds": dict(candidate_params={"fast_period": 1, "slow_period": 3}),
        "cooldown": dict(last_applied_at=NOW - timedelta(days=1)),
        "too few trades": dict(candidate_test=res(4, 3.0, trades=2)),
        "overfit": dict(candidate_train=res(30, 25)),
        "small gain": dict(candidate_test=res(1.2, 1.0)),
    }
    for label, change in cases.items():
        assert not nr.decide(**{**base, **change})["apply"], label
    assert nr.decide(**{**base, "last_applied_at": NOW - timedelta(days=4)})["apply"]


def test_refine_never_touches_news_agents():
    out = nr.refine_agent(None, AGENTS_BY_NAME["news_sentiment_asx"], None)
    assert out["applied"] is False and out["reason"] == "strategy not tunable"


def test_refine_does_not_write_when_live(monkeypatch):
    class Store:
        saved = False
        def get_strategy_override(self, name): return None
        def save_strategy_override(self, *a, **k): Store.saved = True

    import genetic_optimize as go
    monkeypatch.setattr(go, "fetch_full_history", lambda agent: {s: __import__("data_feed").get_synthetic_ohlcv(s, 4400, seed=1) for s in agent.symbols})
    monkeypatch.setattr(go, "run_genetic_search", lambda *a, **k: {"params": NEW, "result": res(6, 5)})
    monkeypatch.setattr(go, "evaluate", lambda agent, data, fam, params: res(4, 3.0) if params == NEW else res(1, 0.5))
    monkeypatch.setattr(nr, "PAPER_TRADING", False)
    out = nr.refine_agent(Store(), AGENTS_BY_NAME["crypto_store_of_value"], None)
    assert out["applied"] is False and "live" in out["reason"] and not Store.saved

    monkeypatch.setattr(nr, "PAPER_TRADING", True)
    out = nr.refine_agent(Store(), AGENTS_BY_NAME["crypto_store_of_value"], None)
    assert out["applied"] is True and Store.saved


# --- data + report -------------------------------------------------------

def test_snapshot_and_report():
    rows = [
        {"agent_name": "crypto_store_of_value", "cash": "60", "positions": '{"BTC/USDT": 0.001}',
         "market_snapshot": {"BTC/USDT": {"price": 50000}}, "paused": False,
         "updated_at": (NOW - timedelta(minutes=10)).isoformat()},
        {"agent_name": "asx_bluechip_steady", "cash": 100, "positions": {}, "market_snapshot": {},
         "paused": True, "updated_at": (NOW - timedelta(hours=5)).isoformat()},
    ]
    trades = [{"agent_name": "crypto_store_of_value"}] * 3
    agents = nr.agent_snapshot(rows, trades, now=NOW)
    btc = next(a for a in agents if a["agent"] == "crypto_store_of_value")
    assert btc["equity"] == 110.0 and btc["return_pct"] == 10.0 and btc["trades_24h"] == 3

    rep = nr.build_report("success", agents, [{"agent": "x", "applied": True, "candidate_params": NEW}], [])
    assert rep["section"] == "rade" and rep["status"] == "warn"  # paused + stale tick
    assert any("ticks stopped" in n for n in rep["needs_you"])
    assert "refined x" in rep["summary"]

    rep = nr.build_report("failure", [], [{"agent": "y", "error": "could not save override: relation agent_overrides does not exist"}], [])
    assert rep["status"] == "fail"
    assert any("tests failure" in n for n in rep["needs_you"])
    assert any("agent_overrides SQL" in n for n in rep["needs_you"])
