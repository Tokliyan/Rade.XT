"""
Genetic parameter search — evolves strategy parameters (SMA windows, RSI
thresholds) against real historical data, then checks whether what it
found actually generalizes.

THE CORE SAFEGUARD, and the entire reason this file exists rather than
just optimizing against all 6 months at once: the data gets SPLIT before
any searching happens.
  - TRAIN (first ~4 months): the genetic search only ever sees this. It
    evolves parameters purely to perform well here.
  - TEST (final ~2 months): completely held out. The winning parameters
    get run against it exactly ONCE, after evolution is finished — never
    used to influence the search itself.

Why this matters: with enough variants and enough generations, a genetic
search WILL eventually find parameters that look great on any fixed
dataset — that's not the same as finding a real edge, it's finding the
specific noise in that specific stretch of history (overfitting). The
train/test split is the only thing that can catch this: if the winning
parameters perform close to as well on the untouched test months as they
did on training, that's real signal. If they fall apart the moment they
see new data, that IS the overfitting, made visible on purpose instead
of hidden.

Uses the exact same PaperBroker, RiskManager, and run_backtest() as the
live agents and the 6-month replay — the only thing that changes here is
which parameters go into the strategy, never how a trade is priced,
sized, or fee'd. No real money, no real broker, same paper-only spirit
as everything else in this project.

Only the 3 price-pattern agents are eligible — the 2 news-sentiment
agents read live news, so there's no historical version of "today's
news" to search over. Same reason they're excluded everywhere else.

Usage:
    python genetic_optimize.py
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass

from config import AGENTS_BY_NAME
from data_feed import get_live_ohlcv_stock, get_live_ohlcv_paginated
from backtester import run_backtest
from strategy import SmaCrossStrategy, RsiMeanReversionStrategy

ELIGIBLE_AGENTS = ["asx_bluechip_steady", "asx_smallcap_growth", "crypto_store_of_value"]

REPLAY_MONTHS = 6
TRAIN_MONTHS = 4  # the search only ever sees this; the rest becomes the held-out test

POPULATION_SIZE = 12
GENERATIONS = 20
SURVIVORS = 4  # top performers kept unchanged each generation (elitism)
DRAWDOWN_PENALTY = 0.5  # fitness = return_pct - DRAWDOWN_PENALTY * max_drawdown_pct —
                         # without this, evolution drifts toward reckless high-variance
                         # parameters that got a lucky big number, not genuinely better ones
RANDOM_SEED = 42  # fixed so a re-run is reproducible, not just "lucky again"


@dataclass
class _EffectiveConfig:
    """Mimics an AgentConfig with one candidate strategy plugged in —
    run_backtest() only reads these specific fields."""
    strategy: object
    starting_balance: float
    fee_pct: float
    risk_per_trade: float
    stop_loss_pct: float
    take_profit_pct: float


def fetch_full_history(agent) -> dict:
    data = {}
    for symbol in agent.symbols:
        if agent.data_source == "stock":
            data[symbol] = get_live_ohlcv_stock(symbol, interval=agent.timeframe, period="6mo")
        else:
            data[symbol] = get_live_ohlcv_paginated(agent.exchange_id, symbol, agent.timeframe, days=REPLAY_MONTHS * 30)
    return data


def split_train_test(df: pd.DataFrame):
    if df.empty:
        return df, df
    cutoff = df.index[0] + pd.Timedelta(days=TRAIN_MONTHS * 30)
    return df[df.index < cutoff], df[df.index >= cutoff]


# --- parameter spaces + mutation, one pair of functions per strategy family ---

def random_sma_params(rng):
    fast = int(rng.integers(3, 26))
    slow = int(rng.integers(fast + 5, 81))
    return {"fast_period": fast, "slow_period": slow}


def mutate_sma_params(params, rng):
    fast = int(np.clip(params["fast_period"] + rng.integers(-3, 4), 3, 25))
    slow = int(np.clip(params["slow_period"] + rng.integers(-8, 9), fast + 5, 80))
    return {"fast_period": fast, "slow_period": slow}


def random_rsi_params(rng):
    return {
        "period": int(rng.integers(7, 26)),
        "oversold": round(float(rng.uniform(15, 35)), 1),
        "overbought": round(float(rng.uniform(65, 85)), 1),
    }


def mutate_rsi_params(params, rng):
    return {
        "period": int(np.clip(params["period"] + rng.integers(-3, 4), 7, 25)),
        "oversold": round(float(np.clip(params["oversold"] + rng.uniform(-5, 5), 10, 40)), 1),
        "overbought": round(float(np.clip(params["overbought"] + rng.uniform(-5, 5), 60, 90)), 1),
    }


STRATEGY_FAMILIES = {
    SmaCrossStrategy: {
        "random": random_sma_params,
        "mutate": mutate_sma_params,
        "build": lambda p: SmaCrossStrategy(fast_period=p["fast_period"], slow_period=p["slow_period"]),
    },
    RsiMeanReversionStrategy: {
        "random": random_rsi_params,
        "mutate": mutate_rsi_params,
        "build": lambda p: RsiMeanReversionStrategy(period=p["period"], oversold=p["oversold"], overbought=p["overbought"]),
    },
}


def evaluate(agent, symbol_data: dict, family, params) -> dict:
    """Runs one parameter set across all of this agent's symbols on the
    given data, combining into one score — same combining approach as
    six_month_replay.py."""
    strategy = family["build"](params)
    symbols = list(symbol_data.keys())
    per_symbol_balance = agent.starting_balance / len(symbols)

    combined_final = 0.0
    combined_start = 0.0
    total_trades = 0
    worst_dd = 0.0

    for symbol, df in symbol_data.items():
        if len(df) < 40:
            continue
        eff = _EffectiveConfig(
            strategy=strategy,
            starting_balance=per_symbol_balance,
            fee_pct=agent.fee_pct,
            risk_per_trade=agent.risk_per_trade,
            stop_loss_pct=agent.stop_loss_pct,
            take_profit_pct=agent.take_profit_pct,
        )
        result = run_backtest(df, eff, symbol, log_path=f"/tmp/genetic_{agent.name}_{symbol.replace('/', '_')}.csv")
        combined_final += result.final_equity
        combined_start += result.starting_equity
        total_trades += result.num_trades
        worst_dd = max(worst_dd, result.max_drawdown_pct)

    if combined_start == 0:
        return {"return_pct": 0.0, "max_drawdown_pct": 0.0, "trades": 0, "fitness": -999.0}

    return_pct = (combined_final / combined_start - 1) * 100
    fitness = return_pct - DRAWDOWN_PENALTY * worst_dd
    return {
        "return_pct": round(return_pct, 2),
        "max_drawdown_pct": round(worst_dd, 2),
        "trades": total_trades,
        "fitness": round(fitness, 3),
    }


def run_genetic_search(agent, train_data: dict, family, rng, generations: int = GENERATIONS, seed_params=None) -> dict:
    population = [family["random"](rng) for _ in range(POPULATION_SIZE)]
    if seed_params is not None:
        population[0] = dict(seed_params)  # current params compete too, so "no change" can win
    best_overall = None

    for gen in range(generations):
        scored = [(evaluate(agent, train_data, family, p), p) for p in population]
        scored.sort(key=lambda x: x[0]["fitness"], reverse=True)

        gen_best_result, gen_best_params = scored[0]
        if best_overall is None or gen_best_result["fitness"] > best_overall["result"]["fitness"]:
            best_overall = {"params": gen_best_params, "result": gen_best_result}

        print(f"    gen {gen+1:2d}/{generations}: best fitness={gen_best_result['fitness']:+.2f} "
              f"(return={gen_best_result['return_pct']:+.2f}%, dd={gen_best_result['max_drawdown_pct']:.2f}%) "
              f"params={gen_best_params}")

        survivors = [p for _, p in scored[:SURVIVORS]]
        next_population = list(survivors)  # elitism: best carries forward unchanged
        while len(next_population) < POPULATION_SIZE:
            parent = survivors[rng.integers(0, len(survivors))]
            child = family["random"](rng) if rng.random() < 0.1 else family["mutate"](parent, rng)
            next_population.append(child)
        population = next_population

    return best_overall


def main():
    rng = np.random.default_rng(RANDOM_SEED)
    report_rows = []

    for agent_name in ELIGIBLE_AGENTS:
        agent = AGENTS_BY_NAME[agent_name]
        family = STRATEGY_FAMILIES.get(type(agent.strategy))
        if family is None:
            print(f"[{agent.name}] no known parameter family for {type(agent.strategy).__name__} — skipping")
            continue

        print(f"\n=== {agent.name} ({type(agent.strategy).__name__}) ===")
        print(f"Fetching {REPLAY_MONTHS} months of real data for {agent.symbols}...")
        try:
            full_data = fetch_full_history(agent)
        except Exception as e:
            print(f"  FAILED to fetch history: {e}")
            continue

        train_data, test_data = {}, {}
        for symbol, df in full_data.items():
            tr, te = split_train_test(df)
            train_data[symbol], test_data[symbol] = tr, te
            print(f"  {symbol}: train {len(tr)} candles, test {len(te)} candles")

        print(f"  Evolving over {GENERATIONS} generations, population {POPULATION_SIZE}...")
        best = run_genetic_search(agent, train_data, family, rng)

        print(f"  Best on TRAINING data: {best['params']} -> "
              f"return={best['result']['return_pct']:+.2f}%, dd={best['result']['max_drawdown_pct']:.2f}%")

        # The actual point of this file: one honest look at data the search never saw.
        test_result = evaluate(agent, test_data, family, best["params"])
        print(f"  SAME params on HELD-OUT test data: "
              f"return={test_result['return_pct']:+.2f}%, dd={test_result['max_drawdown_pct']:.2f}%")

        gap = best["result"]["return_pct"] - test_result["return_pct"]
        verdict = "held up reasonably" if gap < 10 else "LIKELY OVERFIT - big gap between train and test"
        print(f"  Train-vs-test gap: {gap:+.2f} points -> {verdict}")

        report_rows.append({
            "agent": agent.name,
            "best_params": str(best["params"]),
            "train_return_pct": best["result"]["return_pct"],
            "train_max_drawdown_pct": best["result"]["max_drawdown_pct"],
            "test_return_pct": test_result["return_pct"],
            "test_max_drawdown_pct": test_result["max_drawdown_pct"],
            "train_test_gap": round(gap, 2),
            "verdict": verdict,
        })

    if not report_rows:
        print("\nNo results produced.")
        return

    df_report = pd.DataFrame(report_rows)
    print("\n" + "=" * 90)
    print("GENETIC SEARCH SUMMARY - trained on first 4 months, tested once on final ~2 (real data)")
    print("=" * 90)
    print(df_report.to_string(index=False))
    df_report.to_csv("genetic_optimize_results.csv", index=False)
    print("\nSaved: genetic_optimize_results.csv")


if __name__ == "__main__":
    main()
