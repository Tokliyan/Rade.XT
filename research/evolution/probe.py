"""Probe free, keyless data sources from the runner: speed, coverage, history start dates."""
import json, time, sys, concurrent.futures as cf
import requests
import pandas as pd

UA = {"User-Agent": "RadeXT-research/1.0 (student research project; https://github.com/Tokliyan/Rade.XT)"}
API = "https://en.wikipedia.org/w/api.php"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def title(d):
    return f"Portal:Current events/{d.year} {MONTHS[d.month-1]} {d.day}"


def pit(d):
    """page as it stood at 00:00 UTC the day AFTER d"""
    t0 = time.time()
    nxt = (d + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    r = requests.get(API, params={"action": "query", "prop": "revisions", "rvprop": "content|timestamp", "rvslots": "main",
                                  "rvlimit": 1, "rvstart": nxt, "rvdir": "older", "titles": title(d), "format": "json",
                                  "formatversion": 2}, headers=UA, timeout=30)
    j = r.json()
    p = j["query"]["pages"][0]
    if p.get("missing") or "revisions" not in p:
        return None, time.time() - t0, r.status_code
    rev = p["revisions"][0]
    return (rev["timestamp"], len(rev["slots"]["main"]["content"])), time.time() - t0, r.status_code


def latest_batch(ds):
    t0 = time.time()
    r = requests.get(API, params={"action": "query", "prop": "revisions", "rvprop": "content|timestamp", "rvslots": "main",
                                  "titles": "|".join(title(d) for d in ds), "format": "json", "formatversion": 2},
                     headers=UA, timeout=60)
    j = r.json()
    n = sum(1 for p in j["query"]["pages"] if "revisions" in p)
    sz = sum(len(p["revisions"][0]["slots"]["main"]["content"]) for p in j["query"]["pages"] if "revisions" in p)
    return n, sz, time.time() - t0, r.status_code, j.get("continue")


def wiki():
    print("== Wikipedia point-in-time sample")
    for d in ["2001-09-11", "2003-03-20", "2004-06-01", "2005-07-07", "2008-09-15", "2012-06-01", "2015-03-03", "2020-03-16", "2024-06-03", "2026-11-01"]:
        try:
            v, dt, sc = pit(pd.Timestamp(d))
            print(f"  {d}: {v}  {dt:.2f}s http {sc}")
        except Exception as e:
            print(f"  {d}: ERROR {e}")
    print("== Wikipedia speed, 48 point-in-time requests, 6 workers")
    days = pd.date_range("2010-01-01", periods=48)
    t0 = time.time()
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda d: pit(d)[1:], days))
    tot = time.time() - t0
    print(f"  {tot:.1f}s total -> {48/tot:.1f} req/s; slowest {max(r[0] for r in res):.2f}s; statuses {sorted(set(r[1] for r in res))}")
    print("== Wikipedia speed, 8 workers, 96 requests")
    days = pd.date_range("2016-01-01", periods=96)
    t0 = time.time()
    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda d: pit(d)[1:], days))
    tot = time.time() - t0
    print(f"  {tot:.1f}s total -> {96/tot:.1f} req/s; statuses {sorted(set(r[1] for r in res))}")
    print("== Wikipedia latest-version batch of 50 titles")
    ds = pd.date_range("2018-03-01", periods=50)
    try:
        print("  ", latest_batch(ds))
    except Exception as e:
        print("  ERROR", e)
    print("== existence by year (1 sample per year, PIT)")
    for y in range(2001, 2027):
        d = pd.Timestamp(f"{y}-05-15")
        try:
            v, dt, sc = pit(d)
            print(f"  {y}: {v}")
        except Exception as e:
            print(f"  {y}: ERROR {e}")


TICKERS = {
    "ASX200": "^AXJO", "SP500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI", "RUSSELL2000": "^RUT", "NIKKEI": "^N225",
    "FTSE": "^FTSE", "DAX": "^GDAXI", "CAC": "^FCHI", "HANGSENG": "^HSI", "KOSPI": "^KS11", "TSX": "^GSPTSE",
    "BOVESPA": "^BVSP", "SENSEX": "^BSESN", "SHANGHAI": "000001.SS",
    "XLE": "XLE", "XLF": "XLF", "XLK": "XLK", "XLV": "XLV", "XLY": "XLY", "XLP": "XLP", "XLI": "XLI", "XLU": "XLU", "XLB": "XLB",
    "EWA": "EWA", "EWJ": "EWJ", "EWZ": "EWZ", "EWG": "EWG", "EWU": "EWU", "EWH": "EWH", "EWY": "EWY", "EWT": "EWT", "EWC": "EWC", "EWW": "EWW", "FXI": "FXI",
    "GOLD": "GC=F", "SILVER": "SI=F", "OIL": "CL=F", "COPPER": "HG=F", "NATGAS": "NG=F",
    "TLT": "TLT", "IEF": "IEF", "LQD": "LQD", "HYG": "HYG", "VNQ": "VNQ",
    "AUDUSD": "AUDUSD=X", "EURUSD": "EURUSD=X", "USDJPY": "JPY=X", "GBPUSD": "GBPUSD=X",
    "BTC": "BTC-USD", "ETH": "ETH-USD",
    "VIX": "^VIX", "US10Y": "^TNX", "US5Y": "^FVX", "US13W": "^IRX",
}


def yf_probe():
    import yfinance as yf
    print("== yfinance history start dates")
    t0 = time.time()
    d = yf.download(list(TICKERS.values()), start="1993-01-01", progress=False, auto_adjust=True, group_by="column", threads=True)
    print(f"  bulk download {time.time()-t0:.0f}s, shape {d['Close'].shape}")
    c = d["Close"]
    for name, tk in TICKERS.items():
        if tk in c.columns:
            s = c[tk].dropna()
            print(f"  {name:12s} {tk:10s} rows {len(s):5d}  {s.index[0].date() if len(s) else '-'} -> {s.index[-1].date() if len(s) else '-'}")
        else:
            print(f"  {name:12s} {tk:10s} MISSING")




def speed():
    """Latency and status codes for point-in-time page requests at different worker counts and eras."""
    import collections
    for label, start in [("2005 (pages mostly absent)", "2005-03-01"), ("2012", "2012-03-01"), ("2023", "2023-03-01")]:
        for workers in (3, 6):
            days = pd.date_range(start, periods=90)
            stat = collections.Counter()
            lat = []

            def one(d):
                nxt = (d + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
                t0 = time.time()
                try:
                    r = requests.get(API, params={"action": "query", "prop": "revisions", "rvprop": "content|timestamp", "rvslots": "main", "rvlimit": 1,
                                                  "rvstart": nxt, "rvdir": "older", "titles": title(d), "format": "json", "formatversion": 2}, headers=UA, timeout=30)
                    ok = r.text.startswith("{")
                    stat[(r.status_code, ok)] += 1
                    if r.status_code == 429:
                        stat["retry-after:" + str(r.headers.get("Retry-After"))] += 1
                except Exception as e:
                    stat["exc:" + type(e).__name__] += 1
                lat.append(time.time() - t0)

            t0 = time.time()
            with cf.ThreadPoolExecutor(workers) as ex:
                list(ex.map(one, days))
            tot = time.time() - t0
            lat.sort()
            print(f"  {label:28s} workers {workers}: {90/tot:5.1f} req/s, median latency {lat[len(lat)//2]:.2f}s, p90 {lat[int(len(lat)*.9)]:.2f}s, {dict(stat)}", flush=True)
            time.sleep(5)


def peek():
    for d in ["2015-03-03", "2019-06-11", "2023-02-06"]:
        d = pd.Timestamp(d)
        t = title(d)
        r = requests.get(API, params={"action": "query", "prop": "revisions", "rvprop": "content|timestamp|size", "rvslots": "main", "titles": t, "format": "json", "formatversion": 2}, headers=UA, timeout=30).json()
        pg = r["query"]["pages"][0]
        rev = pg["revisions"][0] if "revisions" in pg else None
        print("== LATEST", t, "missing" if pg.get("missing") else "", rev["timestamp"] if rev else "", rev["size"] if rev else "")
        if rev:
            print(rev["slots"]["main"]["content"][:900].replace("\n", " | "))
        v, dt, sc = pit(d)
        nxt = (d + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        r = requests.get(API, params={"action": "query", "prop": "revisions", "rvprop": "content|timestamp|size", "rvslots": "main", "rvlimit": 1, "rvstart": nxt, "rvdir": "older", "titles": t, "format": "json", "formatversion": 2}, headers=UA, timeout=30).json()
        pg = r["query"]["pages"][0]
        if "revisions" in pg:
            rev = pg["revisions"][0]
            print("== PIT", rev["timestamp"], rev["size"])
            print(rev["slots"]["main"]["content"][:900].replace("\n", " | "))
        time.sleep(3)


if __name__ == "__main__":
    for part in sys.argv[1:] or ["wiki", "yf"]:
        try:
            {"wiki": wiki, "yf": yf_probe, "speed": lambda: speed(), "peek": peek}[part]()
        except Exception as e:
            print("PROBE FAILED", part, repr(e))
