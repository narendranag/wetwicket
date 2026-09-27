"""Export the data the site reads: public/data/rain.json (rain-hit matches) and public/data/replay.json (analysis)."""
import collections
import json
import math
import os

import pandas as pd

from rain_rules import se_resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "data")
RULES = ("ARR", "MPO", "DL-SE", "DL-Pro", "DL-Pro-avg", "DL-refit")
# Real ODIs, replayed as if rain ended play after 30 overs of the chase.
EXAMPLES = [("2018-06-24", "Australia"), ("2009-12-15", "India"), ("2019-02-27", "England"),
            ("2016-01-20", "Australia"), ("2006-03-12", "Australia")]


def fmt_group(r):
    t = r.match_type
    if t in ("Test", "ODI"):
        return t
    if t == "IT20" or (t == "T20" and r.team_type == "international"):
        return "T20I"
    if t == "T20":
        return "T20 league"
    return "One-day (other)" if t == "ODM" else "First-class"


def write(name, data):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"-> {path} ({os.path.getsize(path) // 1024} KB)")


def rain_data():
    df = pd.read_csv(os.path.join(ROOT, "data", "matches_rain_flags.csv"), dtype=str).fillna("")
    df["fmt"] = df.apply(fmt_group, axis=1)
    df["year"] = df.date.str[:4].astype(int)
    totals = collections.Counter(zip(df.fmt, df.country, df.year, df.gender))
    rain = df[df.rain_affected != ""]
    cols = ["date", "fmt", "gender", "event", "team1", "team2", "venue", "country",
            "outcome", "rain_affected", "stage", "reason", "method", "match_id"]
    return {
        "matches": rain[cols].values.tolist(),
        "totals": [[f, c, y, g, n] for (f, c, y, g), n in totals.items()],
        "updated": df.date.max(),
    }


def replay_data():
    a = json.load(open(os.path.join(ROOT, "data", "analysis.json")))
    sim = pd.read_pickle(os.path.join(ROOT, "data", "sim_chases.pkl"))
    M = pd.read_pickle(os.path.join(ROOT, "data", "lo_matches.pkl")).set_index("match_id")
    sim = sim.join(M[["team1", "team2", "winner", "runs2", "wkts2"]], on="match_id")

    examples = []
    for date, team1 in EXAMPLES:
        r = sim[(sim.date == date) & (sim.team1 == team1) & (sim.k == 30) & (sim.fmt == "ODI")].iloc[0]
        examples.append({
            "date": date, "team1": r.team1, "team2": r.team2, "S": int(r.S), "runs": int(r.runs), "wkts": int(r.wkts),
            "final": f"{int(r.runs2)}/{int(r.wkts2)}", "winner": r.winner, "match_id": r.match_id,
            "pars": {k: math.floor(r[f"par_{k}"]) for k in RULES},
        })

    se = {str(N): {f"w{w}": [round(100 * se_resource(u * 6, w) / se_resource(N * 6, 0), 1) for u in range(N, -1, -1)]
                   for w in range(10)} for N in (50, 20)}
    counts = sim.groupby("N").match_id.nunique()
    fit = M[(M.rain == "") & (M.date >= "2015-01-01") & M.sched_overs.isin([20, 50])
            & ((M.wkts1 >= 10) | (M.balls1 >= M.sched_overs * 6))
            & ((M.sched_overs == 20) == M.fmt.isin(["T20I", "T20 league"]))]
    return {
        "by_stage": a["by_stage"], "by_score": a["by_score"], "by_wickets": a["by_wickets"], "by_era": a["by_era"],
        "refit": a["refit_tables"], "se": se, "examples": examples,
        "matches": {"50-over": int(counts[50]), "T20": int(counts[20])},
        "states": int(len(sim)), "fit_matches": int(len(fit)),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    write("rain.json", rain_data())
    write("replay.json", replay_data())


if __name__ == "__main__":
    main()
