"""
Market data for the evolution research run.

Real data: daily closes from Yahoo Finance (yfinance) for a fixed, survivor-free
basket of indices / commodities / FX / bonds / crypto. Individual stocks are
deliberately NOT used: Yahoo only keeps companies that still exist, which would
flatter every bot (survivorship bias).

Synthetic data (for validating the machinery without real markets):
  - random:  pure random walks, zero predictability. A sound engine must find
             NOTHING here. If it "finds" money here, it is fooling itself.
  - planted: half the assets have persistent up/down regimes (a real, findable
             trend edge). A sound engine should find this one.
"""
import numpy as np
import pandas as pd

UNIVERSE = {
    "ASX200": "^AXJO", "SP500": "^GSPC", "NASDAQ": "^IXIC", "NIKKEI": "^N225",
    "FTSE": "^FTSE", "DAX": "^GDAXI", "HANGSENG": "^HSI",
    "GOLD": "GC=F", "OIL": "CL=F", "AUDUSD": "AUDUSD=X", "BONDS": "TLT", "BTC": "BTC-USD",
}


def fetch_real(start="1993-01-01", cache=None):
    import yfinance as yf
    cols = {}
    for name, tkr in UNIVERSE.items():
        try:
            d = yf.download(tkr, start=start, progress=False, auto_adjust=True)
            s = d["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s = s.dropna()
            if len(s) < 500:
                print(f"[data] {name} ({tkr}): only {len(s)} rows, skipped")
                continue
            s.index = pd.DatetimeIndex(s.index).tz_localize(None)
            cols[name] = s
            print(f"[data] {name:9s} {tkr:10s} {s.index[0].date()} -> {s.index[-1].date()}  {len(s)} rows")
        except Exception as e:
            print(f"[data] {name} ({tkr}) failed: {e}")
    if not cols:
        raise RuntimeError("no market data could be downloaded")
    df = pd.DataFrame(cols).sort_index()
    df = df[~df.index.duplicated()]
    if cache:
        df.to_csv(cache)
    return df


def load_cached(path):
    return pd.read_csv(path, index_col=0, parse_dates=True)


def _calendar(start="1993-01-01", end="2026-11-20"):
    return pd.bdate_range(start, end)


def synthetic(kind="random", seed=0, n_assets=12, start="1993-01-01", end="2026-11-20"):
    rng = np.random.default_rng(seed)
    idx = _calendar(start, end)
    T = len(idx)
    out = {}
    for a in range(n_assets):
        vol = rng.uniform(0.008, 0.016)          # daily vol
        noise = rng.standard_normal(T) * vol
        if kind == "planted" and a < n_assets // 2:
            # persistent regimes: flip every ~125 days on average, drift +/-0.2%/day (~50%/yr): a strong, deliberately findable edge
            flips = rng.random(T) < 0.008
            regime = np.empty(T)
            cur = 1.0
            for t in range(T):
                if flips[t]:
                    cur = -cur
                regime[t] = cur
            r = regime * 0.002 + noise
        else:
            r = noise                              # zero drift, no structure
        out[f"A{a}"] = 100 * np.exp(np.cumsum(r))
    return pd.DataFrame(out, index=idx)


# ---------------------------------------------------------------------------- v2: 45 markets + macro
UNIVERSE2 = {
    # equity indices
    "ASX200": "^AXJO", "SP500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI", "RUSSELL2000": "^RUT", "NIKKEI": "^N225",
    "FTSE": "^FTSE", "DAX": "^GDAXI", "CAC": "^FCHI", "HANGSENG": "^HSI", "KOSPI": "^KS11", "TSX": "^GSPTSE",
    "BOVESPA": "^BVSP", "SHANGHAI": "000001.SS",
    # US sectors
    "XLE": "XLE", "XLF": "XLF", "XLK": "XLK", "XLV": "XLV", "XLY": "XLY", "XLP": "XLP", "XLI": "XLI", "XLU": "XLU", "XLB": "XLB",
    # country ETFs (USD)
    "EWA": "EWA", "EWZ": "EWZ", "EWY": "EWY", "EWT": "EWT", "EWW": "EWW", "FXI": "FXI",
    # commodities / bonds / property / FX / crypto
    "GOLD": "GC=F", "SILVER": "SI=F", "OIL": "CL=F", "COPPER": "HG=F", "NATGAS": "NG=F",
    "TLT": "TLT", "IEF": "IEF", "LQD": "LQD", "HYG": "HYG", "VNQ": "VNQ",
    "AUDUSD": "AUDUSD=X", "EURUSD": "EURUSD=X", "USDJPY": "JPY=X", "GBPUSD": "GBPUSD=X",
    "BTC": "BTC-USD", "ETH": "ETH-USD",
}
MACRO = {"VIX": "^VIX", "US10Y": "^TNX", "US13W": "^IRX"}
EQUITY = {"ASX200", "SP500", "NASDAQ", "DOW", "RUSSELL2000", "NIKKEI", "FTSE", "DAX", "CAC", "HANGSENG", "KOSPI", "TSX", "BOVESPA",
          "SHANGHAI", "XLE", "XLF", "XLK", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "EWA", "EWZ", "EWY", "EWT", "EWW", "FXI"}


def fetch_real2(start="1993-01-01"):
    """One bulk Yahoo download: tradable markets + macro series (VIX, 10-year and 13-week yields)."""
    import yfinance as yf
    tick = {**UNIVERSE2, **MACRO}
    d = yf.download(list(tick.values()), start=start, progress=False, auto_adjust=True, group_by="column", threads=True)["Close"]
    d.index = pd.DatetimeIndex(d.index).tz_localize(None)
    d = d[~d.index.duplicated()].sort_index()
    cols, macro = {}, {}
    for name, tk in tick.items():
        if tk not in d.columns:
            print(f"[data] {name} ({tk}) missing")
            continue
        s = d[tk].dropna()
        if len(s) < 1500 and name not in ("ETH", "HYG"):
            print(f"[data] {name} ({tk}): only {len(s)} rows, skipped")
            continue
        (macro if name in MACRO else cols)[name] = s
        print(f"[data] {name:12s} {tk:10s} {s.index[0].date()} -> {s.index[-1].date()}  {len(s)} rows")
    prices = pd.DataFrame(cols).sort_index()
    return prices, pd.DataFrame(macro).sort_index()


def load_news(path):
    import os
    if path and os.path.exists(path):
        n = pd.read_csv(path, parse_dates=["date"])
        print(f"[news] {int((n.ok == 1).sum())} days with a page out of {len(n)} cached ({n.date.min().date()} -> {n.date.max().date()})")
        return n
    print("[news] no news file found; running without news")
    return None
