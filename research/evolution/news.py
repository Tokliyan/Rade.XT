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


def fetch_day(d, tries=6):
    nxt = (d + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    params = {"action": "query", "prop": "revisions", "rvprop": "content|timestamp", "rvslots": "main", "rvlimit": 1,
              "rvstart": nxt, "rvdir": "older", "titles": title(d), "format": "json", "formatversion": 2, "maxlag": 5}
    for k in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=30)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2004-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--minutes", type=float, default=9.0)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", default="data/news_counts.csv")
    a = ap.parse_args()
    t0 = time.time()
    end = pd.Timestamp(a.end) if a.end else pd.Timestamp.utcnow().tz_localize(None).normalize() - pd.Timedelta(days=1)
    days = pd.date_range(a.start, end)
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
