"""Over-by-over innings states for every limited-overs match in Cricsheet.

Writes data/overs.pkl (one row per innings per over) and data/lo_matches.pkl (one row per match).
Rain flags come from data/matches_rain_flags.csv (built by flag_rain.py).
"""
import glob
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "all_json")
FULL_MEMBERS = {"Australia", "England", "India", "Pakistan", "South Africa", "New Zealand", "Sri Lanka",
                "West Indies", "Bangladesh", "Zimbabwe", "Ireland", "Afghanistan"}


def fmt_group(match_type, team_type):
    if match_type == "ODI":
        return "ODI"
    if match_type == "ODM":
        return "One-day (other)"
    if match_type == "IT20" or (match_type == "T20" and team_type == "international"):
        return "T20I"
    return "T20 league"


def main():
    flags = pd.read_csv(os.path.join(ROOT, "data", "matches_rain_flags.csv"), dtype={"match_id": str})
    rain = dict(zip(flags.match_id, flags.rain_affected.fillna("")))
    matches, overs = [], []
    for path in glob.glob(os.path.join(SRC, "*.json")):
        mid = os.path.basename(path)[:-5]
        with open(path) as f:
            d = json.load(f)
        info = d["info"]
        if info["match_type"] not in ("ODI", "ODM", "T20", "IT20") or info["balls_per_over"] != 6:
            continue  # The Hundred uses 5-ball sets and doesn't map onto an overs table.
        sched = 20 if info["match_type"] in ("T20", "IT20") else info.get("overs", 50)
        innings = [i for i in d.get("innings", []) if not i.get("super_over")]
        if len(innings) != 2:
            continue
        o = info["outcome"]
        teams = [innings[0]["team"], innings[1]["team"]]
        m = {
            "match_id": mid, "date": info["dates"][0], "fmt": fmt_group(info["match_type"], info["team_type"]),
            "gender": info["gender"], "sched_overs": sched, "team1": teams[0], "team2": teams[1],
            "winner": o.get("winner", ""), "result": o.get("result", ""), "method": o.get("method", ""),
            "rain": rain.get(mid, ""),
            "target_runs": innings[1].get("target", {}).get("runs"),
            "target_overs": innings[1].get("target", {}).get("overs"),
            "full_members": set(teams) <= FULL_MEMBERS,
        }
        for n, inn in enumerate(innings, 1):
            runs = wkts = balls = 0
            for ov in inn.get("overs", []):
                over_runs = 0
                for dl in ov["deliveries"]:
                    ex = dl.get("extras", {})
                    over_runs += dl["runs"]["total"]
                    wkts += len(dl.get("wickets", []))
                    if "wides" not in ex and "noballs" not in ex:
                        balls += 1
                runs += over_runs
                overs.append((mid, n, ov["over"] + 1, over_runs, runs, wkts, balls))
            m[f"runs{n}"], m[f"wkts{n}"], m[f"balls{n}"] = runs, wkts, balls
        matches.append(m)
    mdf = pd.DataFrame(matches)
    odf = pd.DataFrame(overs, columns=["match_id", "inn", "over", "over_runs", "runs", "wkts", "balls"])
    mdf.to_pickle(os.path.join(ROOT, "data", "lo_matches.pkl"))
    odf.to_pickle(os.path.join(ROOT, "data", "overs.pkl"))
    print(len(mdf), "matches,", len(odf), "over rows")
    print(mdf.groupby(["fmt", "rain"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
