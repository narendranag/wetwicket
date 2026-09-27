"""Replay rain-free chases as if rain had ended play after k overs, under each rain rule.

For every completed, uninterrupted limited-overs match with a winner, and every over k at which
the chase was still live, record the chasing side's score and each rule's par score. Comparing
each rule's verdict with what actually happened shows whether it favours the chasing side.

Writes data/sim_chases.pkl and data/refit_tables.pkl.
"""
import os

import numpy as np
import pandas as pd

from rain_rules import ProEdition, RefitModel, first_innings_states, par_arr, par_dl_se

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMATS = {50: ["ODI", "One-day (other)"], 20: ["T20I", "T20 league"]}
MIN_OVERS = {50: 20, 20: 5}  # fewest overs Team 2 must face for a result


def main():
    M = pd.read_pickle(os.path.join(ROOT, "data", "lo_matches.pkl"))
    O = pd.read_pickle(os.path.join(ROOT, "data", "overs.pkl"))
    out, tables = [], {}
    for N, fmts in FORMATS.items():
        pool = M[M.fmt.isin(fmts) & (M.sched_overs == N)]
        model = RefitModel.fit(first_innings_states(O, pool), N)
        tables[N] = model
        ok = pool[(pool.rain == "") & pool.winner.isin([*pool.team1.unique(), *pool.team2.unique()])
                  & (pool.result == "") & (pool.method == "")
                  & ((pool.wkts1 >= 10) | (pool.balls1 >= N * 6))
                  & (pool.target_runs == pool.runs1 + 1) & (pool.target_overs == N)]
        ok = ok[ok.winner != ""]
        o1 = O[(O.inn == 1) & O.match_id.isin(ok.match_id)]
        best = o1.groupby("match_id").over_runs.apply(lambda s: np.sort(s.to_numpy())[::-1].cumsum())
        o2 = O[(O.inn == 2) & O.match_id.isin(ok.match_id)]
        last_over = o2.groupby("match_id").over.max()
        o2 = o2.merge(ok[["match_id", "fmt", "gender", "date", "runs1", "team2", "winner", "full_members"]], on="match_id")
        # G50 per the ICC playing conditions: 245 for full-member men's cricket, 200 below that.
        o2["G50"] = np.where((o2.gender == "male") & o2.full_members, 245, 200)
        lam = {s: ProEdition.lam(s[0], N, s[1]) for s in set(zip(o2.runs1, o2.G50))}
        # Variant: compare S with the real average first-innings total for that gender and year.
        avg = ok.groupby([ok.gender, ok.date.str[:4]]).runs1.mean()
        o2["avg1"] = [avg[(g, d[:4])] for g, d in zip(o2.gender, o2.date)]
        lam_avg = {s: ProEdition.lam(s[0], N, expected=s[1]) for s in set(zip(o2.runs1, o2.avg1))}
        # Chase still live after over k: the innings carried on into over k+1, and k full overs were bowled.
        o2 = o2[(o2.over >= MIN_OVERS[N]) & (o2.over < o2.match_id.map(last_over)) & (o2.balls == o2.over * 6)]
        for r in o2.itertuples(index=False):
            k = r.over
            mpo = best[r.match_id]
            out.append({
                "match_id": r.match_id, "fmt": r.fmt, "gender": r.gender, "date": r.date, "N": N, "k": k,
                "S": r.runs1, "runs": r.runs, "wkts": r.wkts, "chase_won": r.winner == r.team2,
                "par_ARR": par_arr(r.runs1, k, N),
                "par_MPO": float(mpo[min(k, len(mpo)) - 1]),
                "par_DL-SE": par_dl_se(r.runs1, k, N, r.wkts),
                "par_DL-Pro": r.runs1 * (1 - ProEdition.resource(N - k, r.wkts, N, lam[(r.runs1, r.G50)]) / 100),
                "par_DL-Pro-avg": r.runs1 * (1 - ProEdition.resource(N - k, r.wkts, N, lam_avg[(r.runs1, r.avg1)]) / 100),
                "par_DL-refit": model.par(r.runs1, k, N, r.wkts),
            })
        print(f"{N}-over: {len(ok)} matches, {sum(1 for x in out if x['N'] == N)} chase states")
    df = pd.DataFrame(out)
    df.to_pickle(os.path.join(ROOT, "data", "sim_chases.pkl"))
    pd.to_pickle({N: m.table() for N, m in tables.items()}, os.path.join(ROOT, "data", "refit_tables.pkl"))


if __name__ == "__main__":
    main()
