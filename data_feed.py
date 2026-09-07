"""
Market data access.

get_live_ohlcv() pulls real candles via ccxt — this needs internet access
to the exchange itself (e.g. binance.com), so it only works wherever you
actually run the bot, not inside a sandboxed dev environment.

get_synthetic_ohlcv() generates a fake-but-plausible price series so you
can develop and backtest the strategy logic without hitting any API.
"""

import time
import numpy as np
import pandas as pd


def get_live_ohlcv(exchange_id: str, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    import ccxt  # imported here so this file still loads without ccxt configured

    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df.set_index("timestamp")


def get_live_ohlcv_stock(ticker: str, interval: str = "1h", period: str = "1mo") -> pd.DataFrame:
    """
    Free stock candles via yfinance — an unofficial wrapper around Yahoo
    Finance, no account or API key needed. Works for ASX tickers using the
    ".AX" suffix (e.g. "CBA.AX") as well as US tickers.

    Two honest limitations: yfinance is unofficial, so it's occasionally
    flaky (Yahoo changes things without notice now and then). And outside
    market hours (ASX: ~10am-4pm AEST weekdays) this just returns whatever
    the last available bar was — not an error, just no new data, so the
    strategy will naturally see nothing has changed and do nothing until
    the market's open again.
    """
    import yfinance as yf

    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data returned for {ticker} — check the ticker is correct and the market has traded recently.")
    df.columns = [c.lower() for c in df.columns]
    return df[["open", "high", "low", "close", "volume"]]


def get_synthetic_ohlcv(symbol: str, periods: int = 1000, seed: int | None = None,
                         start_price: float = 100.0, freq: str = "h") -> pd.DataFrame:
    """
    Generates a random-walk-with-drift price series for backtesting the
    plumbing. This is NOT real market data and has no predictive value —
    it exists purely so the bot's logic can be exercised end to end.
    """
    rng = np.random.default_rng(seed if seed is not None else abs(hash(symbol)) % (2**32))
    returns = rng.normal(loc=0.0002, scale=0.01, size=periods)
    price = start_price * np.exp(np.cumsum(returns))

    high = price * (1 + np.abs(rng.normal(0, 0.003, periods)))
    low = price * (1 - np.abs(rng.normal(0, 0.003, periods)))
    open_ = price * (1 + rng.normal(0, 0.001, periods))
    volume = rng.uniform(100, 1000, periods)

    idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=periods, freq=freq)
    df = pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": price, "volume": volume
    }, index=idx)
    return df
