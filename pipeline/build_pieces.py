"""Export the data behind the D/L calculator, Beat the Par, and Classics pages. Rebuilt by hand.

    python pipeline/build_pieces.py              # the D/L table and the game's chases
    python pipeline/build_pieces.py 65272        # also src/data/classics/<id>.json for each match id
"""
import json
import os
import random
import sqlite3
import sys

from rain_rules import SE, par_arr, par_dl_se

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "data")
CLASSICS = os.path.join(ROOT, "src", "data", "classics")
DB = os.path.join(ROOT, "data", "wetwicket.sqlite")
# The game sticks to sides most players will know.
SIDES = ("Australia", "Bangladesh", "England", "India", "Ireland", "New Zealand", "Pakistan", "South Africa",
         "Sri Lanka", "West Indies", "Zimbabwe")
# (format, overs, earliest and latest over the rain may come, matches to sample)
GAME = [("ODI", 50, 15, 42, 260), ("T20I", 20, 6, 16, 140)]


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"-> {path} ({os.path.getsize(path) / 1024:.0f} KB)")


def game_data(con):
    """Rain-free chases, each stopped at a random over, with the Standard Edition par at that point."""
    rng = random.Random(2002)
    marks = ",".join("?" * len(SIDES))
    chases = []
    for fmt, N, lo, hi, n in GAME:
        rows = con.execute(f"""
            SELECT m.id, m.date, m.gender, m.team1, m.team2, m.winner, m.outcome_text, i1.runs AS S, i2.overs_json
            FROM matches m JOIN innings i1 ON i1.match_id = m.id AND i1.inn = 1
                           JOIN innings i2 ON i2.match_id = m.id AND i2.inn = 2
            WHERE m.fmt = ? AND m.overs = ? AND m.rain = '' AND m.winner IS NOT NULL AND m.method IS NULL
              AND (i1.wkts = 10 OR i1.balls = ?) AND m.team1 IN ({marks}) AND m.team2 IN ({marks})
            ORDER BY m.id""", (fmt, N, N * 6, *SIDES, *SIDES)).fetchall()
        picked = 0
        for r in rng.sample(rows, len(rows)):
            overs = json.loads(r["overs_json"])
            k = rng.randint(lo, hi)
            if len(overs) <= k or overs[k - 1][4] >= 9:  # the chase must still be alive when the rain comes
                continue
            runs, wkts = overs[k - 1][3], overs[k - 1][4]
            chases.append([r["id"], r["date"], fmt, r["gender"], r["team1"], r["team2"], r["S"], N, k, runs, wkts,
                           par_dl_se(S=r["S"], k=k, N=N, wkts2=wkts), round(par_arr(S=r["S"], k=k, N=N)),
                           r["outcome_text"]])
            picked += 1
            if picked == n:
                break
    return {"fields": ["id", "date", "fmt", "gender", "team1", "team2", "S", "N", "k", "runs", "wkts", "par", "arr",
                       "outcome"], "chases": chases}


def classic_data(con, match_id):
    """A limited-overs match with the Standard Edition par after each over of the chase."""
    m = dict(con.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone())
    inns = [dict(r) for r in con.execute("SELECT * FROM innings WHERE match_id = ? AND super_over = 0 ORDER BY inn",
                                         (match_id,))]
    S, N = inns[0]["runs"], m["overs"]
    for i in inns:
        for key in ("overs_json", "fow_json", "partnerships_json"):
            i[key[:-5]] = json.loads(i.pop(key) or "[]")
    chase = [[k, cum, w, par_dl_se(S=S, k=k, N=N, wkts2=w)] for k, _, _, cum, w in inns[1]["overs"]]
    last = chase[-1][0]
    return {
        "id": m["id"], "date": m["date"], "team1": m["team1"], "team2": m["team2"], "event": m["event_name"],
        "detail": m["event_detail"], "venue": m["venue"], "outcome": m["outcome_text"], "overs": N,
        "innings": [{k: i[k] for k in ("team", "runs", "wkts", "balls", "overs", "fow")} for i in inns],
        "chase": chase,  # [over, runs, wickets, par]
        "sheet": [par_dl_se(S=S, k=last, N=N, wkts2=w) for w in range(10)],  # par after the last over, by wickets
    }


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    write(os.path.join(OUT, "dl-se.json"), SE.tolist())  # [balls_left][wickets_lost], percent
    write(os.path.join(OUT, "par-game.json"), game_data(con))
    for match_id in sys.argv[1:]:
        write(os.path.join(CLASSICS, f"{match_id}.json"), classic_data(con, match_id))


if __name__ == "__main__":
    main()
