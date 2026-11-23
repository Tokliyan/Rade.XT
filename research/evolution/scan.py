"""
TEST B - gap scanner: one written idea at a time, each judged by the 6 gates.   python scan.py

Each idea is a FIXED rule with textbook settings (nothing is tuned here), and comes with the reason
somebody else would be losing money on the other side. The same pass rule applies: a 5-month period
passes if the idea returns >= +6.5% net of costs.

  Gate 1  a named reason someone else loses on the other side (written below, before any test)
  Gate 2  positive after OUR real fees (flat $2 per trade on a $100 account)
  Gate 3  positive on the held-out era (2018 onward)
  Gate 4  works on several markets, not just one (positive on >= 60% of the markets it applies to)
  Gate 5  still significant after counting every idea x market tried (deflated Sharpe >= 0.95)
  Gate 6  a 4-week forward paper test matches the backtest -> cannot be done in a backtest; any idea passing 1-5 joins the paper queue
"""
import argparse, os, time
import numpy as np
import pandas as pd
import data as D
import engine as E

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 200)
PASS = 0.065


def sma(x, w):
    return pd.Series(x).rolling(w, min_periods=w).mean().to_numpy()


def hold_after(trigger, n):
    """Position that is on for n days after each trigger day (signal day included)."""
    pos = np.zeros(len(trigger), bool)
    last = -10**9
    for t in np.flatnonzero(trigger):
        pos[t:t + n + 1] = True
    return pos


def feat(F, name):
    return F.X[F.xnames.index(name)] if name in F.xnames else None


def build_ideas():
    return [
        dict(id="turn_of_month", group="equity", why="Pension, super and salary money arrives around month-end and start; buyers who must invest on a schedule push prices up, and sellers who ignore the calendar sell cheaper.",
             fn=lambda F, a: (F.dtme < 2) | (F.dom < 3)),
        dict(id="trend_200d", group="all", why="Slow institutions and loss-averse investors under-react to price trends and sell late; trend followers get paid for stepping aside in long falls.",
             fn=lambda F, a: F.C[a] > sma(F.C[a], 200)),
        dict(id="momentum_12_1", group="all", why="Investors anchor on old prices and under-react to news, so markets that rose over the past year (skipping the last month) tend to keep rising; the sellers are anchored holders.",
             fn=lambda F, a: (F.LP[a] - np.r_[np.full(21, np.nan), F.LP[a][:-21]]) > 0 if False else (np.r_[np.full(21, np.nan), F.LP[a][:-21]] - np.r_[np.full(252, np.nan), F.LP[a][:-252]]) > 0),
        dict(id="rotation_top_third", group="all", why="Money flows slowly between markets; the markets with the strongest recent returns keep attracting it, and the laggards' holders are late sellers.",
             fn=lambda F, a: np.nan_to_num(F.RANK[3, a], nan=0.0) >= 0.67),
        dict(id="vix_panic_buy", group="equity", why="Forced sellers and people who buy insurance at any price create short-term over-reaction when the VIX spikes; calmer buyers are paid for supplying cash.",
             fn=lambda F, a: hold_after(feat(F, "vix_level@1") > 2.0, 10) if feat(F, "vix_level@1") is not None else np.zeros(F.T, bool)),
        dict(id="short_dip_in_uptrend", group="equity", why="Short-term sellers over-react inside a rising market; liquidity providers who buy a sharp 3-day drop are paid for the risk, and the sellers pay the spread.",
             fn=lambda F, a: hold_after(((F.LP[a] - np.r_[np.full(3, np.nan), F.LP[a][:-3]]) < -2.0 * np.sqrt(3) * pd.Series(np.diff(F.LP[a], prepend=np.nan)).rolling(60, min_periods=60).std().to_numpy()) & (F.C[a] > sma(F.C[a], 200)), 5)),
        dict(id="news_tone_panic_buy", group="equity", why="Headline-driven sellers dump after a burst of bad world news; calmer buyers collect the over-reaction (this idea only exists from the news start date).",
             fn=lambda F, a: hold_after(feat(F, "news_tone@5") < -2.0, 10) if feat(F, "news_tone@5") is not None else np.zeros(F.T, bool)),
        dict(id="calm_uptrend", group="all", why="Risk-limit rules force funds to sell when volatility rises, so calm periods in an uptrend are when those funds stay invested; the edge is being invested only when forced sellers are absent.",
             fn=lambda F, a: (pd.Series(np.diff(F.LP[a], prepend=np.nan)).rolling(20, min_periods=20).std().to_numpy() < pd.Series(np.diff(F.LP[a], prepend=np.nan)).rolling(250, min_periods=120).std().to_numpy()) & (F.C[a] > sma(F.C[a], 100))),
        dict(id="halloween_nov_apr", group="equity", why="Holiday and summer liquidity and fund-manager behaviour make the Nov-Apr half of the year historically stronger; the sellers are summer-leavers who shift risk by calendar.",
             fn=lambda F, a: np.isin(F.dates.month.to_numpy(), [11, 12, 1, 2, 3, 4])),
        dict(id="yield_curve_on", group="equity", why="When the yield curve flattens sharply, banks lend less and slow-moving investors keep holding risk into the downturn; staying out of equities then avoids their losses.",
             fn=lambda F, a: (feat(F, "yield_curve@20") > -1.0) if feat(F, "yield_curve@20") is not None else np.ones(F.T, bool)),
    ]


def strategy_returns(F, a, pos):
    """Daily returns with the engine's timing: signal at the close of t, trade at the close of t+1, first earns the day after."""
    pos = np.asarray(pos, bool) & ~np.isnan(F.C[a])
    ex = np.r_[False, pos[:-1]]                   # state after trading at close t
    held = np.r_[False, ex[:-1]]                  # state earning day t's return
    chg = ex != np.r_[False, ex[:-1]]
    cost = F.cost_vec[a] * F.mult
    r = np.where(held, F.R[a], 0.0) - np.where(chg, cost, 0.0)
    r[:F.start[a] + 1] = 0.0
    return r, chg


def window_rets(r, windows):
    return np.array([np.prod(1 + r[a:b]) - 1 for a, b in windows])


def ann(r, n=None):
    n = len(r) if n is None else n
    g = np.prod(1 + r)
    return g ** (252 / max(n, 1)) - 1 if g > 0 else -1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="real", choices=["real", "synth_planted", "synth_random"])
    ap.add_argument("--news", default="data/news_pit.csv")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.data == "real":
        prices, macro = D.fetch_real2()
        news = D.load_news(a.news)
        eq_names = D.EQUITY
    else:
        prices = D.synthetic(a.data.split("_")[1], seed=1, n_assets=12)
        macro, news, eq_names = None, None, set(prices.columns[:6])
    prices = prices.sort_index()
    ext = E.make_ext(prices.index, macro, news)
    F = E.Features(prices, ext)
    bnds = E.boundaries(F.dates, "1998-01-01")
    bnds = bnds + [F.T - 1] if bnds[-1] < F.T - 2 else bnds
    windows = [(x, y) for x, y in zip(bnds[:-1], bnds[1:]) if y - x >= 100]
    hold = int(np.searchsorted(F.dates.values, np.datetime64("2018-01-01")))
    ideas = build_ideas()
    rows, pooled = [], {}
    n_trials = 0
    for idea in ideas:
        mk = [i for i, n in enumerate(F.names) if idea["group"] == "all" or n in eq_names]
        for i in mk:
            n_trials += 1
    print(f"{len(ideas)} ideas, {n_trials} idea x market tests counted for gate 5")
    for idea in ideas:
        mk = [i for i, n in enumerate(F.names) if idea["group"] == "all" or n in eq_names]
        per = []
        for i in mk:
            t_first = max(F.start[i] + 300, int(np.searchsorted(F.dates.values, np.datetime64("1998-01-01"))))
            pos = np.asarray(idea["fn"](F, i), bool)
            r, chg = strategy_returns(F, i, pos)
            ws = [(x, y) for x, y in windows if x >= t_first]
            if len(ws) < 8:
                continue
            wr = window_rets(r, ws)
            bh = np.array([F.C[i, y] / F.C[i, x] - 1 for x, y in ws])
            h_idx = [k for k, (x, y) in enumerate(ws) if x >= hold]
            yrs = (ws[-1][1] - ws[0][0]) / 252
            trades_yr = chg[ws[0][0]:ws[-1][1]].sum() / yrs
            drag = trades_yr * (0.02 - F.cost_vec[i])
            r_all = r[ws[0][0]:ws[-1][1]]
            r_h = r[hold:]
            hy = max((F.T - hold) / 252, 1e-9)
            sd = r_all.std()
            per.append({"market": F.names[i], "ann": ann(r_all), "ann_100": ann(r_all) - drag, "hold_ann": ann(r_h, len(r_h)),
                        "hold_ann_100": ann(r_h, len(r_h)) - chg[hold:].sum() / hy * (0.02 - F.cost_vec[i]),
                        "pass": float((wr >= PASS).mean()), "bh_pass": float((bh >= PASS).mean()), "mean5": float(wr.mean()), "bh_mean5": float(bh.mean()),
                        "hold_pass": float((wr[h_idx] >= PASS).mean()) if h_idx else np.nan, "trades_yr": float(trades_yr),
                        "sharpe_d": float(r_all.mean() / sd) if sd > 0 else 0.0, "n": len(r_all), "skew": float(pd.Series(r_all).skew()), "kurt": float(pd.Series(r_all).kurt() + 3)})
            pooled.setdefault(idea["id"], []).append(r_all)
        if not per:
            continue
        d = pd.DataFrame(per)
        pr = np.mean([x for x in pooled[idea["id"]] if len(x) == len(pooled[idea["id"]][0])], axis=0) if len({len(x) for x in pooled[idea["id"]]}) == 1 else None
        if pr is None:
            L = min(len(x) for x in pooled[idea["id"]])
            pr = np.mean([x[-L:] for x in pooled[idea["id"]]], axis=0)
        sr = pr.mean() / pr.std() if pr.std() > 0 else 0.0
        dsr = E.deflated_sharpe_prob(sr, len(pr), n_trials, float(pd.Series(pr).skew()), float(pd.Series(pr).kurt() + 3))
        g2 = d["ann_100"].median() > 0
        g3 = d["hold_ann_100"].median() > 0 and (d["hold_ann_100"] > 0).mean() >= 0.5
        g4 = (d["ann"] > 0).mean() >= 0.60
        g5 = dsr >= 0.95
        rows.append({"idea": idea["id"], "markets": len(d), "net_ann_median": d["ann"].median(), "net_ann_$100_median": d["ann_100"].median(),
                     "holdout_ann_$100_median": d["hold_ann_100"].median(), "share_markets_positive": (d["ann"] > 0).mean(),
                     "pass6.5_rate": d["pass"].median(), "market_pass_rate": d["bh_pass"].median(), "mean_5m": d["mean5"].median(), "market_mean_5m": d["bh_mean5"].median(),
                     "trades_yr": d["trades_yr"].median(), "dsr": dsr, "G1": True, "G2": bool(g2), "G3": bool(g3), "G4": bool(g4), "G5": bool(g5),
                     "gates": int(1 + g2 + g3 + g4 + g5), "why": idea["why"],
                     "breakeven_account": (2.0 * d["trades_yr"].median() / d["ann"].median()) if d["ann"].median() > 0 else float("inf")})
    T = pd.DataFrame(rows).sort_values(["gates", "pass6.5_rate"], ascending=False)
    T.to_csv(os.path.join(a.out, "scan.csv"), index=False)
    print("\n" + "=" * 100)
    print("TEST B: gap scanner, one idea at a time (fixed textbook settings, nothing tuned)")
    print(f"Pass rule: >= +6.5% in a 5-month period net of costs. Gate 5 counts all {n_trials} idea x market tests. Gate 6 (4-week forward paper test) is separate.")
    print("=" * 100)
    for _, r in T.iterrows():
        gl = "".join(f"G{k}{'+' if r['G'+str(k)] else '-'} " for k in (1, 2, 3, 4, 5))
        print(f"\n{r['idea']:22s} {gl} ({int(r['gates'])}/5 gates)   markets {int(r['markets'])}")
        print(f"   net annual (median market) {r['net_ann_median']*100:+.1f}%   on $100 with $2 fees {r['net_ann_$100_median']*100:+.1f}%   holdout 2018+ on $100 {r['holdout_ann_$100_median']*100:+.1f}%   markets positive {r['share_markets_positive']*100:.0f}%")
        print(f"   hits +6.5% per 5 months in {r['pass6.5_rate']*100:.0f}% of periods (just holding the market: {r['market_pass_rate']*100:.0f}%); mean per 5m {r['mean_5m']*100:+.1f}% vs holding {r['market_mean_5m']*100:+.1f}%; {r['trades_yr']:.1f} trades a year; deflated-Sharpe prob {r['dsr']:.2f}")
        be = r["breakeven_account"]
        print(f"   $2-per-trade fees stop eating the edge only above an account of about {'never (no edge before fees)' if not np.isfinite(be) else '$' + format(be, ',.0f')}")
        print(f"   why anyone would lose: {r['why']}")
    passed = T[T["gates"] >= 5]
    print(f"\nIdeas passing all of gates 1-5: {len(passed)} of {len(T)}" + (": " + ", ".join(passed['idea']) if len(passed) else ". None goes to the forward paper queue."))


if __name__ == "__main__":
    main()
