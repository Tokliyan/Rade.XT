"""
Point-in-time daily news features from Wikipedia's "Portal:Current events" (free, no key).

Why this source: each day has its own page listing that day's major world events. Wikipedia keeps
every revision with a timestamp, so we can ask for the page EXACTLY as it stood at 00:00 UTC the next
day (revision-as-of). That is what a person could have read by the end of that day. Pages that were
created later (back-filled after the fact) simply do not exist at that moment and come back empty,
so hindsight cannot sneak in through back-filling.

Per day we keep only counts from a FIXED word list (written here, never tuned) per 1000 words.
No text is stored and no AI model reads it, so nothing "knows" what happens next.

  python news.py --start 2004-01-01 --minutes 9 --out data/news_counts.csv
Resumable: days already in the csv are skipped. Stops cleanly at the time budget.

Speed: Wikipedia rate-limits per-day point-in-time requests (about 4 per second sustained, so 8,000 days
would take ~35 minutes). So there are two modes:
  --mode pit    the exact page as of the end of each day (slow, pure)
  --mode batch  25 days per request, latest version of each page (fast, ~2 minutes)
  --mode audit  fetch the exact point-in-time page for a random sample of days and measure how much the fast
                version differs. The features are word-list densities, so later edits hardly move them, but we measure it.
"""
import argparse, concurrent.futures as cf, os, re, time
import pandas as pd
import requests

UA = {"User-Agent": "RadeXT-research/1.0 (student research project; https://github.com/Tokliyan/Rade.XT)"}
API = "https://en.wikipedia.org/w/api.php"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

LEX = {
    "neg": r"crash|collapse|crisis|recession|default|bankrupt\w*|plunge\w*|plummet\w*|slump\w*|sell-?off|panic|fears?|war|invasion|attack\w*|bomb\w*|killed|dead|deaths?|terror\w*|disaster|earthquake|explosion|shooting|coup|sanctions?|downgrade\w*|layoffs?|unemployment|strikes?|protests?|riots?|shutdown|outbreak|pandemic|epidemic|lockdown|bailout",
    "pos": r"rall(?:y|ies|ied)|records?|surge\w*|growth|recover\w*|boom\w*|agreement|deals?|ceasefire|peace|approved|breakthrough|cure|vaccine\w*|gains?|profits?|stimulus|rebound\w*|upgrade\w*",
    "conflict": r"war|invasion|invaded|airstrikes?|bomb\w*|missiles?|troops|military|shelling|offensive|insurgents?|rebels?|militants?",
    "fincrisis": r"crash|collapse\w*|bankrupt\w*|default\w*|bailout|recession|downgrade\w*|bank run|insolven\w*|credit crunch|financial crisis",
    "ratesinfl": r"interest rates?|inflation|central bank|federal reserve|rate (?:hike|cut)s?|reserve bank|monetary policy|bond yields?",
    "trade": r"tariffs?|trade war|sanctions?|embargo\w*|trade deal|export bans?",
    "energy": r"oil|opec|crude|natural gas|pipeline|refiner\w+|petroleum",
    "health": r"pandemic|outbreak|virus|epidemic|covid\w*|coronavirus|quarantine|lockdown|flu|ebola|sars",
    "disaster": r"earthquake|hurricane|tsunami|flood\w*|wildfires?|typhoon|cyclone|volcano|eruption",
}
PAT = {k: re.compile(r"\b(?:" + v + r")\b") for k, v in LEX.items()}
WORD = re.compile(r"[a-z']+")


def title(d):
    return f"Portal:Current events/{d.year} {MONTHS[d.month-1]} {d.day}"


def clean(txt):
    txt = re.sub(r"\{\{\s*Current events\s*\|[^{}]*?content\s*=", " ", txt, flags=re.I)   # newer pages wrap the body in a template: keep its text
    txt = re.sub(r"<ref[^>]*?/>", " ", txt)
    txt = re.sub(r"<ref[^>]*>.*?</ref>", " ", txt, flags=re.S)
    for _ in range(4):
        txt = re.sub(r"\{\{[^{}]*\}\}", " ", txt)
    txt = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", " ", txt, flags=re.I)
    txt = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", txt)
    txt = re.sub(r"\[\[([^\]]*)\]\]", r"\1", txt)
    txt = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", txt)
    txt = re.sub(r"https?://\S+", " ", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"(?m)^[;=].*$", " ", txt)           # section headings
    txt = re.sub(r"(?m)^\s*'''[^'\n]+'''\s*$", " ", txt)   # bold section headings
    return txt.replace("'''", "").replace("''", "").lower()


def score(txt):
    t = clean(txt)
    n = len(WORD.findall(t))
    if n < 30:
        return None
    row = {"words": n}
    for k, p in PAT.items():
        row[k] = len(p.findall(t)) * 1000.0 / n
    return row


_PAUSE = {"until": 0.0}      # shared by all workers: when Wikipedia says slow down, everybody waits


def fetch_day(d, tries=8):
    nxt = (d + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    params = {"action": "query", "prop": "revisions", "rvprop": "content|timestamp", "rvslots": "main", "rvlimit": 1,
              "rvstart": nxt, "rvdir": "older", "titles": title(d), "format": "json", "formatversion": 2, "maxlag": 5}
    for k in range(tries):
        try:
            w = _PAUSE["until"] - time.time()
            if w > 0:
                time.sleep(w)
            r = requests.get(API, params=params, headers=UA, timeout=30)
            if r.status_code == 429:
                _PAUSE["until"] = max(_PAUSE["until"], time.time() + min(float(r.headers.get("Retry-After", 10)) + 1, 30))
                continue
            if r.status_code == 200 and r.text.startswith("{"):
                j = r.json()
                if "error" in j and j["error"].get("code") == "maxlag":
                    time.sleep(2 + k)
                    continue
                p = j["query"]["pages"][0]
                if p.get("missing") or "revisions" not in p:
                    return {"date": d, "ok": 0}
                rev = p["revisions"][0]
                if rev["timestamp"][:10] > (d + pd.Timedelta(days=1)).strftime("%Y-%m-%d"):
                    return {"date": d, "ok": 0}       # defensive: never accept a revision made after the cut-off
                row = score(rev["slots"]["main"]["content"])
                if row is None:
                    return {"date": d, "ok": 0}
                row.update(date=d, ok=1)
                return row
            time.sleep(1.5 * (k + 1))
        except Exception:
            time.sleep(1.5 * (k + 1))
    return {"date": d, "ok": -1}                          # transient failure: retried on the next run


def fetch_batch(days, tries=6):
    """Latest version of up to 25 daily pages in ONE request. Returns {day: row}, and records when each page was last edited."""
    titles = {title(d): d for d in days}
    params = {"action": "query", "prop": "revisions", "rvprop": "content|timestamp", "rvslots": "main", "titles": "|".join(titles),
              "format": "json", "formatversion": 2, "maxlag": 5}
    out, cont = {}, {}
    for _ in range(40):                                     # follow API continuation if the answer is split
        got = None
        for k in range(tries):
            try:
                r = requests.get(API, params={**params, **cont}, headers=UA, timeout=60)
                if r.status_code == 429:
                    time.sleep(min(float(r.headers.get("Retry-After", 10)) + 1, 30))
                    continue
                if r.status_code == 200 and r.text.startswith("{"):
                    j = r.json()
                    if "error" in j:
                        time.sleep(2 + k)
                        continue
                    got = j
                    break
                time.sleep(1.5 * (k + 1))
            except Exception:
                time.sleep(1.5 * (k + 1))
        if got is None:
            return {d: {"date": d, "ok": -1} for d in days if d not in out}
        for p in got["query"]["pages"]:
            d = titles.get(p["title"])
            if d is None:
                continue
            if p.get("missing") or "revisions" not in p:
                out.setdefault(d, {"date": d, "ok": 0})
                continue
            rev = p["revisions"][0]
            row = score(rev["slots"]["main"]["content"])
            if row is None:
                out[d] = {"date": d, "ok": 0}
            else:
                row.update(date=d, ok=1, last_edit=rev["timestamp"][:10])
                out[d] = row
        cont = got.get("continue")
        if not cont:
            break
    for d in days:
        out.setdefault(d, {"date": d, "ok": 0})
    return out


def run_batch(a, days):
    t0 = time.time()
    chunks = [days[i:i + 25] for i in range(0, len(days), 25)]
    rows, deadline = [], t0 + a.minutes * 60
    with cf.ThreadPoolExecutor(2) as ex:
        futs = []
        for c in chunks:
            futs.append(ex.submit(fetch_batch, c))
        for n, f in enumerate(futs):
            try:
                rows.extend(f.result(timeout=max(5, deadline - time.time())).values())
            except Exception:
                break
            if n % 40 == 0:
                print(f"  batch {n}/{len(chunks)}  {time.time()-t0:.0f}s", flush=True)
            if time.time() > deadline:
                print("  time budget reached", flush=True)
                break
        for f in futs:
            f.cancel()
    return pd.DataFrame(rows)


def audit(a):
    """Compare the FAST version (latest page) with the TRUE point-in-time version on a sample of days, to measure any hindsight leak."""
    fast = pd.read_csv(a.out, parse_dates=["date"])
    fast = fast[fast.ok == 1].set_index("date")
    pit_old = pd.read_csv(a.pit, parse_dates=["date"]) if os.path.exists(a.pit) else pd.DataFrame(columns=["date", "ok"])
    pit_old = pit_old[pit_old.ok == 1].set_index("date")
    rng = pd.Series(fast.index)
    sample = rng[rng >= "2009-06-01"].sample(min(a.audit, int((rng >= "2009-06-01").sum())), random_state=1).sort_values().tolist()
    t0 = time.time()
    got = []
    with cf.ThreadPoolExecutor(3) as ex:
        for r in ex.map(fetch_day, sample):
            got.append(r)
            if time.time() - t0 > a.minutes * 60:
                break
    pit_new = pd.DataFrame(got)
    pit_new = pit_new[pit_new.ok == 1].set_index("date")
    pit = pd.concat([pit_old, pit_new]).sort_index()
    cols = ["words", "neg", "pos", "conflict", "fincrisis", "ratesinfl", "trade", "energy", "health", "disaster"]
    both = pit.join(fast, lsuffix="_pit", rsuffix="_fast", how="inner")
    print(f"AUDIT: {len(both)} days compared (PIT cached {len(pit_old)} + fresh {len(pit_new)})")
    rep = []
    for c in cols:
        x, y = both[c + "_pit"], both[c + "_fast"]
        rep.append({"feature": c, "corr": float(x.corr(y)), "median_pit": float(x.median()), "median_latest": float(y.median())})
    if "tone" not in cols:
        both["tone_pit"] = both["pos_pit"] - both["neg_pit"]
        both["tone_fast"] = both["pos_fast"] - both["neg_fast"]
        rep.append({"feature": "tone(pos-neg)", "corr": float(both["tone_pit"].corr(both["tone_fast"])), "median_pit": float(both["tone_pit"].median()), "median_latest": float(both["tone_fast"].median())})
    R = pd.DataFrame(rep)
    print(R.round(3).to_string(index=False))
    if "last_edit" in fast.columns:
        le = pd.to_datetime(fast["last_edit"], errors="coerce")
        lag = (le - fast.index.to_series()).dt.days
        print(f"last edit of page vs its day: median {lag.median():.0f} days after; edited more than 3 days after its day: {(lag>3).mean()*100:.0f}% of pages; more than a year after: {(lag>365).mean()*100:.0f}%")
    R.to_csv(os.path.join(os.path.dirname(a.out) or ".", "news_audit.csv"), index=False)
    both.reset_index().to_csv(os.path.join(os.path.dirname(a.out) or ".", "news_audit_pairs.csv"), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2004-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--step", type=int, default=1, help="take every Nth day (saves requests; features carry forward in between)")
    ap.add_argument("--minutes", type=float, default=9.0)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", default="data/news_counts.csv")
    ap.add_argument("--mode", default="pit", choices=["pit", "batch", "audit"])
    ap.add_argument("--pit", default="data/news_pit.csv")
    ap.add_argument("--audit", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    if a.mode == "audit":
        return audit(a)
    end = pd.Timestamp(a.end) if a.end else pd.Timestamp.utcnow().tz_localize(None).normalize() - pd.Timedelta(days=1)
    days = pd.date_range(a.start, end)[::a.step]
    if a.mode == "batch":
        res = run_batch(a, list(days))
        res = res[res["ok"] >= 0].sort_values("date")
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        res.to_csv(a.out, index=False)
        g = res.assign(y=res["date"].dt.year).groupby("y").agg(days=("date", "size"), with_page=("ok", "sum"), avg_words=("words", "mean"))
        print(f"saved {len(res)} days to {a.out} in {time.time()-t0:.0f}s (batch mode: latest version of each page)")
        print(g.round(0).to_string())
        return
    done = pd.DataFrame()
    if os.path.exists(a.out):
        done = pd.read_csv(a.out, parse_dates=["date"])
        done = done[done["ok"] >= 0]
    todo = [d for d in days if d not in set(done["date"])] if len(done) else list(days)
    print(f"{len(days)} days in range, {len(done)} already cached, {len(todo)} to fetch, budget {a.minutes} min, {a.workers} workers", flush=True)
    rows, deadline = [], t0 + a.minutes * 60
    n = 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        it = iter(todo)
        pending = set()
        while True:
            while len(pending) < a.workers * 3 and time.time() < deadline:
                try:
                    pending.add(ex.submit(fetch_day, next(it)))
                except StopIteration:
                    break
            if not pending:
                break
            fin, pending = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
            for f in fin:
                rows.append(f.result())
                n += 1
            if n % 1000 < len(fin):
                print(f"  {n}/{len(todo)} fetched, {time.time()-t0:.0f}s, {n/(time.time()-t0):.1f} req/s", flush=True)
    new = pd.DataFrame(rows)
    out = pd.concat([done, new[new["ok"] >= 0]], ignore_index=True).drop_duplicates("date", keep="last").sort_values("date")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    out.to_csv(a.out, index=False)
    fail = int((new["ok"] == -1).sum()) if len(new) else 0
    print(f"saved {len(out)} days to {a.out} in {time.time()-t0:.0f}s; failures to retry {fail}; unfetched (budget) {len(todo)-n}")
    g = out.assign(y=out["date"].dt.year).groupby("y").agg(days=("date", "size"), with_page=("ok", "sum"), avg_words=("words", "mean"))
    print(g.round(0).to_string())


if __name__ == "__main__":
    main()
