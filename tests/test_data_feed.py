"""The data feed falls back to a US-friendly exchange when Binance is blocked (HTTP 451 on GitHub runners)."""
import sys
import types

import pytest

import data_feed


def _fake_ccxt(behaviour):
    """behaviour: {(exchange, symbol): candles | Exception}. Records every call."""
    calls = []
    mod = types.ModuleType("ccxt")

    def make(name):
        class Ex:
            def __init__(self, opts=None):
                pass

            def fetch_ohlcv(self, symbol, timeframe="1h", limit=500, since=None):
                calls.append((name, symbol))
                out = behaviour.get((name, symbol), RuntimeError(f"{name} {symbol} not listed"))
                if isinstance(out, Exception):
                    raise out
                return out

            def milliseconds(self):
                return 10_000_000

            def parse_timeframe(self, tf):
                return 3600
        return Ex

    for n in ("binance", "kraken", "coinbase"):
        setattr(mod, n, make(n))
    return mod, calls


CANDLES = [[i * 3600_000, 1, 2, 0.5, 1.5, 10] for i in range(5)]
BLOCKED = RuntimeError('binance GET exchangeInfo 451 {"msg": "Service unavailable from a restricted location"}')


@pytest.fixture
def ccxt_with(monkeypatch):
    def install(behaviour):
        mod, calls = _fake_ccxt(behaviour)
        monkeypatch.setitem(sys.modules, "ccxt", mod)
        return calls
    return install


def test_configured_exchange_used_when_it_works(ccxt_with):
    calls = ccxt_with({("binance", "BTC/USDT"): CANDLES})
    df = data_feed.get_live_ohlcv("binance", "BTC/USDT", "1h")
    assert len(df) == 5
    assert calls == [("binance", "BTC/USDT")]


def test_falls_back_when_binance_blocked(ccxt_with):
    calls = ccxt_with({("binance", "BTC/USDT"): BLOCKED, ("kraken", "BTC/USDT"): CANDLES})
    df = data_feed.get_live_ohlcv("binance", "BTC/USDT", "1h")
    assert len(df) == 5
    assert calls[0] == ("binance", "BTC/USDT") and calls[-1] == ("kraken", "BTC/USDT")


def test_tries_usd_pair_when_usdt_pair_not_listed(ccxt_with):
    calls = ccxt_with({("binance", "PAXG/USDT"): BLOCKED, ("kraken", "PAXG/USD"): CANDLES})
    df = data_feed.get_live_ohlcv("binance", "PAXG/USDT", "1h")
    assert len(df) == 5
    assert ("kraken", "PAXG/USD") in calls


def test_error_names_every_attempt_when_all_fail(ccxt_with):
    ccxt_with({("binance", "BTC/USDT"): BLOCKED})
    with pytest.raises(RuntimeError) as e:
        data_feed.get_live_ohlcv("binance", "BTC/USDT", "1h")
    msg = str(e.value)
    assert "binance BTC/USDT" in msg and "kraken" in msg and "coinbase" in msg


def test_empty_candles_count_as_a_failure(ccxt_with):
    ccxt_with({("binance", "BTC/USDT"): [], ("kraken", "BTC/USDT"): CANDLES})
    assert len(data_feed.get_live_ohlcv("binance", "BTC/USDT", "1h")) == 5


def test_paginated_also_falls_back(ccxt_with):
    ccxt_with({("binance", "BTC/USDT"): BLOCKED, ("kraken", "BTC/USDT"): CANDLES})
    df = data_feed.get_live_ohlcv_paginated("binance", "BTC/USDT", "1h", days=1)
    assert len(df) == 5
