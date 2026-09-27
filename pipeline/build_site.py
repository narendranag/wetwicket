"""Export the data the site reads: public/data/rain.json (rain-hit matches) and public/data/replay.json (analysis)."""
import json
import math
import os

import sqlite3
import sys

import pandas as pd

from rain_rules import se_resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "data")
DB = os.path.join(ROOT, "data", "wetwicket.sqlite")
RULES = ("ARR", "MPO", "DL-SE", "DL-Pro", "DL-Pro-avg", "DL-refit")
# Real ODIs, replayed as if rain ended play after 30 overs of the chase.
EXAMPLES = [("2018-06-24", "Australia"), ("2009-12-15", "India"), ("2019-02-27", "England"),
            ("2016-01-20", "Australia"), ("2006-03-12", "Australia")]


def write(name, data):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"-> {path} ({os.path.getsize(path) // 1024} KB)")


def rain_data():
    """Rain-hit matches for the Rain Stopped Play explorer, from the match database."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    # The explorer groups formats more coarsely than the archive: The Hundred counts as a T20 league.
    fmt = "CASE fmt WHEN 'The Hundred' THEN 'T20 league' ELSE fmt END"
    totals = con.execute(f"""SELECT {fmt} AS f, country, CAST(substr(date, 1, 4) AS INT) AS y, gender, COUNT(*) AS n
                             FROM matches GROUP BY f, country, y, gender""").fetchall()
    rows = con.execute(f"""SELECT date, {fmt} AS f, gender, COALESCE(event_name, '') AS event, team1, team2, venue, country,
                                  outcome_text, rain, COALESCE(rain_stage, ''), rain_reason, COALESCE(method, ''), id
                           FROM matches WHERE rain != '' ORDER BY date DESC, id DESC""").fetchall()
    latest = con.execute("SELECT MAX(date) FROM matches").fetchone()[0]
    return {"matches": [list(r) for r in rows], "totals": [list(t) for t in totals], "updated": latest}


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
    if "--rain-only" not in sys.argv:  # the replay analysis is rebuilt by hand, not nightly
        write("replay.json", replay_data())


if __name__ == "__main__":
    main()
