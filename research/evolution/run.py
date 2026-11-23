"""
TEST A - widen the search.   python run.py --data real --seeds 6

  * 45 markets, 9 strategy families, optional gates driven by macro numbers and point-in-time news counts
  * 1,000 bots, 1998 -> today, a new generation every 5 months, kill/clone, 12 independent runs
  * Pass rule: a bot passes a 5-month period if it returns >= +6.5% NET of trading costs
  * Reports: Frozen Ten (fair test), Hall of Fame (hindsight), luck baseline (same system on fake shuffled markets),
    news ablation (with news / macro only / no gates), repeat offenders, which time periods produce passes.
Outputs go to ./out (csv/json/md) and are printed to the log.
"""
import argparse, json, os, time
import numpy as np
import pandas as pd
import data as D
import engine as E
import report as R

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 400)


def pct(x, d=1):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x*100:+.{d}f}%"


def load_inputs(a):
    if a.data == "real":
        prices, macro = D.fetch_real2()
        news = D.load_news(a.news)
    else:
        prices = D.synthetic(a.data.split("_")[1], seed=1, n_assets=20)
        rng = np.random.default_rng(5)
        macro = pd.DataFrame({"VIX": 18 * np.exp(np.cumsum(rng.normal(0, .02, len(prices)))), "US10Y": 3 + np.cumsum(rng.normal(0, .02, len(prices))),
                              "US13W": 2 + np.cumsum(rng.normal(0, .02, len(prices)))}, index=prices.index)
        news = None
    if a.exclude:
        prices = prices.drop(columns=[c for c in a.exclude if c in prices.columns])
    return prices, macro, news


def skill_stats(rows, era):
    r = rows[(rows["era"] == era)].dropna(subset=["comm_ret"])
    if len(r) < 3:
        return float("nan")
    d = (r["comm_ret"] - r["pop_mean"]).to_numpy()
    return float(d.mean() / (d.std() / np.sqrt(len(d)))) if d.std() > 0 else 0.0


def do_run(F, seed, cull, pop, variant, kind, keep=False):
    out = E.evolve(F, pop=pop, cull=cull, seed=seed)
    p = R.period_table(F, out["perf"])
    luck = R.hof_luck_stats(p, out["genomes"])
    s = {"variant": variant, "kind": kind, "seed": seed, "cull": cull, **luck,
         "skill_t_train": skill_stats(out["rows"], "train"), "skill_t_hold": skill_stats(out["rows"], "hold")}
    fz = None
    if out["frozen"] is not None:
        tbl, summ, aux = R.frozen_ten(F, out["frozen"], out["bnds"])
        s.update({"fz_port_mean": summ["port_mean"], "fz_port_mean100": summ["port_mean_$100"], "fz_port_share": summ["port_passes"] / summ["windows"],
                  "fz_port_share100": summ["port_passes_$100"] / summ["windows"], "fz_bot_share": summ["bot_pass_total"] / summ["bot_slots"],
                  "fz_port_total": summ["port_total"], "fz_worst": summ["port_worst"]})
        fz = (tbl, summ, aux)
    return s, (out, p, fz) if keep else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="real", choices=["real", "synth_random", "synth_planted"])
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--culls", type=float, nargs="+", default=[0.10, 0.30])
    ap.add_argument("--pop", type=int, default=1000)
    ap.add_argument("--nulls", type=int, default=6)
    ap.add_argument("--news", default="data/news_pit.csv")
    ap.add_argument("--out", default="out")
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--variants", nargs="*", default=["full", "macro", "none"])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t_start = time.time()
    prices, macro, news = load_inputs(a)
    prices = prices.sort_index()
    ext_full = E.make_ext(prices.index, macro, news)
    ext_macro = ext_full[[c for c in ext_full.columns if not c.startswith("news_")]]
    exts = {"full": ext_full, "macro": ext_macro, "none": None}
    if news is None:
        a.variants = [v for v in a.variants if v != "macro"]
    Fs = {v: E.Features(prices, exts[v]) for v in a.variants}
    F = Fs[a.variants[0]]
    first_news = None
    if news is not None and (news.ok == 1).any():
        first_news = str(news[news.ok == 1].date.min().date())
    print(f"markets: {F.A}  days: {F.T}  {F.dates[0].date()} -> {F.dates[-1].date()}  gate inputs: {Fs[a.variants[0]].NX} "
          f"(macro {ext_macro.shape[1]}, news {ext_full.shape[1]-ext_macro.shape[1]}); news pages from {first_news}; bad prints clipped {F.bad_prints}")
    pd.DataFrame({"market": F.names, "first_date": [str(F.dates[s].date()) if s < F.T else "none" for s in F.start]}).to_csv(os.path.join(a.out, "universe.csv"), index=False)

    summaries, kept = [], []
    n_runs = a.seeds * len(a.culls)
    for v in a.variants:
        for cull in a.culls:
            for s in range(a.seeds):
                row, keep = do_run(Fs[v], 1000 + s, cull, a.pop, v, "real", keep=(v == "full" or v == a.variants[0]))
                summaries.append(row)
                if keep is not None and v == a.variants[0]:
                    kept.append((row, keep))
        print(f"variant {v}: {n_runs} runs done ({time.time()-t_start:.0f}s)", flush=True)
    for k in range(a.nulls):
        seed = 9000 + k
        shuffled = E.block_shuffle_prices(prices, seed)
        extn = E.block_shuffle_rows(exts[a.variants[0]], seed) if exts[a.variants[0]] is not None else None
        Fn = E.Features(shuffled, extn)
        row, _ = do_run(Fn, seed, 0.10, a.pop, "null", "null")
        summaries.append(row)
    print(f"null (shuffled-market) runs done ({time.time()-t_start:.0f}s)", flush=True)
    S = pd.DataFrame(summaries)
    S.to_csv(os.path.join(a.out, "runs.csv"), index=False)

    # ------------------------------------------------------------------ pooled analysis on the main variant
    main_v = a.variants[0]
    ps, gs, evs, tops = [], [], [], []
    for i, (row, (out, p, fz)) in enumerate(kept):
        off = (i + 1) * 10_000_000
        q = p.copy(); q["bid"] += off
        g = out["genomes"].copy(); g["bid"] += off; g["lineage"] += off; g["parent"] = np.where(g["parent"] >= 0, g["parent"] + off, -1)
        ps.append(q); gs.append(g)
        bots = R.top_bots(p, out["genomes"], k=30)
        ev = R.evaluate_bots(F=Fs[main_v], bots=bots, genomes=out["genomes"], bnds=out["bnds"])
        ev["bid"] += off
        ev["run"] = i
        ev["seed"], ev["cull"] = row["seed"], row["cull"]
        evs.append(ev)
    P, GN = pd.concat(ps, ignore_index=True), pd.concat(gs, ignore_index=True)
    EV = pd.concat(evs, ignore_index=True)
    FM = Fs[main_v]
    bnds = kept[0][1][0]["bnds"]

    # ------------------------------------------------------------------ report
    L = []
    def say(s=""):
        print(s); L.append(s)

    say("=" * 100)
    say(f"TEST A: widened search. {F.A} markets, 9 strategy families, {n_runs} runs per variant, 1,000 bots, 1998 -> {F.dates[-1].date()}")
    say(f"Pass rule: >= +6.5% in a 5-month period, net of trading costs ($100 version: flat $2 per trade). Holdout = 2018-01 onward.")
    say("=" * 100)

    # 1. Frozen Ten (headline run = first run, declared in advance)
    row0, (out0, p0, fz0) = kept[0]
    tbl, summ, aux = fz0
    say(f"\n1) THE FROZEN TEN  (fair test: picked in Jan 2018 from older data only, then run untouched; headline run seed {row0['seed']}, cull {row0['cull']})")
    say(f"   {summ['windows']} five-month windows from {summ['first']}.  Ten-bot portfolio passes in {summ['port_passes']} of {summ['windows']} windows "
        f"(on $100 with $2 fees: {summ['port_passes_$100']}).  Mean per 5 months {pct(summ['port_mean'])} (after $2 fees {pct(summ['port_mean_$100'])}); "
        f"worst {pct(summ['port_worst'])}, best {pct(summ['port_best'])}; total {pct(summ['port_total'])}.")
    say(f"   For comparison just holding the S&P 500 passes {summ['sp500_passes']} of {summ['windows']} (mean {pct(summ['sp500_mean'])} per 5 months); "
        f"an equal mix of all markets passes {summ['ew_passes']} (mean {pct(summ['ew_mean'])}).")
    for i, r in tbl.iterrows():
        say(f"   #{i+1:<2d} [{r['family']:9s}|{r['market']:11s}|gate:{r['gate']:5s}] passes {r['passes']:>2d}/{r['windows']} ($100: {r['passes_$100']:>2d})  "
            f"mean {pct(r['mean_5m'])}  worst {pct(r['worst_5m'])}  best {pct(r['best_5m'])}  holding that market passes {r['market_passes']}/{r['windows']}")
        say(f"        {r['strategy']}")
    real = S[(S.kind == "real") & (S.variant == main_v)]
    nul = S[S.kind == "null"]
    say(f"\n   Across all {len(real)} runs, the Frozen Ten portfolio passes {real.fz_port_share.median()*100:.0f}% of windows (median; range {real.fz_port_share.min()*100:.0f}% to {real.fz_port_share.max()*100:.0f}%); "
        f"mean per 5 months {pct(real.fz_port_mean.median())}; after $2 fees {pct(real.fz_port_mean100.median())}.")

    # 2. Hall of fame
    EV = EV.sort_values(["passes", "life_mean"], ascending=False)
    EV["key"] = EV["family"] + "|" + EV["market"]
    seen = EV.groupby("key")["run"].nunique().rename("seen_in_runs")
    hof = EV.drop_duplicates("key").join(seen, on="key")
    hof["lb"] = [R.wilson_lb(int(k), int(n)) for k, n in zip(hof["passes"], hof["periods"])]
    hof = hof.sort_values(["lb", "life_mean"], ascending=False)
    say(f"\n2) HALL OF FAME  (hindsight list: the bots with the best pass record over their own lives, pooled over {len(kept)} runs; expect luck in here)")
    top10 = hof.head(10)
    for i, (_, r) in enumerate(top10.iterrows(), 1):
        say(f"   #{i:<2d} [{r['family']:9s}|{r['market']:11s}|gate:{r['gate']:5s}] passed {r['passes']}/{r['periods']} of its own periods ($100: {r['passes_$100']}), mean {pct(r['life_mean'])}; "
            f"seen in {r['seen_in_runs']} of {len(kept)} runs; VERDICT {r['verdict']}")
        say(f"        {r['strategy']}")
        say(f"        checks: after selection {pct(r['fwd_rate'],0)} of {r['fwd_n']} later periods pass (mean {pct(r['fwd_mean'])}); all history {pct(r['all_rate'],0)} vs {pct(r['market_rate'],0)} for holding the market; passes in {r['pass_years']} years")
        if r["good"]:
            say(f"        good: {r['good']}")
        if r["flags"]:
            say(f"        warnings: {r['flags']}")

    # 3. luck baseline
    say("\n3) LUCK BASELINE  (same system, same rules, on FAKE markets where the real returns were shuffled in blocks: no edge exists there)")
    def line(lbl, col, f=lambda x: f"{x:.2f}"):
        rr, nn = real[col].dropna(), nul[col].dropna()
        say(f"   {lbl:55s} real median {f(rr.median())} (runs {f(rr.min())}..{f(rr.max())}) | fake markets median {f(nn.median())} (runs {f(nn.min())}..{f(nn.max())})")
    if len(nul):
        line("Hall of Fame top-10: average share of periods passed", "top_mean_rate")
        line("Bots passing >= 60% of their periods (count)", "n_bots_60pct", lambda x: f"{x:.0f}")
        line("All bot-periods that pass +6.5% (share)", "pop_pass_rate")
        line("Frozen Ten portfolio: share of windows passing", "fz_port_share")
        line("Frozen Ten portfolio: mean 5-month return", "fz_port_mean", lambda x: pct(x))
        line("Selection skill t-stat, holdout (above +3 = real)", "skill_t_hold", lambda x: f"{x:+.1f}")
    else:
        say("   (no null runs)")

    # 4. ablation
    say("\n4) DOES NEWS HELP?  (same seeds, three settings)")
    ab = S[S.kind == "real"].groupby("variant").agg(fz_share=("fz_port_share", "median"), fz_mean=("fz_port_mean", "median"), fz_mean100=("fz_port_mean100", "median"),
                                                    hof_rate=("top_mean_rate", "median"), pop_pass=("pop_pass_rate", "median"), skill_hold=("skill_t_hold", "median"),
                                                    skill_train=("skill_t_train", "median"))
    names = {"full": "news + macro gates", "macro": "macro gates only (no news)", "none": "no gates at all"}
    for v, r in ab.iterrows():
        say(f"   {names.get(v, v):28s} Frozen Ten passes {r.fz_share*100:4.0f}% of windows, mean {pct(r.fz_mean)} per 5m ({pct(r.fz_mean100)} after $2 fees) | Hall-of-Fame top-10 pass rate {r.hof_rate*100:.0f}% | "
            f"all bot-periods passing {r.pop_pass*100:.1f}% | selection t train {r.skill_train:+.1f}, holdout {r.skill_hold:+.1f}")
    gate_use = GN.drop_duplicates("bid")
    say(f"   Gate usage in the main variant: {(gate_use.gfeat>=0).mean()*100:.0f}% of all bots ever born carry a gate; among Hall-of-Fame bots: "
        f"{(hof.head(30)['gate']!='none').mean()*100:.0f}% (top 30).")

    # 5. attention list
    say("\n5) NEEDS YOUR ATTENTION")
    cand = hof[hof["verdict"] == "CANDIDATE"].head(8)
    watch = hof[hof["verdict"] == "WATCH"].head(8)
    say(f"   CANDIDATES (kept passing after they were selected, beat just holding the market, spread over 4+ years, survive $2 fees): {len(hof[hof['verdict']=='CANDIDATE'])}")
    for _, r in cand.iterrows():
        say(f"     - [{r['family']}|{r['market']}] {r['strategy']}  | later periods {pct(r['fwd_rate'],0)} of {r['fwd_n']}, all history {pct(r['all_rate'],0)} vs market {pct(r['market_rate'],0)}")
    say(f"   WATCH (decent but not proven): {len(hof[hof['verdict']=='WATCH'])}")
    for _, r in watch.iterrows():
        say(f"     - [{r['family']}|{r['market']}] {r['strategy']}  | {r['good']}; {r['flags']}")
    lucky_top = top10[top10["verdict"] == "LUCKY?"]
    say(f"   WARNING: {len(lucky_top)} of the Hall-of-Fame top 10 look like luck (their record does not hold outside the periods they were picked on).")

    combos = R.combo_table(FM, P, GN)
    nc = len(combos)
    thr = 3.7 if nc > 100 else 3.3
    say(f"\n6) REPEAT OFFENDERS  (family x market combos where ALL bots of that type beat just holding the market, period after period, across every run; {nc} combos tested, need t > {thr})")
    for _, r in combos.head(10).iterrows():
        say(f"   {r['family']:9s} {r['market']:11s} {r['periods']:3.0f} periods  all-bot mean {pct(r['mean_5m'])} vs holding {pct(r['hold_5m'])} -> excess {pct(r['excess_5m'])} per 5m (t={r['t']:+.1f})  "
            f"passes {r['pass_rate']*100:.0f}% of the time vs {r['hold_pass_rate']*100:.0f}% for holding  {'<-- clears the bar' if r['t']>thr else ''}")
    say(f"   Combos clearing the bar: {int((combos['t']>thr).sum())} of {nc}.  (With {nc} tries, a few at t>2.5 are expected by luck alone.)")

    wt = R.window_table(FM, P, bnds)
    say("\n7) WHICH 5-MONTH PERIODS PRODUCE PASSES  (share of ALL bots passing, per period, vs what markets did)")
    top_w = wt.sort_values("share_bots_pass", ascending=False).head(8)
    for _, r in top_w.iterrows():
        say(f"   from {r['start']}: {r['share_bots_pass']*100:4.1f}% of bots pass | S&P 500 {pct(r['sp500'])}  Bitcoin {pct(r['btc'])}  average bot {pct(r['pop_mean'])}")
    ok = wt.dropna(subset=["sp500"])
    say(f"   Correlation between 'share of bots passing' and the S&P 500's return in that period: {np.corrcoef(ok['share_bots_pass'], ok['sp500'])[0,1]:+.2f}  (high = passes mostly ride the market)")
    last = wt.tail(6)
    say("   Most recent periods: " + "; ".join(f"{r['start']}: {r['share_bots_pass']*100:.1f}% pass" for _, r in last.iterrows()))

    say(f"\nTotal time {time.time()-t_start:.0f}s")
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(L))
    hof.to_csv(os.path.join(a.out, "hall_of_fame.csv"), index=False)
    EV.to_csv(os.path.join(a.out, "hall_of_fame_all_runs.csv"), index=False)
    tbl.to_csv(os.path.join(a.out, "frozen_ten.csv"), index=False)
    combos.to_csv(os.path.join(a.out, "combos.csv"), index=False)
    wt.to_csv(os.path.join(a.out, "windows.csv"), index=False)
    json.dump({"frozen_ten_summary": summ, "ablation": ab.to_dict()}, open(os.path.join(a.out, "summary.json"), "w"), default=float, indent=1)


if __name__ == "__main__":
    main()
