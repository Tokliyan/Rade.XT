"""
Validation of the evolution engine on fake markets. Run: python test_engine.py

1. Causality   - changing FUTURE prices AND FUTURE news/macro inputs must not change any bot's PAST equity
                 (this is the "bot only knows the past and present" guarantee, including the news gates).
2. Null market - pure random walks. The engine must find nothing real.
3. Planted edge - persistent-trend assets. The engine should find it.
4. News wiring  - a fake news input that really predicts the next days must be found and used by gated bots;
                  a news input that is pure noise must not help.
"""
import sys
import numpy as np
import pandas as pd
import data
import engine as E


def fake_ext(idx, seed, n=6):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(rng.normal(size=(len(idx), n)), index=idx, columns=[f"x{i}@1" for i in range(n)])


def causality():
    df = data.synthetic("planted", seed=3, n_assets=14)
    ext = fake_ext(df.index, 4)
    cut = 5000
    F1 = E.Features(df, ext)
    df2 = df.copy()
    rng = np.random.default_rng(9)
    df2.iloc[cut + 1:] = df2.iloc[cut + 1:] * np.exp(np.cumsum(rng.normal(0, 0.03, (len(df) - cut - 1, df.shape[1])), axis=0))
    ext2 = ext.copy()
    ext2.iloc[cut + 1:] = rng.normal(size=ext2.iloc[cut + 1:].shape) * 3          # future news/macro rewritten
    F2 = E.Features(df2, ext2)
    g = E.rand_genome(np.arange(900) % E.NF, np.random.default_rng(5), F1.A, F1.NX)
    r1 = E.run(F1, g, 3000, cut + 300, rec=True)["hist"]
    r2 = E.run(F2, g, 3000, cut + 300, rec=True)["hist"]
    n = cut - 3000 + 1
    same = np.allclose(r1[:n], r2[:n], rtol=0, atol=1e-9)
    gated = int((g["gfeat"] >= 0).sum())
    print(f"[1] causality: past equity unchanged when future prices AND future news inputs are rewritten ({gated} gated bots, all 9 families) -> {'PASS' if same else 'FAIL'}")
    # also: the z-score builder itself must not look ahead
    idx = pd.bdate_range("2010-01-01", periods=1500)
    macro = pd.DataFrame({"VIX": 20 + np.cumsum(np.random.default_rng(1).normal(0, .5, 1500)), "US10Y": 3 + np.cumsum(np.random.default_rng(2).normal(0, .02, 1500)),
                          "US13W": 1 + np.cumsum(np.random.default_rng(3).normal(0, .01, 1500))}, index=idx)
    a = E.make_ext(idx, macro, None)
    m2 = macro.copy()
    m2.iloc[1000:] = m2.iloc[1000:] * 5
    b = E.make_ext(idx, m2, None)
    ok2 = np.allclose(a.iloc[:1000].to_numpy(), b.iloc[:1000].to_numpy())
    print(f"[1b] macro/news feature builder uses only data up to each day -> {'PASS' if ok2 else 'FAIL'}")
    return same and ok2


def evo_stats(kind, seeds, ext_fn=None, n_assets=12):
    sel, frozen_ann = [], []
    for s in seeds:
        df = data.synthetic(kind, seed=s, n_assets=n_assets)
        ext = ext_fn(df, s) if ext_fn else None
        F = E.Features(df, ext)
        out = E.evolve(F, pop=1000, cull=0.1, seed=s)
        rows = out["rows"].dropna(subset=["comm_ret"])
        sel.append((rows["comm_ret"] - rows["pop_mean"]).to_numpy())
        fz = E.freeze_and_test(F, out["frozen"])
        frozen_ann.append(fz["stats"]["ann"])
    allsel = np.concatenate(sel)
    t = allsel.mean() / (allsel.std() / np.sqrt(len(allsel)))
    return allsel.mean(), t, np.array(frozen_ann)


def news_planted(df, s):
    """x0 = a signal that is high BEFORE crashes in asset A0 (planted: A0 drops after x0>1.5); x1.. noise."""
    ext = fake_ext(df.index, 100 + s, 4)
    return ext


def main():
    ok = causality()
    print("[2] null market (no edge anywhere), 4 seeds x 70 generations, with noise news inputs")
    m, t, fz = evo_stats("random", [11, 12, 13, 14], lambda df, s: fake_ext(df.index, 50 + s, 6))
    print(f"    selected-minus-population next-period return: {m*100:+.2f}% per 5 months (t={t:+.1f}); frozen holdout ann: "
          f"{np.round(fz*100,1)}%  mean {fz.mean()*100:+.1f}%")
    null_ok = t < 3.0 and fz.mean() < 0.02
    print("    ->", "PASS: no phantom edge" if null_ok else "FAIL: engine found money in noise")
    print("[3] planted trend edge, 4 seeds")
    m2, t2, fz2 = evo_stats("planted", [21, 22, 23, 24], lambda df, s: fake_ext(df.index, 60 + s, 6))
    print(f"    selected-minus-population next-period return: {m2*100:+.2f}% per 5 months (t={t2:+.1f}); frozen holdout ann: "
          f"{np.round(fz2*100,1)}%  mean {fz2.mean()*100:+.1f}%")
    plant_ok = t2 > 3.0 and fz2.mean() > 0.02
    print("    ->", "PASS: real edge detected" if plant_ok else "WEAK: edge not clearly detected")
    # 4. news wiring: both assets suffer sudden drops; only a news input announces them. Same prices, real vs scrambled warning.
    print("[4] news wiring: assets with sudden drops that a news input announces a day ahead, vs the SAME prices with the warning scrambled")
    res = []
    for scramble in (False, True):
        outs = []
        for s in (31, 32, 33):
            rng = np.random.default_rng(s)
            idx = pd.bdate_range("1993-01-01", "2026-11-20")
            T = len(idx)
            warn = np.zeros(T)
            r0 = rng.standard_normal(T) * 0.010 + 0.0030
            r1 = rng.standard_normal(T) * 0.010 + 0.0030
            ev = rng.random(T) < 0.03
            for t in np.flatnonzero(ev):
                if t + 3 < T:
                    warn[t:t + 4] = 3.0          # a news burst lasting 4 days...
                    for r in (r0, r1):
                        r[t + 1] -= 0.035         # ...then a drop that cannot be dodged...
                        r[t + 2] -= 0.02          # ...and two more drops a bot that heeds the news can dodge
                        r[t + 3] -= 0.02
            px = pd.DataFrame({"A0": 100 * np.exp(np.cumsum(r0)), "A1": 100 * np.exp(np.cumsum(r1))}, index=idx)
            w = rng.permutation(warn) if scramble else warn
            ext = pd.DataFrame({"warn@1": w, "noise@1": rng.normal(size=T)}, index=idx)
            F = E.Features(px, ext)
            out = E.evolve(F, pop=1000, cull=0.1, seed=s)
            rows = out["rows"].dropna(subset=["comm_ret"])
            outs.append(float(rows["comm_ret"].mean()))
        res.append(np.mean(outs))
    wire_ok = res[0] > res[1] + 0.01
    print(f"    selected bots, mean per 5 months: real warning {res[0]*100:+.2f}%  scrambled warning {res[1]*100:+.2f}%  -> "
          f"{'PASS: gates find and use a real news signal' if wire_ok else 'WEAK: gate did not exploit a planted news signal'}")
    sys.exit(0 if (ok and null_ok and plant_ok and wire_ok) else 1)


if __name__ == "__main__":
    main()
