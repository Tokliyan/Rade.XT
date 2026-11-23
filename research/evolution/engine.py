"""
Evolution engine v2: 1,000 trading bots, walk-forward through history, 9 strategy families,
free macro + point-in-time news inputs.

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
FAMS = ["trend", "reversion", "breakout", "tsmom", "voltiming", "calendar", "xsmom", "pairs", "regime"]
NF = len(FAMS)
XS_WIN = np.array([20, 40, 60, 120, 250])     # look-backs for cross-market momentum ranking
XWIN = (1, 5, 20)                              # smoothing windows for macro / news features

# (lo, hi, log-scale?) for gene p1..p4 of each family; None = unused
RANGES = {
    0: [(5, 120, True), (1.5, 6.0, False), None, None],             # trend: fast window, slow/fast ratio
    1: [(5, 80, True), (0.5, 3.0, False), (-0.5, 1.0, False), (0.0, 1.0, False)],  # reversion: window, z entry, z exit, trend-filter flag
    2: [(0, G - 1, False), (0, G - 1, False), None, None],         # breakout: entry lookback idx, exit lookback idx
    3: [(20, 250, True), (-0.02, 0.10, False), None, None],        # tsmom: window, threshold
    4: [(10, 60, False), (0.08, 0.40, False), (0.0, 1.0, False), None],  # vol timing: window, vol cap, trend-filter flag
    5: [(0, 6, False), (0, 6, False), None, None],                 # calendar: last-N days of month, first-N days of next
    6: [(0, 4, False), (0.10, 0.50, False), None, None],           # xsmom: ranking window idx, top fraction held
    7: [(5, 80, True), (0.5, 3.0, False), (-0.5, 1.0, False), None],  # pairs: window, z entry (asset lags partner), z exit
    8: [(0, 1, False), (50, 250, True), None, None],               # regime: use-trend-filter flag, filter window
}
REV_FAMS = (1, 7)                                                  # families that get a max-hold gene

DEATH_DD = 0.30          # die after losing 30% from the period peak
CULL_DEFAULT = 0.10
WEIGHTS = np.array([0.4, 0.3, 0.2, 0.1])   # fitness memory: ~20 months
DD_PENALTY = 0.5
CRYPTO = {"BTC", "ETH"}


# --------------------------------------------------------------------------- extra inputs (macro + news)
def _zs(s, win=250, minp=60):
    m = s.rolling(win, min_periods=minp).mean().shift(1)
    sd = s.rolling(win, min_periods=minp).std().shift(1)
    return ((s - m) / sd.replace(0, np.nan)).clip(-4, 4)


def make_ext(dates, macro=None, news=None):
    """Causal, smoothed, z-scored extra inputs aligned to `dates`.
    Every value on day t uses only data published on or before day t (trailing z-scores, trailing means).
    Missing data (e.g. news before Wikipedia daily pages existed) becomes 0 = "nothing unusual"."""
    cols = {}
    if macro is not None and len(macro):
        m = macro.sort_index()
        m = m[~m.index.duplicated()].ffill()
        cols["vix_level"] = _zs(m["VIX"])
        cols["vix_jump5"] = _zs(m["VIX"].pct_change(5))
        cols["yield_curve"] = _zs(m["US10Y"] - m["US13W"], 500, 120)
        cols["rate_move60"] = _zs(m["US10Y"].diff(60), 500, 120)
    if news is not None and len(news):
        n = news[news["ok"] == 1].set_index("date").sort_index()
        n = n.reindex(pd.date_range(n.index[0], n.index[-1]))          # missing days stay NaN
        base = {"news_tone": n["pos"] - n["neg"], "news_volume": np.log(n["words"]),
                "news_conflict": n["conflict"], "news_fincrisis": n["fincrisis"], "news_ratesinfl": n["ratesinfl"],
                "news_trade": n["trade"], "news_energy": n["energy"], "news_health": n["health"], "news_disaster": n["disaster"]}
        for k, s in base.items():
            cols[k] = _zs(s, 250, 60)
    out = {}
    for k, s in cols.items():
        for w in XWIN:
            sm = s.rolling(w, min_periods=1).mean() if w > 1 else s
            out[f"{k}@{w}"] = sm.reindex(dates, method="ffill", limit=7).fillna(0.0).clip(-4, 4)
    return pd.DataFrame(out, index=dates)


# --------------------------------------------------------------------------- features
class Features:
    def __init__(self, prices: pd.DataFrame, ext: pd.DataFrame = None, base_cost=0.0025, crypto_cost=0.006,
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
        # cross-market momentum rank (0..1) of each asset's w-day return among all assets with data that day
        self.RANK = np.full((len(XS_WIN), A, T), np.nan)
        for i, w in enumerate(XS_WIN):
            d = df - df.shift(w)
            rk = d.rank(axis=1, pct=True)
            rk[(d.notna().sum(axis=1) < 8).to_numpy()] = np.nan
            self.RANK[i] = rk.to_numpy().T
        ym = np.asarray(self.dates.year * 100 + self.dates.month)
        s = pd.Series(ym)
        dom = s.groupby(s).cumcount().to_numpy()
        size = s.groupby(s).transform("size").to_numpy()
        self.dom = dom
        self.dtme = size - 1 - dom
        self.cost_vec = np.array([crypto_cost if n in CRYPTO else base_cost for n in self.names])
        self.mult = np.where(self.dates < pd.Timestamp(era_cut), era_mult, 1.0)
        if ext is not None and ext.shape[1]:
            assert ext.index.equals(self.dates), "ext must be aligned to the price dates"
            self.X = ext.to_numpy(float).T.copy()
            self.xnames = list(ext.columns)
        else:
            self.X = np.zeros((0, T))
            self.xnames = []
        self.NX = self.X.shape[0]

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


def rand_genome(fams, rng, n_assets, nx=0):
    n = len(fams)
    asset = rng.integers(0, n_assets, n)
    g = {"fam": fams.astype(int), "asset": asset, "partner": (asset + rng.integers(1, max(n_assets, 2), n)) % n_assets,
         "size": rng.uniform(0.25, 1.0, n), "stop": np.exp(rng.uniform(np.log(0.02), np.log(0.25), n)),
         "maxhold": np.full(n, 9999.0)}
    has = (rng.random(n) < 0.4) if nx > 0 else np.zeros(n, bool)
    if nx > 0:
        has |= (g["fam"] == 8)
    g["gfeat"] = np.where(has, rng.integers(0, max(nx, 1), n), -1)
    g["gthr"] = rng.uniform(0.5, 2.5, n)
    g["gdir"] = np.where(rng.random(n) < 0.5, 1.0, -1.0)
    for j in range(4):
        g[f"p{j+1}"] = np.zeros(n)
    for f in range(NF):
        idx = np.where(g["fam"] == f)[0]
        if not idx.size:
            continue
        for j, spec in enumerate(RANGES[f]):
            if spec is not None:
                g[f"p{j+1}"][idx] = _draw(*spec, rng, idx.size)
        if f in REV_FAMS:
            g["maxhold"][idx] = np.exp(rng.uniform(np.log(3), np.log(60), idx.size))
    return g


def take(g, idx):
    return {k: v[idx].copy() for k, v in g.items()}


def put(g, idx, src):
    for k in g:
        g[k][idx] = src[k]


def mutate(src, rng, n_assets, rate=0.35, nx=0):
    out = {k: v.copy() for k, v in src.items()}
    n = len(out["fam"])
    m = rng.random(n) < rate
    out["size"] = np.clip(out["size"] + m * rng.normal(0, 0.12, n), 0.25, 1.0)
    m = rng.random(n) < rate
    out["stop"] = np.clip(out["stop"] * np.exp(m * rng.normal(0, 0.25, n)), 0.02, 0.25)
    m = rng.random(n) < 0.06
    out["asset"] = np.where(m, rng.integers(0, n_assets, n), out["asset"])
    m = rng.random(n) < 0.06
    out["partner"] = np.where(m, rng.integers(0, n_assets, n), out["partner"])
    out["partner"] = np.where(out["partner"] == out["asset"], (out["asset"] + 1) % n_assets, out["partner"])
    if nx > 0:
        m = rng.random(n) < 0.08
        out["gfeat"] = np.where(m, rng.integers(0, nx, n), out["gfeat"])
        off = (rng.random(n) < 0.03) & (out["fam"] != 8)
        out["gfeat"] = np.where(off, -1, out["gfeat"])
        m = rng.random(n) < rate
        out["gthr"] = np.clip(out["gthr"] + m * rng.normal(0, 0.3, n), 0.3, 3.0)
        out["gdir"] = np.where(rng.random(n) < 0.03, -out["gdir"], out["gdir"])
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
        if f in REV_FAMS:
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
    gf = g["gfeat"].astype(int)
    has_g = (gf >= 0) & (F.NX > 0)
    gthr, gdir = g["gthr"], g["gdir"]
    gfi = np.maximum(gf, 0)

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
    if fi[6].size:
        i = fi[6]
        pre[6] = (a[i], np.clip(np.round(g["p1"][i]).astype(int), 0, len(XS_WIN) - 1), g["p2"][i])
    if fi[7].size:
        i = fi[7]
        pre[7] = (a[i], g["partner"][i], np.round(g["p1"][i]).astype(int), g["p2"][i], g["p3"][i])
    if fi[8].size:
        i = fi[8]
        pre[8] = (a[i], g["p1"][i] > 0.5, np.round(g["p2"][i]).astype(int))

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
        if 6 in pre:
            aa, wi, top = pre[6]
            rk = F.RANK[wi, aa, t]
            cur = inpos[fi[6]]
            w[fi[6]] = ~np.isnan(rk) & ((rk >= 1 - top) | (cur & (rk >= 1 - top - 0.15)))
        if 7 in pre:
            aa, bb, win, ze, zx = pre[7]
            lo = t + 1 - win
            ok = (lo >= F.start[aa] + 1) & (lo >= F.start[bb] + 1)
            lo = np.maximum(lo, 0)
            rel = (F.Rc[aa, t + 1] - F.Rc[aa, lo]) - (F.Rc[bb, t + 1] - F.Rc[bb, lo])
            va = (F.R2c[aa, t + 1] - F.R2c[aa, lo]) / win
            vb = (F.R2c[bb, t + 1] - F.R2c[bb, lo]) / win
            z = rel / np.sqrt(win * (va + vb) + 1e-12)
            cur = inpos[fi[7]]
            w[fi[7]] = ok & (((~cur) & (z < -ze)) | (cur & (z <= zx)))
        if 8 in pre:
            aa, filt, win = pre[8]
            m, ok = F.sma(aa, win, t)
            w[fi[8]] = np.where(filt, ok & (LP[aa, t] > m), True)
        w &= ~np.isnan(C[a, t])
        if has_g.any():
            xv = F.X[gfi, t]
            w &= ~(has_g & (gdir * xv > gthr))          # the gate: step aside when the chosen macro/news input is extreme
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


def pick_committee(fit, fam, K=10, per_fam=3, exclude=None):
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



def net100_of(F, g, ret, trades, t0):
    """Approximate the period return for a $100 account paying a flat $2 per trade instead of the model's % cost."""
    model = F.cost_vec[g["asset"]] * g["size"] * F.mult[t0]
    return ret - trades * (0.02 - model)


def evolve(F: Features, pop=1000, cull=CULL_DEFAULT, seed=0, start="1998-01-01", holdout="2018-01-01",
           K=10, per_fam=3, immigrants=0.05, cost_scale=1.0, verbose=False):
    """Walk-forward evolution. Also records every bot's every period (for the Hall of Fame) and
    freezes the top K (selected on data strictly before `holdout`) for the Frozen Ten test."""
    rng = np.random.default_rng(seed)
    A, NX = F.A, F.NX
    fams = np.arange(pop) % NF
    g = rand_genome(fams, rng, A, NX)
    hist = np.full((pop, len(WEIGHTS)), np.nan)
    bnds = boundaries(F.dates, start)
    bnds = bnds + [F.T - 1] if bnds[-1] < F.T - 2 else bnds
    hold_idx = int(np.searchsorted(F.dates.values, np.datetime64(pd.Timestamp(holdout))))
    births = pop
    committee = None
    frozen = None
    rows = []
    # ---- identities, parents, lineages, genome archive, per-period records
    bid = np.arange(pop)
    lin_slot = bid.copy()
    next_id = pop
    arch = [(bid.copy(), np.full(pop, -1), bid.copy(), np.zeros(pop, int), take(g, np.arange(pop)))]
    rec = {"bid": [], "gen": [], "t0": [], "days": [], "ret": [], "ddmax": [], "trades": [], "dead": [], "net100": []}

    def register(slots, parents, lineages, gen):
        nonlocal next_id
        ids = np.arange(next_id, next_id + len(slots))
        next_id += len(slots)
        bid[slots] = ids
        lin_slot[slots] = ids if lineages is None else lineages
        arch.append((ids, parents, lin_slot[slots].copy(), np.full(len(slots), gen), take(g, slots)))

    for b in range(len(bnds) - 1):
        t0, t1 = bnds[b], bnds[b + 1]
        res = run(F, g, t0, t1, cost_scale=cost_scale)
        ret = res["eq"] / 100.0 - 1.0
        score = ret - DD_PENALTY * res["ddmax"]
        rec["bid"].append(bid.copy()); rec["gen"].append(np.full(pop, b)); rec["t0"].append(np.full(pop, t0)); rec["days"].append(np.full(pop, t1 - t0))
        rec["ret"].append(ret); rec["ddmax"].append(res["ddmax"]); rec["trades"].append(res["trades"]); rec["dead"].append(res["dead"])
        rec["net100"].append(net100_of(F, g, ret, res["trades"], t0))
        row = {"start": F.dates[t0], "end": F.dates[t1], "t0": t0, "t1": t1, "days": t1 - t0, "pop_mean": float(ret.mean()),
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
        committee = pick_committee(fit, g["fam"], K, per_fam)
        if frozen is None and t1 == hold_idx:
            frozen = (take(g, committee), t1, bid[committee].copy())      # genomes chosen on data strictly before the holdout
        # ---- selection: immigrants, then per-island kill & clone
        protect = np.zeros(pop, bool)
        protect[committee] = True
        n_imm = int(immigrants * pop)
        order = np.argsort(fit + protect * 1e6)
        imm = order[:n_imm]
        newg = rand_genome(rng.integers(0, NF, n_imm), rng, A, NX)
        put(g, imm, newg)
        hist[imm] = np.nan
        register(imm, np.full(n_imm, -1), None, b + 1)
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
            kids = mutate(take(g, winners), rng, A, nx=NX)
            swap = rng.random(losers.size) < 0.15
            if swap.any():
                mates = winners[rng.integers(0, winners.size, losers.size)]
                for j in range(1, 5):
                    kids[f"p{j}"] = np.where(swap & (g["fam"][mates] == f), g[f"p{j}"][mates], kids[f"p{j}"])
            parent_ids, parent_lin = bid[winners].copy(), lin_slot[winners].copy()
            put(g, losers, kids)
            hist[losers] = hist[winners]
            register(losers, parent_ids, parent_lin, b + 1)
            births += losers.size
        if verbose and b % 10 == 0:
            print(f"  gen {b:2d} {F.dates[t0].date()}  pop {ret.mean():+.3f}  comm_next {rows[-1].get('comm_ret', float('nan')):+.3f}")
    perf = pd.DataFrame({k: np.concatenate(v) for k, v in rec.items()})
    gen_tbl = pd.concat([pd.DataFrame({"bid": ids, "parent": par, "lineage": lin, "birth_gen": bg, **{k: v for k, v in gg.items()}})
                         for ids, par, lin, bg, gg in arch], ignore_index=True)
    return {"rows": pd.DataFrame(rows), "births": births, "final_genomes": g, "frozen": frozen, "perf": perf,
            "genomes": gen_tbl, "bnds": bnds, "hold_idx": hold_idx}


def window_returns(F: Features, g, windows, cost_scale=1.0):
    """Run genomes through each (t0, t1) window from a flat start. Returns net-of-model-cost returns, trades, ddmax matrices [N, W]."""
    N = len(g["fam"])
    R = np.zeros((N, len(windows))); Tr = np.zeros_like(R); DD = np.zeros_like(R); N100 = np.zeros_like(R)
    for w, (a, b) in enumerate(windows):
        res = run(F, g, a, b, cost_scale=cost_scale)
        R[:, w] = res["eq"] / 100.0 - 1.0
        Tr[:, w] = res["trades"]
        DD[:, w] = res["ddmax"]
        N100[:, w] = net100_of(F, g, R[:, w], Tr[:, w], a)
    return R, Tr, DD, N100


def freeze_and_test(F: Features, frozen, cost_scale=1.0):
    gfz, t0 = frozen[0], frozen[1]
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


def buyhold_windows(F: Features, windows):
    """Buy-and-hold return of every asset in every window (NaN if the asset had no data at the window start). [A, W]"""
    out = np.full((F.A, len(windows)), np.nan)
    for w, (a, b) in enumerate(windows):
        ok = F.start <= a
        out[ok, w] = F.C[ok, b] / F.C[ok, a] - 1.0
    return out


def block_shuffle_prices(prices: pd.DataFrame, seed, block=20):
    """Null market: re-order the real daily returns in blocks. Keeps each asset's return distribution, volatility clusters
    and cross-asset links inside a block, but destroys every real link between today and tomorrow beyond ~a month."""
    rng = np.random.default_rng(seed)
    px = prices.sort_index().ffill()
    ret = px.pct_change()
    T = len(ret)
    nb = int(np.ceil(T / block))
    starts = rng.integers(0, T - block, nb)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:T]
    sh = ret.iloc[idx].copy()
    for c in sh.columns:                                       # rows where the asset did not exist yet: draw from its own returns
        col = sh[c].to_numpy().copy()
        pool = ret[c].dropna().to_numpy()
        bad = np.isnan(col)
        col[bad] = rng.choice(pool, bad.sum())
        sh[c] = col
    sh.index = ret.index
    first = {c: px[c].first_valid_index() for c in px.columns}
    out = 100 * (1 + sh.clip(-0.4, 0.4)).cumprod()
    for c in out.columns:
        out.loc[out.index < first[c], c] = np.nan
    return out


def block_shuffle_rows(df: pd.DataFrame, seed, block=20):
    """Same block shuffle for the extra inputs (macro/news), independently of prices, so any link between them and returns is cut."""
    rng = np.random.default_rng(seed + 7919)
    T = len(df)
    nb = int(np.ceil(T / block))
    starts = rng.integers(0, max(T - block, 1), nb)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:T]
    return pd.DataFrame(df.to_numpy()[idx], index=df.index, columns=df.columns)
