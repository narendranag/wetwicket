"""Summarise sim_chases.pkl: does each rain rule favour the chasing side?

For each rule and stoppage point:
  agree        rule's verdict matches the real result
  to_chaser    rule hands the chasing side a win it went on to lose   (% of chases)
  to_defender  rule hands the defending side a win the chaser went on to take
  net          to_chaser - to_defender, in percentage points. > 0 favours chasing sides.
  p_at_par     chance a chaser exactly on par actually won (logistic fit). 50% is fair.
  fair_shift   runs to add to par to make it a true 50/50. > 0 means par is too low (favours chaser).

Writes data/analysis.json for the report page.
"""
import json
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = ["ARR", "MPO", "DL-SE", "DL-Pro", "DL-Pro-avg", "DL-refit"]
STAGES = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def logistic(margin, y):
    """Fit P(chase won) = sigmoid(a + b * margin). Returns (p_at_par, fair_shift)."""
    x, y = np.asarray(margin, float), np.asarray(y, float)

    def nll(t):
        z = t[0] + t[1] * x
        return np.sum(np.logaddexp(0, z) - y * z)

    a, b = minimize(nll, [0.0, 0.1], method="BFGS").x
    return 1 / (1 + np.exp(-a)), -a / b


def summarise(df, rule):
    par = np.floor(df[f"par_{rule}"])
    says_chase = df.runs > par
    says_def = df.runs < par
    won = df.chase_won
    p, shift = logistic(df.runs - df[f"par_{rule}"], won)
    return {
        "n": int(len(df)),
        "agree": float(((says_chase & won) | (says_def & ~won)).mean()),
        "to_chaser": float((says_chase & ~won).mean()),
        "to_defender": float((says_def & won).mean()),
        "tie": float((df.runs == par).mean()),
        "p_at_par": float(p),
        "fair_shift": float(shift),
    }


def benchmark_agree(df, folds=5):
    """Cross-validated agreement of a win-probability model (score, wickets, target): a ceiling for any rule."""
    X = np.column_stack([np.ones(len(df)), df.runs - df["par_DL-SE"], df.wkts, df.wkts ** 2, df.S / 100])
    X[:, 1:] = (X[:, 1:] - X[:, 1:].mean(0)) / X[:, 1:].std(0)
    y = df.chase_won.to_numpy(float)
    fold = np.random.default_rng(0).integers(0, folds, len(df))
    hits = np.zeros(len(df), bool)
    for f in range(folds):
        tr, te = fold != f, fold == f

        def nll(t):
            z = X[tr] @ t
            return np.sum(np.logaddexp(0, z) - y[tr] * z)

        t = minimize(nll, np.zeros(X.shape[1]), method="BFGS").x
        hits[te] = ((X[te] @ t) > 0) == (y[te] == 1)
    return float(hits.mean())


def main():
    df = pd.read_pickle(os.path.join(ROOT, "data", "sim_chases.pkl"))
    df["stage"] = (df.k / df.N).round(2)
    df["family"] = np.where(df.N == 50, "50-over", "T20")
    df["year"] = df.date.str[:4].astype(int)
    df = df[df.stage.isin(STAGES)]
    res = {"by_stage": [], "by_era": [], "by_score": [], "by_wickets": [], "by_fmt": [], "examples": []}

    for fam, g in df.groupby("family"):
        for stage, h in g.groupby("stage"):
            for rule in RULES:
                res["by_stage"].append({"family": fam, "stage": stage, "k": int(h.k.iloc[0]), "rule": rule, **summarise(h, rule)})
            res["by_stage"].append({"family": fam, "stage": stage, "k": int(h.k.iloc[0]), "rule": "Best possible",
                                    "n": int(len(h)), "agree": benchmark_agree(h)})
        for fmt, h in g.groupby("fmt"):
            for rule in RULES:
                res["by_fmt"].append({"family": fam, "fmt": fmt, "rule": rule, **summarise(h, rule)})
        eras = pd.cut(g.year, [2000, 2009, 2014, 2019, 2026], labels=["2001–09", "2010–14", "2015–19", "2020–26"])
        for era, h in g.groupby(eras, observed=True):
            for rule in RULES:
                res["by_era"].append({"family": fam, "era": str(era), "rule": rule, **summarise(h, rule)})
        bins = [0, 199, 249, 299, 999] if fam == "50-over" else [0, 139, 169, 199, 999]
        labels = ["<200", "200–249", "250–299", "300+"] if fam == "50-over" else ["<140", "140–169", "170–199", "200+"]
        for band, h in g.groupby(pd.cut(g.S, bins, labels=labels), observed=True):
            for rule in RULES:
                res["by_score"].append({"family": fam, "band": str(band), "rule": rule, **summarise(h, rule)})
        for band, h in g.groupby(pd.cut(g.wkts, [-1, 1, 3, 5, 9], labels=["0–1", "2–3", "4–5", "6+"]), observed=True):
            for rule in RULES:
                res["by_wickets"].append({"family": fam, "band": str(band), "rule": rule, **summarise(h, rule)})

    tables = pd.read_pickle(os.path.join(ROOT, "data", "refit_tables.pkl"))
    res["refit_tables"] = {str(N): t.round(1).reset_index().to_dict("list") for N, t in tables.items()}
    json.dump(res, open(os.path.join(ROOT, "data", "analysis.json"), "w"), indent=1)

    pd.set_option("display.width", 200)
    s = pd.DataFrame(res["by_stage"])
    s["net"] = s.to_chaser - s.to_defender
    print("\n== agree")
    print(s.pivot_table(index=["family", "k"], columns="rule", values="agree").map("{:.1%}".format).to_string())
    s = s[s.rule != "Best possible"]
    for col, fmt in ( ("net", "{:+.1%}"), ("p_at_par", "{:.1%}"), ("fair_shift", "{:+.1f}")):
        print(f"\n== {col}")
        print(s.pivot_table(index=["family", "k"], columns="rule", values=col).map(fmt.format).to_string())
    for key, idx in (("by_era", "era"), ("by_score", "band"), ("by_wickets", "band"), ("by_fmt", "fmt")):
        t = pd.DataFrame(res[key])
        print(f"\n== fair_shift (runs) {key}")
        print(t.pivot_table(index=["family", idx], columns="rule", values="fair_shift", sort=False).round(1).to_string())


if __name__ == "__main__":
    main()
