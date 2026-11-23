"""
Evolution engine: 1,000 trading bots, walk-forward through history.

Standalone research tool. It never touches Supabase, the live agents or the
dashboard.

How it works (plain version)
  * A bot is a row of numbers (a "genome"): which market, which strategy family
    (6 of them), look-back windows, thresholds, stop-loss, position size.
  * Every bot trades the same history day by day, seeing only data up to
    "today", with real costs charged on every trade. Each bot is isolated: it
    only has its own cash/position row. No containers needed.
  * Every 5 months is a generation: rank the bots, kill the worst, clone the
    best with small random changes. Repeat until today.
  * Bots die (are flat for the rest of the period) if they lose 30% from peak.
  * Diversity guards: the population is split into 6 "islands" (one per
    strategy family) that select within themselves, plus 5% random newcomers
    each generation, so the population cannot collapse into one idea.

Honesty rules baked in
  * Features are causal (verified by test_engine.py): no bot can see the future.
  * A signal at the close of day t is executed at the close of day t+1.
  * The headline number is NEVER the best bot's score. It is how the bots we
    SELECTED do in the NEXT period (and, separately, a frozen committee run on
    a final holdout era nobody tuned against).
"""
from math import sqrt
from statistics import NormalDist

import numpy as np
import pandas as pd

GRID = np.array([5, 8, 10, 13, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250])
G = len(GRID)
FAMS = ["trend", "reversion", "breakout", "tsmom", "voltiming", "calendar"]
NF = len(FAMS)

# (lo, hi, log-scale?) for gene p1..p4 of each family; None = unused
RANGES = {
    0: [(5, 120, True), (1.5, 6.0, False), None, None],             # trend: fast window, slow/fast ratio
    1: [(5, 80, True), (0.5, 3.0, False), (-0.5, 1.0, False), (0.0, 1.0, False)],  # reversion: window, z entry, z exit, trend-filter flag
    2: [(0, G - 1, False), (0, G - 1, False), None, None],         # breakout: entry lookback idx, exit lookback idx
    3: [(20, 250, True), (-0.02, 0.10, False), None, None],        # tsmom: window, threshold
    4: [(10, 60, False), (0.08, 0.40, False), (0.0, 1.0, False), None],  # vol timing: window, vol cap, trend-filter flag
    5: [(0, 6, False), (0, 6, False), None, None],                 # calendar: last-N days of month, first-N days of next
}

DEATH_DD = 0.30          # die after losing 30% from the period peak
CULL_DEFAULT = 0.10
WEIGHTS = np.array([0.4, 0.3, 0.2, 0.1])   # fitness memory: ~20 months
DD_PENALTY = 0.5
CRYPTO = {"BTC"}


# --------------------------------------------------------------------------- features
class Features:
    def __init__(self, prices: pd.DataFrame, base_cost=0.0025, crypto_cost=0.006,
                 era_cut="2006-01-01", era_mult=1.5):
        prices = prices.sort_index().ffill()
        self.dates = prices.index
        self.names = list(prices.columns)
        C = prices.to_numpy(float).T.copy()
        A, T = C.shape
        self.A, self.T = A, T
        valid = ~np.isnan(C)
        self.start = np.array([int(np.argmax(valid[a])) if valid[a].any() else T for a in range(A)])
        self.C = C
        LP = np.log(C)
        self.LP = LP
        R = np.zeros_like(C)
        both = valid[:, 1:] & valid[:, :-1]
        R[:, 1:] = np.where(both, C[:, 1:] / C[:, :-1] - 1.0, 0.0)
        self.bad_prints = int((np.abs(R) > 0.5).sum())
        R[np.abs(R) > 0.5] = 0.0
        self.R = R
        z = np.zeros((A, 1))
        LPf = np.nan_to_num(LP)
        self.LPc = np.hstack([z, np.cumsum(LPf, axis=1)])
        self.LP2c = np.hstack([z, np.cumsum(LPf ** 2, axis=1)])
        self.Rc = np.hstack([z, np.cumsum(R, axis=1)])
        self.R2c = np.hstack([z, np.cumsum(R ** 2, axis=1)])
        df = pd.DataFrame(LP.T)
        self.HI = np.stack([df.rolling(w, min_periods=w).max().shift(1).to_numpy().T for w in GRID])
        self.LO = np.stack([df.rolling(w, min_periods=w).min().shift(1).to_numpy().T for w in GRID])
        ym = np.asarray(self.dates.year * 100 + self.dates.month)
        s = pd.Series(ym)
        dom = s.groupby(s).cumcount().to_numpy()
        size = s.groupby(s).transform("size").to_numpy()
        self.dom = dom
        self.dtme = size - 1 - dom
        self.cost_vec = np.array([crypto_cost if n in CRYPTO else base_cost for n in self.names])
        self.mult = np.where(self.dates < pd.Timestamp(era_cut), era_mult, 1.0)

    def sma(self, a, w, t):
        lo = t + 1 - w
        ok = lo >= self.start[a]
        v = (self.LPc[a, t + 1] - self.LPc[a, np.maximum(lo, 0)]) / w
        return v, ok

    def std(self, a, w, t, m):
        lo = np.maximum(t + 1 - w, 0)
        v = (self.LP2c[a, t + 1] - self.LP2c[a, lo]) / w - m * m
        return np.sqrt(np.maximum(v, 1e-10))


# --------------------------------------------------------------------------- genomes
def _draw(lo, hi, lg, rng, n):
    if lg:
        return np.exp(rng.uniform(np.log(lo), np.log(hi), n))
    return rng.uniform(lo, hi, n)


def rand_genome(fams, rng, n_assets):
    n = len(fams)
    g = {"fam": fams.astype(int), "asset": rng.integers(0, n_assets, n),
         "size": rng.uniform(0.25, 1.0, n), "stop": np.exp(rng.uniform(np.log(0.02), np.log(0.25), n)),
         "maxhold": np.full(n, 9999.0)}
    for j in range(4):
        g[f"p{j+1}"] = np.zeros(n)
    for f in range(NF):
        idx = np.where(g["fam"] == f)[0]
        if not idx.size:
            continue
        for j, spec in enumerate(RANGES[f]):
            if spec is not None:
                g[f"p{j+1}"][idx] = _draw(*spec, rng, idx.size)
        if f == 1:
            g["maxhold"][idx] = np.exp(rng.uniform(np.log(3), np.log(60), idx.size))
    return g


def take(g, idx):
    return {k: v[idx].copy() for k, v in g.items()}


def put(g, idx, src):
    for k in g:
        g[k][idx] = src[k]


def mutate(src, rng, n_assets, rate=0.35):
    out = {k: v.copy() for k, v in src.items()}
    n = len(out["fam"])
    m = rng.random(n) < rate
    out["size"] = np.clip(out["size"] + m * rng.normal(0, 0.12, n), 0.25, 1.0)
    m = rng.random(n) < rate
    out["stop"] = np.clip(out["stop"] * np.exp(m * rng.normal(0, 0.25, n)), 0.02, 0.25)
    m = rng.random(n) < 0.06
    out["asset"] = np.where(m, rng.integers(0, n_assets, n), out["asset"])
    for f in range(NF):
        idx = np.where(out["fam"] == f)[0]
        if not idx.size:
            continue
        for j, spec in enumerate(RANGES[f]):
            if spec is None:
                continue
            lo, hi, lg = spec
            k = f"p{j+1}"
            m = rng.random(idx.size) < rate
            if lg:
                out[k][idx] = np.clip(out[k][idx] * np.exp(m * rng.normal(0, 0.2, idx.size)), lo, hi)
            else:
                out[k][idx] = np.clip(out[k][idx] + m * rng.normal(0, 0.15 * (hi - lo), idx.size), lo, hi)
        if f == 1:
            m = rng.random(idx.size) < rate
            out["maxhold"][idx] = np.clip(out["maxhold"][idx] * np.exp(m * rng.normal(0, 0.25, idx.size)), 3, 60)
    return out


# --------------------------------------------------------------------------- simulation
def run(F: Features, g, t0, t1, rec=False, cost_scale=1.0):
    """Simulate genomes g over trading days [t0, t1). All bots start with 100, flat."""
    N = len(g["fam"])
    a, size, stop, maxhold = g["asset"], g["size"], g["stop"], g["maxhold"]
    C, LP = F.C, F.LP
    eq = np.full(N, 100.0)
    peak = eq.copy()
    ddmax = np.zeros(N)
    dead = np.zeros(N, bool)
    inpos = np.zeros(N, bool)
    entry = np.ones(N)
    held = np.zeros(N)
    blocked = np.zeros(N, bool)
    trades = np.zeros(N)
    costv = F.cost_vec[a] * cost_scale * size

    fi = [np.where(g["fam"] == f)[0] for f in range(NF)]
    pre = {}
    if fi[0].size:
        i = fi[0]
        wf = np.round(g["p1"][i]).astype(int)
        ws = np.clip(np.round(g["p1"][i] * g["p2"][i]), wf + 1, 300).astype(int)
        pre[0] = (a[i], wf, ws)
    if fi[1].size:
        i = fi[1]
        pre[1] = (a[i], np.round(g["p1"][i]).astype(int), g["p2"][i], g["p3"][i], g["p4"][i] > 0.5)
    if fi[2].size:
        i = fi[2]
        pre[2] = (a[i], np.clip(np.round(g["p1"][i]).astype(int), 0, G - 1), np.clip(np.round(g["p2"][i]).astype(int), 0, G - 1))
    if fi[3].size:
        i = fi[3]
        pre[3] = (a[i], np.round(g["p1"][i]).astype(int), g["p2"][i])
    if fi[4].size:
        i = fi[4]
        pre[4] = (a[i], np.round(g["p1"][i]).astype(int), g["p2"][i], g["p3"][i] > 0.5)
    if fi[5].size:
        i = fi[5]
        pre[5] = (a[i], np.round(g["p1"][i]).astype(int), np.round(g["p2"][i]).astype(int))

    def want_at(t):
        w = np.zeros(N, bool)
        if 0 in pre:
            aa, wf, ws = pre[0]
            m1, o1 = F.sma(aa, wf, t)
            m2, o2 = F.sma(aa, ws, t)
            w[fi[0]] = o1 & o2 & (m1 > m2)
        if 1 in pre:
            aa, win, ze, zx, filt = pre[1]
            m, ok = F.sma(aa, win, t)
            s = F.std(aa, win, t, m)
            z = (LP[aa, t] - m) / s
            m200, ok200 = F.sma(aa, np.full(aa.size, 200), t)
            fl = np.where(filt, ok200 & (LP[aa, t] > m200), True)
            cur = inpos[fi[1]]
            w[fi[1]] = ok & fl & (((~cur) & (z < -ze)) | (cur & (z <= zx)))
        if 2 in pre:
            aa, gi, go = pre[2]
            lp = LP[aa, t]
            cur = inpos[fi[2]]
            w[fi[2]] = (lp > F.HI[gi, aa, t]) | (cur & ~(lp < F.LO[go, aa, t]))
        if 3 in pre:
            aa, win, thr = pre[3]
            lo = t - win
            ok = lo >= F.start[aa]
            r = LP[aa, t] - LP[aa, np.maximum(lo, 0)]
            w[fi[3]] = ok & (r > thr)
        if 4 in pre:
            aa, win, cap, filt = pre[4]
            lo = t + 1 - win
            ok = lo >= F.start[aa] + 1
            lo = np.maximum(lo, 0)
            mean = (F.Rc[aa, t + 1] - F.Rc[aa, lo]) / win
            var = (F.R2c[aa, t + 1] - F.R2c[aa, lo]) / win - mean * mean
            vol = np.sqrt(np.maximum(var, 0)) * sqrt(252)
            m100, ok100 = F.sma(aa, np.full(aa.size, 100), t)
            fl = np.where(filt, ok100 & (LP[aa, t] > m100), True)
            w[fi[4]] = ok & (vol < cap) & fl
        if 5 in pre:
            aa, tin, tout = pre[5]
            w[fi[5]] = (F.dtme[t] < tin) | (F.dom[t] < tout)
        w &= ~np.isnan(C[a, t])
        return w & ~dead

    pending = want_at(t0 - 1)
    hist = np.zeros((t1 - t0, N)) if rec else None
    for t in range(t0, t1):
        r = F.R[a, t]
        eq = np.where(inpos, eq * (1.0 + size * r), eq)
        peak = np.maximum(peak, eq)
        dd = 1.0 - eq / peak
        ddmax = np.maximum(ddmax, dd)
        nd = (~dead) & (dd >= DEATH_DD)
        if nd.any():
            dead |= nd
            inpos &= ~nd
            pending &= ~nd
        px = C[a, t]
        st = inpos & (px / entry - 1.0 <= -stop)
        if st.any():
            eq[st] *= 1.0 - costv[st] * F.mult[t]
            trades[st] += 1
            inpos[st] = False
            blocked[st] = True
            pending[st] = False
        chg = (pending != inpos) & ~dead
        if chg.any():
            eq[chg] *= 1.0 - costv[chg] * F.mult[t]
            trades[chg] += 1
            ent = chg & pending
            entry[ent] = px[ent]
            held[ent] = 0
            inpos[chg] = pending[chg]
        held += inpos
        w = want_at(t)
        blocked &= w
        mh = inpos & (held >= maxhold)
        blocked |= mh
        w &= ~blocked
        pending = w
        if rec:
            hist[t - t0] = eq
    return {"eq": eq, "ddmax": ddmax, "dead": dead, "trades": trades, "hist": hist}


# --------------------------------------------------------------------------- stats
def curve_stats(eq_curve, days_per_year=252):
    eq_curve = np.asarray(eq_curve, float)
    n = len(eq_curve)
    if n < 2:
        return {"ann": 0.0, "vol": 0.0, "sharpe": 0.0, "maxdd": 0.0, "total": 0.0}
    r = eq_curve[1:] / eq_curve[:-1] - 1
    yrs = n / days_per_year
    total = eq_curve[-1] / eq_curve[0] - 1
    ann = (eq_curve[-1] / eq_curve[0]) ** (1 / yrs) - 1 if eq_curve[-1] > 0 else -1.0
    vol = float(np.std(r) * sqrt(days_per_year))
    sharpe = float(np.mean(r) / np.std(r) * sqrt(days_per_year)) if np.std(r) > 0 else 0.0
    pk = np.maximum.accumulate(eq_curve)
    return {"ann": float(ann), "vol": vol, "sharpe": sharpe, "maxdd": float(np.max(1 - eq_curve / pk)), "total": float(total)}


def deflated_sharpe_prob(sr, n_obs, n_trials, skew=0.0, kurt=3.0):
    """Probability the true Sharpe is > 0 after allowing for the best of n_trials tries (Bailey & Lopez de Prado)."""
    nd = NormalDist()
    g = 0.5772156649
    n_trials = max(int(n_trials), 1)
    if n_trials == 1:
        sr0 = 0.0
    else:
        sr0 = sqrt(1.0 / max(n_obs, 2)) * ((1 - g) * nd.inv_cdf(1 - 1.0 / n_trials) + g * nd.inv_cdf(1 - 1.0 / (n_trials * np.e)))
    den = 1 - skew * sr + (kurt - 1) / 4.0 * sr * sr
    if den <= 0:
        return 0.0
    return nd.cdf((sr - sr0) * sqrt(max(n_obs - 1, 1)) / sqrt(den))


# --------------------------------------------------------------------------- evolution
def boundaries(dates, start="1998-01-01", months=5):
    end = dates[-1]
    grid = pd.date_range(start, end, freq=f"{months}MS")
    idx = [int(np.searchsorted(dates.values, np.datetime64(d))) for d in grid]
    idx = sorted(set(i for i in idx if 260 < i < len(dates)))
    return idx


def fitness_of(hist):
    ok = ~np.isnan(hist)
    num = np.nansum(hist * WEIGHTS, axis=1)
    den = (ok * WEIGHTS).sum(axis=1)
    return np.where(den > 0, num / np.maximum(den, 1e-12), -9.0)


def pick_committee(fit, fam, K=20, per_fam=5, exclude=None):
    order = np.argsort(-fit)
    cnt = np.zeros(NF, int)
    chosen = []
    for i in order:
        if exclude is not None and exclude[i]:
            continue
        f = int(fam[i])
        if cnt[f] < per_fam:
            chosen.append(int(i))
            cnt[f] += 1
        if len(chosen) >= K:
            break
    return np.array(chosen, int)


def evolve(F: Features, pop=1000, cull=CULL_DEFAULT, seed=0, start="1998-01-01", holdout="2018-01-01",
           K=20, immigrants=0.05, cost_scale=1.0, verbose=False):
    rng = np.random.default_rng(seed)
    A = F.A
    fams = np.arange(pop) % NF
    g = rand_genome(fams, rng, A)
    hist = np.full((pop, len(WEIGHTS)), np.nan)
    bnds = boundaries(F.dates, start)
    bnds = bnds + [F.T - 1] if bnds[-1] < F.T - 2 else bnds
    hold_idx = int(np.searchsorted(F.dates.values, np.datetime64(pd.Timestamp(holdout))))
    births = pop
    committee = None
    frozen = None
    rows = []
    for b in range(len(bnds) - 1):
        t0, t1 = bnds[b], bnds[b + 1]
        res = run(F, g, t0, t1, cost_scale=cost_scale)
        ret = res["eq"] / 100.0 - 1.0
        score = ret - DD_PENALTY * res["ddmax"]
        row = {"start": F.dates[t0], "end": F.dates[t1], "days": t1 - t0, "pop_mean": float(ret.mean()),
               "pop_med": float(np.median(ret)), "best_ret": float(ret.max()), "dead_frac": float(res["dead"].mean()),
               "era": "hold" if t0 >= hold_idx else "train"}
        if committee is not None:
            c = committee
            row["comm_ret"] = float(ret[c].mean())
            row["comm_trades"] = float(res["trades"][c].mean())
            row["comm_cost_gap"] = float(np.mean(res["trades"][c] * (0.02 - F.cost_vec[g["asset"][c]] * g["size"][c])))
        rows.append(row)
        hist[:, 1:] = hist[:, :-1]
        hist[:, 0] = score
        fit = fitness_of(hist)
        committee = pick_committee(fit, g["fam"], K)
        if frozen is None and t1 == hold_idx:
            frozen = (take(g, committee), t1)      # freeze genomes selected on data strictly before the holdout
        # ---- selection: immigrants, then per-island kill & clone
        protect = np.zeros(pop, bool)
        protect[committee] = True
        n_imm = int(immigrants * pop)
        order = np.argsort(fit + protect * 1e6)
        imm = order[:n_imm]
        newg = rand_genome(rng.integers(0, NF, n_imm), rng, A)
        put(g, imm, newg)
        hist[imm] = np.nan
        births += n_imm
        taken = np.zeros(pop, bool)
        taken[imm] = True
        for f in range(NF):
            idx = np.where((g["fam"] == f) & ~taken)[0]
            n = idx.size
            k = min(max(1, int(round(cull * n))), n // 2)
            if n < 4:
                continue
            o = idx[np.argsort(fit[idx])]
            losers, winners = o[:k], o[::-1][:k]
            losers = losers[~protect[losers]]
            winners = winners[: losers.size]
            if not losers.size:
                continue
            kids = mutate(take(g, winners), rng, A)
            swap = rng.random(losers.size) < 0.15
            if swap.any():
                mates = winners[rng.integers(0, winners.size, losers.size)]
                for j in range(1, 5):
                    kids[f"p{j}"] = np.where(swap & (g["fam"][mates] == f), g[f"p{j}"][mates], kids[f"p{j}"])
            put(g, losers, kids)
            hist[losers] = hist[winners]
            births += losers.size
        if verbose and b % 10 == 0:
            print(f"  gen {b:2d} {F.dates[t0].date()}  pop {ret.mean():+.3f}  comm_next {rows[-1].get('comm_ret', float('nan')):+.3f}")
    out = {"rows": pd.DataFrame(rows), "births": births, "final_genomes": g}
    out["frozen"] = frozen
    return out


def freeze_and_test(F: Features, frozen, cost_scale=1.0):
    gfz, t0 = frozen
    res = run(F, gfz, t0, F.T, rec=True, cost_scale=cost_scale)
    port = res["hist"].mean(axis=1)
    yrs = (F.T - t0) / 252
    tr = res["trades"] / yrs
    drag = float(np.mean(tr * (0.02 - F.cost_vec[gfz["asset"]] * gfz["size"])))
    return {"curve": port, "stats": curve_stats(np.r_[100.0, port]), "trades_per_year": float(tr.mean()),
            "drag_100": drag, "dead": int(res["dead"].sum()), "fam": gfz["fam"], "ind_ret": res["eq"] / 100 - 1,
            "t0": t0}


def benchmark_stats(F: Features, t0, t1):
    out = {}
    for name in ("ASX200", "SP500"):
        if name in F.names:
            a = F.names.index(name)
            s = F.C[a, t0:t1]
            s = s[~np.isnan(s)]
            if len(s) > 10:
                out[name] = curve_stats(s)
    R = F.R[:, t0:t1]
    avail = ~np.isnan(F.C[:, t0:t1])
    n = np.maximum(avail.sum(axis=0), 1)
    rp = (R * avail).sum(axis=0) / n
    out["EqualWeight"] = curve_stats(np.r_[1.0, np.cumprod(1 + rp)])
    return out
