"""
Strategy parameters as plain dicts — the bridge between the nightly
refine step (which finds new parameters) and the live agents (which have
to trade with them).

The nightly review never edits config.py. It writes a parameter override
for an agent into the agent_overrides table, and main.py rebuilds that
agent's strategy from it at the start of every tick. Deleting the row
puts the agent straight back on its config.py defaults.

Every override is checked against hard bounds here before it's used, so a
bad row in the database can't produce a nonsense strategy (a 1-candle
moving average, an RSI that buys at 90). An out-of-bounds or wrong-shape
override is ignored, not "clamped into shape", and the agent keeps its
defaults.
"""

from typing import Optional

from strategy import SmaCrossStrategy, RsiMeanReversionStrategy

BOUNDS = {
    "sma": {"fast_period": (3, 25), "slow_period": (8, 80)},
    "rsi": {"period": (7, 25), "oversold": (10.0, 40.0), "overbought": (60.0, 90.0)},
}


def family_of(strategy) -> Optional[str]:
    if isinstance(strategy, SmaCrossStrategy):
        return "sma"
    if isinstance(strategy, RsiMeanReversionStrategy):
        return "rsi"
    return None  # news-sentiment and anything else: not tunable


def params_of(strategy) -> Optional[dict]:
    fam = family_of(strategy)
    if fam == "sma":
        return {"fast_period": strategy.fast_period, "slow_period": strategy.slow_period}
    if fam == "rsi":
        return {"period": strategy.period, "oversold": float(strategy.oversold), "overbought": float(strategy.overbought)}
    return None


def validate(family: str, params) -> bool:
    if family not in BOUNDS or not isinstance(params, dict):
        return False
    bounds = BOUNDS[family]
    if set(params) != set(bounds):
        return False
    for key, (lo, hi) in bounds.items():
        v = params[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return False
        if not (lo <= v <= hi):
            return False
    if family == "sma" and params["slow_period"] < params["fast_period"] + 5:
        return False
    if family == "rsi" and params["oversold"] >= params["overbought"]:
        return False
    return True


def build(family: str, params: dict):
    if family == "sma":
        return SmaCrossStrategy(fast_period=int(params["fast_period"]), slow_period=int(params["slow_period"]))
    if family == "rsi":
        return RsiMeanReversionStrategy(
            period=int(params["period"]), oversold=float(params["oversold"]), overbought=float(params["overbought"])
        )
    raise ValueError(f"unknown strategy family {family!r}")


def strategy_with_override(default_strategy, override: Optional[dict]):
    """Returns (strategy, source) where source is 'override' or 'config'."""
    fam = family_of(default_strategy)
    if not override or fam is None:
        return default_strategy, "config"
    if override.get("family") != fam or not validate(fam, override.get("params")):
        return default_strategy, "config"
    return build(fam, override["params"]), "override"
