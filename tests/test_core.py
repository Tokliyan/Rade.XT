"""Core trading logic — no network, no Supabase. Synthetic data only."""
import pandas as pd
import pytest

from backtester import run_backtest
from broker import PaperBroker
from config import AGENTS, PAPER_TRADING, RISK_PROFILES
from data_feed import get_synthetic_ohlcv
from genetic_optimize import _EffectiveConfig
from risk_manager import RiskManager
from strategy import RsiMeanReversionStrategy, SmaCrossStrategy


def _df(closes):
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="h")
    return pd.DataFrame({"open": closes, "high": closes, "low": closes, "close": closes, "volume": 1.0}, index=idx)


def test_paper_trading_switch_is_on():
    # The whole project's safety assumption. Flipping this should be a
    # deliberate act that also makes this test fail on purpose.
    assert PAPER_TRADING is True


def test_agent_names_unique_and_profiles_capped():
    names = [a.name for a in AGENTS]
    assert len(names) == len(set(names))
    for p in RISK_PROFILES.values():
        cap = p["max_daily_loss_pct"]
        assert cap is None or 0 < cap <= 0.25  # a circuit breaker always exists


def test_sma_cross_signals():
    s = SmaCrossStrategy(fast_period=2, slow_period=4)
    assert s.generate_signal(_df([10, 10])) == "HOLD"  # not enough data
    assert s.generate_signal(_df([10, 10, 10, 10, 10, 9, 8, 13])) == "BUY"
    assert s.generate_signal(_df([10, 10, 10, 10, 10, 11, 12, 7])) == "SELL"


def test_rsi_signals():
    s = RsiMeanReversionStrategy(period=3, oversold=30, overbought=70)
    assert s.generate_signal(_df([10, 11, 10, 9, 8, 7])) == "BUY"
    assert s.generate_signal(_df([10, 11, 12, 13, 12.9, 14, 15])) == "SELL"


def test_risk_manager_levels_and_sizing():
    r = RiskManager(0.02, 0.03, 0.06)
    assert r.stop_loss_price(100, "BUY") == pytest.approx(97)
    assert r.take_profit_price(100, "BUY") == pytest.approx(106)
    qty = r.position_size(1000, 100)
    assert qty > 0 and qty * 100 <= 1000  # never sizes beyond equity


def test_paper_broker_round_trip_charges_fees(tmp_path):
    b = PaperBroker(starting_balance=100.0, fee_pct=0.001, log_path=str(tmp_path / "log.csv"))
    b.execute(pd.Timestamp("2026-01-01"), "X", "BUY", 0.5, 100.0)
    b.execute(pd.Timestamp("2026-01-02"), "X", "SELL", 0.5, 100.0)
    assert b.positions.get("X", 0.0) == pytest.approx(0.0)
    assert b.cash < 100.0  # flat price, so fees are the only change


def test_backtest_runs_and_reports_sane_numbers(tmp_path):
    df = get_synthetic_ohlcv("TEST", periods=400, seed=7)
    cfg = _EffectiveConfig(SmaCrossStrategy(5, 20), 100.0, 0.001, 0.02, 0.03, 0.06)
    res = run_backtest(df, cfg, "TEST", log_path=str(tmp_path / "bt.csv"))
    assert res.starting_equity == 100.0
    assert res.final_equity > 0
    assert 0 <= res.max_drawdown_pct <= 100
