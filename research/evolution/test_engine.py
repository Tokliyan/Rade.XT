"""
Validation of the evolution engine on fake markets. Run: python test_engine.py

1. Causality   - changing FUTURE prices must not change any bot's PAST equity.
2. Null market - pure random walks. The engine must find nothing real:
                 selected bots must not beat the population next period.
3. Planted edge - persistent-trend assets. The engine should find it.
"""
import sys
import numpy as np
import pandas as pd
import data
import engine as E


def causality():
    df = data.synthetic("planted", seed=3)
    F1 = E.Features(df)
    cut = 5000
    df2 = df.copy()
    rng = np.random.default_rng(9)
    df2.iloc[cut + 1:] = df2.iloc[cut + 1:] * np.exp(np.cumsum(rng.normal(0, 0.03, (len(df) - cut - 1, df.shape[1])), axis=0))
    F2 = E.Features(df2)
    g = E.rand_genome(np.arange(600) % E.NF, np.random.default_rng(5), F1.A)
    r1 = E.run(F1, g, 3000, cut + 300, rec=True)["hist"]
    r2 = E.run(F2, g, 3000, cut + 300, rec=True)["hist"]
    n = cut - 3000 + 1
    same = np.allclose(r1[:n], r2[:n], rtol=0, atol=1e-9)
    print(f"[1] causality: past equity unchanged when future is altered -> {'PASS' if same else 'FAIL'}")
    return same


def evo_stats(kind, seeds):
    sel, frozen_ann, fz_vs_pop = [], [], []
    for s in seeds:
        df = data.synthetic(kind, seed=s)
        F = E.Features(df)
        out = E.evolve(F, pop=1000, cull=0.1, seed=s)
        rows = out["rows"].dropna(subset=["comm_ret"])
        sel.append((rows["comm_ret"] - rows["pop_mean"]).to_numpy())
        fz = E.freeze_and_test(F, out["frozen"])
        frozen_ann.append(fz["stats"]["ann"])
    allsel = np.concatenate(sel)
    t = allsel.mean() / (allsel.std() / np.sqrt(len(allsel)))
    return allsel.mean(), t, np.array(frozen_ann)


def main():
    ok = causality()
    print("[2] null market (no edge anywhere), 4 seeds x 70 generations")
    m, t, fz = evo_stats("random", [11, 12, 13, 14])
    print(f"    selected-minus-population next-period return: {m*100:+.2f}% per 5 months (t={t:+.1f}); frozen holdout ann: "
          f"{np.round(fz*100,1)}%  mean {fz.mean()*100:+.1f}%")
    null_ok = t < 3.0 and fz.mean() < 0.02
    print("    ->", "PASS: no phantom edge" if null_ok else "FAIL: engine found money in noise")
    print("[3] planted trend edge, 4 seeds")
    m2, t2, fz2 = evo_stats("planted", [21, 22, 23, 24])
    print(f"    selected-minus-population next-period return: {m2*100:+.2f}% per 5 months (t={t2:+.1f}); frozen holdout ann: "
          f"{np.round(fz2*100,1)}%  mean {fz2.mean()*100:+.1f}%")
    plant_ok = t2 > 3.0 and fz2.mean() > 0.02
    print("    ->", "PASS: real edge detected" if plant_ok else "WEAK: edge not clearly detected")
    sys.exit(0 if (ok and null_ok and plant_ok) else 1)


if __name__ == "__main__":
    main()
