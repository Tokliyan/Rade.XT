"""
Reports for the evolution research: Hall of Fame (hindsight), Frozen Ten (fair test), luck checks,
plain-English strategy descriptions and verdicts.

Pass rule used everywhere: a 5-month period "passes" if the bot's return is >= +6.5% NET of the model's
trading costs. A second count uses a $100 account that pays a flat $2 per trade instead.
"""
from math import sqrt
import numpy as np
import pandas as pd
import engine as E

PASS = 0.065
GENES = ["fam", "asset", "partner", "size", "stop", "maxhold", "gfeat", "gthr", "gdir", "p1", "p2", "p3", "p4"]
MIN_DAYS = 100            # shorter (unfinished) periods are ignored in pass statistics
CRYPTO = ("BTC", "ETH")

FEATURE_WORDS = {
    "vix_level": "the VIX fear index", "vix_jump5": "a jump in the VIX", "yield_curve": "the yield-curve slope (10yr minus 3-month)",
    "rate_move60": "the 60-day move in 10-year yields", "news_tone": "the tone of world news", "news_volume": "how much news there is",
    "news_conflict": "conflict/war news", "news_fincrisis": "financial-crisis news", "news_ratesinfl": "interest-rate/inflation news",
    "news_trade": "tariff/sanctions news", "news_energy": "oil/energy news", "news_health": "health/pandemic news",
    "news_disaster": "disaster news"}


def wilson_lb(k, n, z=1.64):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d


def feature_text(name):
    base, w = name.split("@")
    when = {"1": "today's reading of", "5": "the 5-day average of", "20": "the 20-day average of"}[w]
    return f"{when} {FEATURE_WORDS.get(base, base)}"


def describe(F, r):
    """Plain-English strategy for one genome row (mapping with the GENES keys)."""
    fam, a = int(r["fam"]), F.names[int(r["asset"])]
    if fam == 0:
        wf = int(round(r["p1"])); ws = int(round(wf * r["p2"]))
        s = f"Holds {a} while its {wf}-day average is above its {ws}-day average (trend following)"
    elif fam == 1:
        s = (f"Buys {a} after it falls {r['p2']:.1f} standard deviations below its {int(round(r['p1']))}-day average, "
             f"sells when it recovers to {r['p3']:+.1f} (dip buying)" + (", only in an uptrend" if r["p4"] > 0.5 else ""))
    elif fam == 2:
        s = f"Buys {a} on a new {int(E.GRID[int(np.clip(round(r['p1']), 0, E.G-1))])}-day high, sells on a new {int(E.GRID[int(np.clip(round(r['p2']), 0, E.G-1))])}-day low (breakout)"
    elif fam == 3:
        s = f"Holds {a} while its {int(round(r['p1']))}-day return is above {r['p2']*100:.1f}% (momentum)"
    elif fam == 4:
        s = f"Holds {a} only while its {int(round(r['p1']))}-day volatility is under {r['p2']*100:.0f}% a year" + (" and it is in an uptrend" if r["p3"] > 0.5 else "") + " (calm-market timing)"
    elif fam == 5:
        s = f"Holds {a} over the last {int(round(r['p1']))} and first {int(round(r['p2']))} trading days of each month (calendar)"
    elif fam == 6:
        s = f"Holds {a} while it ranks in the top {r['p2']*100:.0f}% of all markets by {int(E.XS_WIN[int(np.clip(round(r['p1']), 0, 4))])}-day return (rotation)"
    elif fam == 7:
        s = (f"Buys {a} when it lags {F.names[int(r['partner'])]} by {r['p2']:.1f} standard deviations over {int(round(r['p1']))} days, "
             f"sells when the gap closes to {r['p3']:+.1f} (relative value)")
    else:
        s = f"Holds {a}" + (f" while above its {int(round(r['p2']))}-day average" if r["p1"] > 0.5 else " all the time") + " (risk-off timing)"
    if int(r["gfeat"]) >= 0 and F.NX:
        side = "above" if r["gdir"] > 0 else "below"
        s += f"; steps aside when {feature_text(F.xnames[int(r['gfeat'])])} is more than {r['gthr']:.1f} std {side} its norm"
    s += f". Position {r['size']*100:.0f}% of the account, stop-loss {r['stop']*100:.0f}%."
    return s


def gate_kind(F, r):
    if int(r["gfeat"]) < 0 or not F.NX:
        return "none"
    return "news" if F.xnames[int(r["gfeat"])].startswith("news_") else "macro"


def genome_dict(genomes_df, bids):
    gi = genomes_df.drop_duplicates("bid").set_index("bid").loc[list(bids)]
    d = {}
    for k in GENES:
        v = gi[k].to_numpy()
        d[k] = v.astype(int) if k in ("fam", "asset", "partner", "gfeat") else v.astype(float)
    return d


def row_of(gd, i):
    return {k: gd[k][i] for k in GENES}


def period_table(F, perf):
    p = perf[perf["days"] >= MIN_DAYS].copy()
    p["year"] = F.dates[p["t0"].to_numpy()].year
    p["pass"] = p["ret"] >= PASS
    p["pass100"] = p["net100"] >= PASS
    return p


def bot_table(p):
    g = p.groupby("bid")
    t = pd.DataFrame({"n": g.size(), "passes": g["pass"].sum(), "passes100": g["pass100"].sum(), "mean_ret": g["ret"].mean(),
                      "worst": g["ret"].min(), "first_gen": g["gen"].min(), "last_gen": g["gen"].max(), "mean_trades": g["trades"].mean()})
    t["years"] = g["year"].apply(lambda s: s.nunique())
    t["pass_years"] = p[p["pass"]].groupby("bid")["year"].nunique()
    t["pass_years"] = t["pass_years"].fillna(0).astype(int)
    t["rate"] = t["passes"] / t["n"]
    t["lb"] = [wilson_lb(int(k), int(n)) for k, n in zip(t["passes"], t["n"])]
    return t


def top_bots(p, genomes, k=30, min_periods=4):
    t = bot_table(p)
    t = t[t["n"] >= min_periods].join(genomes.drop_duplicates("bid").set_index("bid")[["lineage"]])
    t = t.sort_values(["lb", "mean_ret"], ascending=False)
    t = t.drop_duplicates("lineage")                          # clones of one idea count once
    return t.head(k)


def evaluate_bots(F, bots, genomes, bnds, hold_idx=None):
    """Re-run each bot through EVERY 5-month window of history (flat start each window) and add forward / out-of-lifetime / market checks."""
    windows = list(zip(bnds[:-1], bnds[1:]))
    full = np.array([(b - a) >= MIN_DAYS for a, b in windows])
    gd = genome_dict(genomes, bots.index)
    R, Tr, DD, N100 = E.window_returns(F, gd, windows)
    BH = E.buyhold_windows(F, windows)
    rows = []
    for i, bid in enumerate(bots.index):
        a = int(gd["asset"][i])
        ok = full & (F.start[a] <= np.array([w[0] for w in windows]))
        first, last = int(bots.loc[bid, "first_gen"]), int(bots.loc[bid, "last_gen"])
        gens = np.arange(len(windows))
        fwd = ok & (gens > last)
        before = ok & (gens < first)
        allr = float(np.mean(R[i][ok] >= PASS)) if ok.any() else np.nan
        bh = float(np.mean(BH[a][ok] >= PASS)) if ok.any() else np.nan
        fr = float(np.mean(R[i][fwd] >= PASS)) if fwd.any() else np.nan
        fr100 = float(np.mean(N100[i][fwd] >= PASS)) if fwd.any() else np.nan
        bh_f = float(np.mean(BH[a][fwd] >= PASS)) if fwd.any() else np.nan
        fwd_mean = float(np.mean(R[i][fwd])) if fwd.any() else np.nan
        r = row_of(gd, i)
        name = F.names[a]
        flags, good = [], []
        n_fwd = int(fwd.sum())
        if n_fwd >= 6 and fr >= 0.45 and fr >= bh_f + 0.10:
            good.append(f"keeps passing after it was selected ({fr*100:.0f}% of {n_fwd} later periods vs {bh_f*100:.0f}% for just holding {name})")
        elif n_fwd < 6:
            flags.append(f"only {n_fwd} later periods to check")
        else:
            flags.append(f"after selection it passes {fr*100:.0f}% of {n_fwd} later periods (holding {name} passes {bh_f*100:.0f}%)")
        if allr >= bh + 0.10:
            good.append(f"over all history passes {allr*100:.0f}% vs {bh*100:.0f}% for holding {name}")
        else:
            flags.append(f"over all history {allr*100:.0f}% vs {bh*100:.0f}% for just holding {name}")
        py = int(bots.loc[bid, "pass_years"])
        if py >= 4:
            good.append(f"passes spread over {py} different years")
        else:
            flags.append(f"passes come from only {py} year(s)")
        if name in CRYPTO:
            flags.append("crypto: results hang on boom years")
        if bots.loc[bid, "mean_trades"] < 2:
            flags.append("makes very few trades per period, so little evidence")
        if bots.loc[bid, "passes100"] < 0.5 * bots.loc[bid, "passes"]:
            flags.append("most passes disappear with $2 fees on $100")
        if n_fwd >= 6 and fr >= 0.45 and fr >= bh_f + 0.10 and py >= 4 and not (bots.loc[bid, "passes100"] < 0.5 * bots.loc[bid, "passes"]):
            verdict = "CANDIDATE"
        elif allr >= bh + 0.10 and py >= 4 and (n_fwd < 6 or fr >= 0.35):
            verdict = "WATCH"
        else:
            verdict = "LUCKY?"
        rows.append({"bid": bid, "market": name, "family": E.FAMS[int(gd["fam"][i])], "gate": gate_kind(F, r), "strategy": describe(F, r),
                     "periods": int(bots.loc[bid, "n"]), "passes": int(bots.loc[bid, "passes"]), "passes_$100": int(bots.loc[bid, "passes100"]),
                     "life_mean": float(bots.loc[bid, "mean_ret"]), "all_rate": allr, "market_rate": bh, "fwd_n": n_fwd, "fwd_rate": fr,
                     "fwd_rate_$100": fr100, "fwd_mean": fwd_mean, "pass_years": py, "verdict": verdict,
                     "good": "; ".join(good), "flags": "; ".join(flags)})
    return pd.DataFrame(rows)


def frozen_ten(F, frozen, bnds):
    """The fair test: ten bots picked at the holdout date from older data only, then run untouched, one 5-month window at a time."""
    gfz, t_hold, ids = frozen
    windows = [(a, b) for a, b in zip(bnds[:-1], bnds[1:]) if a >= t_hold and (b - a) >= MIN_DAYS]
    R, Tr, DD, N100 = E.window_returns(F, gfz, windows)
    BH = E.buyhold_windows(F, windows)
    sp = BH[F.names.index("SP500")] if "SP500" in F.names else np.full(len(windows), np.nan)
    ew = np.nanmean(BH, axis=0)
    port = R.mean(axis=0)
    port100 = N100.mean(axis=0)
    rows = []
    for i in range(len(ids)):
        a = int(gfz["asset"][i])
        r = row_of(gfz, i)
        rows.append({"bid": int(ids[i]), "market": F.names[a], "family": E.FAMS[int(gfz["fam"][i])], "gate": gate_kind(F, r),
                     "strategy": describe(F, r), "windows": len(windows), "passes": int((R[i] >= PASS).sum()),
                     "passes_$100": int((N100[i] >= PASS).sum()), "mean_5m": float(R[i].mean()), "worst_5m": float(R[i].min()),
                     "best_5m": float(R[i].max()), "total": float(np.prod(1 + R[i]) - 1), "market_passes": int((BH[a] >= PASS).sum()),
                     "trades_per_period": float(Tr[i].mean())})
    summary = {"windows": len(windows), "first": str(F.dates[windows[0][0]].date()), "port_passes": int((port >= PASS).sum()),
               "port_passes_$100": int((port100 >= PASS).sum()), "port_mean": float(port.mean()), "port_mean_$100": float(port100.mean()),
               "port_worst": float(port.min()), "port_best": float(port.max()), "port_total": float(np.prod(1 + port) - 1),
               "sp500_passes": int((sp >= PASS).sum()), "sp500_mean": float(np.nanmean(sp)), "ew_passes": int((ew >= PASS).sum()),
               "ew_mean": float(np.nanmean(ew)), "bot_pass_total": int(sum(r["passes"] for r in rows)),
               "bot_slots": len(windows) * len(ids)}
    return pd.DataFrame(rows), summary, {"R": R, "port": port, "windows": windows, "sp": sp}


def hof_luck_stats(p, genomes, k=10, min_periods=4):
    """Summary of the top-k hindsight list. Used to compare the real market against fake (shuffled) markets with no edge."""
    t = top_bots(p, genomes, k=k, min_periods=min_periods)
    return {"top_mean_rate": float(t["rate"].mean()), "top_best_rate": float(t["rate"].max()), "top_mean_passes": float(t["passes"].mean()),
            "n_bots_60pct": int(((bot_table(p).query("n >= @min_periods"))["rate"] >= 0.6).sum()),
            "pop_pass_rate": float(p["pass"].mean())}


def combo_table(F, p, genomes):
    """Idea x market combinations: how much do all bots of this family on this market beat simply holding the market, period by period?"""
    gi = genomes.drop_duplicates("bid").set_index("bid")[["fam", "asset"]]
    q = p.join(gi, on="bid")
    per = q.groupby(["fam", "asset", "gen"]).agg(ret=("ret", "mean"), n=("ret", "size"), pas=("pass", "mean")).reset_index()
    windows = {g: (t0, t0 + d) for g, t0, d in q.drop_duplicates("gen")[["gen", "t0", "days"]].itertuples(index=False)}
    bh = []
    for r in per.itertuples(index=False):
        t0, t1 = windows[r.gen]
        bh.append(F.C[int(r.asset), min(t1, F.T - 1)] / F.C[int(r.asset), t0] - 1.0 if F.start[int(r.asset)] <= t0 else np.nan)
    per["bh"] = bh
    per = per.dropna(subset=["bh"])
    per["excess"] = per["ret"] - per["bh"]
    rows = []
    for (f, a), d in per.groupby(["fam", "asset"]):
        if len(d) < 20:
            continue
        ex = d["excess"].to_numpy()
        sd = ex.std(ddof=1)
        t = ex.mean() / (sd / sqrt(len(ex))) if sd > 0 else 0.0
        rows.append({"family": E.FAMS[int(f)], "market": F.names[int(a)], "periods": len(d), "mean_5m": float(d["ret"].mean()),
                     "hold_5m": float(d["bh"].mean()), "excess_5m": float(ex.mean()), "t": float(t), "pass_rate": float(d["pas"].mean()),
                     "hold_pass_rate": float((d["bh"] >= PASS).mean())})
    return pd.DataFrame(rows).sort_values("t", ascending=False)


def window_table(F, p, bnds):
    """Which 5-month periods produce lots of passes? Compare with what the S&P 500 and Bitcoin did."""
    g = p.groupby("gen").agg(t0=("t0", "first"), share=("pass", "mean"), pop_mean=("ret", "mean"))
    out = []
    for gen, r in g.iterrows():
        t0, t1 = bnds[int(gen)], bnds[int(gen) + 1]
        sp = F.C[F.names.index("SP500"), t1] / F.C[F.names.index("SP500"), t0] - 1 if "SP500" in F.names else np.nan
        bt = np.nan
        if "BTC" in F.names and F.start[F.names.index("BTC")] <= t0:
            bt = F.C[F.names.index("BTC"), t1] / F.C[F.names.index("BTC"), t0] - 1
        out.append({"gen": int(gen), "start": str(F.dates[t0].date()), "share_bots_pass": float(r["share"]), "pop_mean": float(r["pop_mean"]), "sp500": float(sp), "btc": float(bt)})
    return pd.DataFrame(out)
