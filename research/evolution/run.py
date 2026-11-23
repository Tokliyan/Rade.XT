"""
Run the evolution research and print an honest summary.

  python run.py --data real                       # real history (needs internet; run in GitHub Actions)
  python run.py --data synth_planted --seeds 2    # validation on fake data
Outputs go to ./out : summary.json, runs.csv, generations.csv, universe.csv
"""
import argparse, json, os, sys, time
import numpy as np
import pandas as pd
import data as D
import engine as E


def era_stats(rows, era):
    r = rows[(rows["era"] == era)].dropna(subset=["comm_ret"])
    if r.empty:
        return {}
    growth = float(np.prod(1 + r["comm_ret"]))
    yrs = r["days"].sum() / 252
    ann = growth ** (1 / yrs) - 1 if growth > 0 else -1.0
    gap = float(r["comm_cost_gap"].sum() / yrs)
    diff = (r["comm_ret"] - r["pop_mean"]).to_numpy()
    t = float(diff.mean() / (diff.std() / np.sqrt(len(diff)))) if len(diff) > 2 and diff.std() > 0 else 0.0
    pop_growth = float(np.prod(1 + r["pop_mean"]))
    return {"ann": ann, "ann_net_100": ann - gap, "pop_ann": pop_growth ** (1 / yrs) - 1,
            "skill_per_5m": float(diff.mean()), "skill_t": t, "n": int(len(r)), "years": float(yrs),
            "best_bot_inperiod": float(rows[rows["era"] == era]["best_ret"].mean())}


def one_run(F, seed, cull, pop):
    out = E.evolve(F, pop=pop, cull=cull, seed=seed)
    rows = out["rows"]
    res = {"seed": seed, "cull": cull, "births": out["births"],
           "wf_train": era_stats(rows, "train"), "wf_hold": era_stats(rows, "hold")}
    if out["frozen"] is not None:
        fz = E.freeze_and_test(F, out["frozen"])
        fz2 = E.freeze_and_test(F, out["frozen"], cost_scale=2.0)
        t0 = fz["t0"]
        res["frozen"] = fz["stats"]
        res["frozen"]["trades_per_year"] = fz["trades_per_year"]
        res["frozen"]["net_100_ann"] = fz["stats"]["ann"] - fz["drag_100"]
        res["frozen"]["ann_cost_x2"] = fz2["stats"]["ann"]
        res["frozen"]["dead"] = fz["dead"]
        res["frozen"]["bench"] = E.benchmark_stats(F, t0, F.T)
        fam = {}
        for f in range(E.NF):
            m = fz["fam"] == f
            if m.any():
                fam[E.FAMS[f]] = {"n": int(m.sum()), "mean_total_ret": float(fz["ind_ret"][m].mean())}
        res["frozen"]["by_family"] = fam
        sr = fz["stats"]["sharpe"] / np.sqrt(252)
        res["frozen"]["dsr_prob"] = None
        res["frozen"]["_sr_daily"] = sr
        res["frozen"]["_n_days"] = F.T - t0
    return res, rows.assign(seed=seed, cull=cull)


def pct(x):
    return "n/a" if x is None else f"{x*100:+.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="real", choices=["real", "synth_random", "synth_planted"])
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--culls", type=float, nargs="+", default=[0.10, 0.30])
    ap.add_argument("--pop", type=int, default=1000)
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.data == "real":
        prices = D.fetch_real(cache=os.path.join(a.out, "prices.csv"))
    else:
        prices = D.synthetic(a.data.split("_")[1], seed=1)
    F = E.Features(prices)
    cover = pd.DataFrame({"asset": F.names, "first_date": [str(F.dates[s].date()) if s < F.T else "none" for s in F.start]})
    cover.to_csv(os.path.join(a.out, "universe.csv"), index=False)
    print(cover.to_string(index=False))
    print(f"bad prints clipped: {F.bad_prints}; days: {F.T}; {F.dates[0].date()} -> {F.dates[-1].date()}")
    runs, gens = [], []
    n_runs = a.seeds * len(a.culls)
    t_start = time.time()
    for cull in a.culls:
        for s in range(a.seeds):
            r, g = one_run(F, 1000 + s, cull, a.pop)
            runs.append(r)
            gens.append(g)
            fz = r.get("frozen", {})
            print(f"run cull={cull:.2f} seed={r['seed']}: frozen-holdout ann {pct(fz.get('ann'))} | walk-forward hold ann {pct(r['wf_hold'].get('ann'))} | skill t={r['wf_hold'].get('skill_t', 0):+.1f}  ({time.time()-t_start:.0f}s)")
    for r in runs:
        fz = r.get("frozen")
        if fz:
            fz["dsr_prob"] = E.deflated_sharpe_prob(fz["_sr_daily"], fz["_n_days"], n_runs)
    pd.concat(gens).to_csv(os.path.join(a.out, "generations.csv"), index=False)
    flat = []
    for r in runs:
        fz = r.get("frozen", {})
        flat.append({"seed": r["seed"], "cull": r["cull"], "frozen_ann": fz.get("ann"), "frozen_net100": fz.get("net_100_ann"),
                     "frozen_cost2x": fz.get("ann_cost_x2"), "frozen_maxdd": fz.get("maxdd"), "frozen_sharpe": fz.get("sharpe"),
                     "trades_yr": fz.get("trades_per_year"), "wf_train_ann": r["wf_train"].get("ann"), "wf_hold_ann": r["wf_hold"].get("ann"),
                     "wf_hold_net100": r["wf_hold"].get("ann_net_100"), "skill_train_t": r["wf_train"].get("skill_t"),
                     "skill_hold_t": r["wf_hold"].get("skill_t"), "dsr": fz.get("dsr_prob"),
                     "best_bot_5m_train": r["wf_train"].get("best_bot_inperiod"), "pop_hold_ann": r["wf_hold"].get("pop_ann")})
    df = pd.DataFrame(flat)
    df.to_csv(os.path.join(a.out, "runs.csv"), index=False)
    json.dump(runs, open(os.path.join(a.out, "summary.json"), "w"), default=float, indent=1)

    bench = runs[0].get("frozen", {}).get("bench", {})
    print("\n==================== SUMMARY ====================")
    print(f"{n_runs} independent runs ({a.seeds} seeds x culls {a.culls}), population {a.pop}, ~{runs[0]['births']} bots born per run")
    print("Holdout era = 2018-01 -> today (never used for selection by the frozen committee)")
    print("Benchmarks over holdout (buy & hold, price only):", {k: pct(v['ann']) + " /yr, maxDD " + pct(-v['maxdd']) for k, v in bench.items()})
    for col, label in [("frozen_ann", "FROZEN committee, holdout, annual (gross of $100 fees)"),
                       ("frozen_net100", "  same, after $2/trade fees on a $100 account"),
                       ("frozen_cost2x", "  same, with trading costs doubled (stress)"),
                       ("wf_hold_ann", "WALK-FORWARD committee (keeps evolving), holdout era, annual"),
                       ("wf_train_ann", "WALK-FORWARD committee, training era 1998-2017, annual")]:
        v = df[col].dropna().to_numpy()
        if len(v):
            print(f"{label:62s} worst {pct(v.min())}  median {pct(np.median(v))}  best {pct(v.max())}   runs>0: {(v>0).mean()*100:.0f}%")
    v = df["frozen_maxdd"].dropna()
    print(f"Frozen committee max drawdown: median {pct(-v.median())}, worst {pct(-v.max())}")
    print(f"Frozen committee trades/year per bot: median {df['trades_yr'].median():.1f}")
    for col, label in [("skill_train_t", "selection skill t-stat (train)"), ("skill_hold_t", "selection skill t-stat (holdout)")]:
        print(f"{label}: median {df[col].median():+.1f}  (above +3 = selection beat luck)")
    print(f"deflated-Sharpe probability that frozen edge is real (adjusted for {n_runs} tries): median {df['dsr'].median():.2f}")
    print(f"NAIVE best-single-bot score in training replay: {df['best_bot_5m_train'].median()*100:+.1f}% per 5 months (this is the misleading chart)")
    fam_acc = {}
    for r in runs:
        for k, v in r.get("frozen", {}).get("by_family", {}).items():
            fam_acc.setdefault(k, []).append(v["mean_total_ret"])
    print("Holdout total return of frozen-committee members by family (mean over runs):", {k: pct(float(np.mean(v))) for k, v in fam_acc.items()})

    # ---- extra detail printed to the log (so results are readable without downloading the artifact)
    print("\n---- per run ----")
    cols = ["seed", "cull", "frozen_ann", "frozen_net100", "frozen_cost2x", "frozen_maxdd", "wf_hold_ann", "wf_hold_net100", "pop_hold_ann", "skill_hold_t"]
    print(df[cols].round(3).to_string(index=False))
    g = pd.concat(gens)
    g["yr"] = pd.to_datetime(g["start"]).dt.year
    h = g.dropna(subset=["comm_ret"])
    y = h.groupby("yr").agg(committee=("comm_ret", "mean"), population=("pop_mean", "mean"), best_bot=("best_ret", "mean"))
    print("\n---- average 5-month return by year (%, mean over runs): committee = bots we selected, population = all 1000, best_bot = naive chart ----")
    print((y * 100).round(1).to_string())
    print(f"\nCommittee 5-month periods: worst {h.comm_ret.min()*100:+.1f}%  best {h.comm_ret.max()*100:+.1f}%  positive {(h.comm_ret > 0).mean()*100:.0f}% of the time")
    print(f"Mean per 5 months: committee {h.comm_ret.mean()*100:+.2f}%  population {h.pop_mean.mean()*100:+.2f}%")
    for era in ("train", "hold"):
        e = h[h.era == era]
        print(f"  {era}: committee {e.comm_ret.mean()*100:+.2f}%  population {e.pop_mean.mean()*100:+.2f}%  committee worst period {e.comm_ret.min()*100:+.1f}%")


if __name__ == "__main__":
    main()
