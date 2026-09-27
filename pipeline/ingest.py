"""Load Cricsheet match JSON and the Cricsheet Register into data/wetwicket.sqlite.

    python pipeline/ingest.py --matches data/raw/all_json          # full load (directory or .zip)
    python pipeline/ingest.py --matches recently_added_2_json.zip   # daily top-up
    python pipeline/ingest.py --register data/raw/register          # people.csv, names.csv

Each match is replaced whole (delete then insert), so re-ingesting a file Cricsheet has corrected
is safe. Changed match ids are appended to data/changed_matches.txt for the D1 sync.
"""
import argparse
import csv
import datetime as dt
import glob
import io
import json
import os
import re
import sqlite3
import zipfile

from countries import country_for
from flag_rain import classify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "wetwicket.sqlite")
SCHEMA = os.path.join(ROOT, "db", "schema.sql")
CHANGED = os.path.join(ROOT, "data", "changed_matches.txt")
BOWLER_WICKETS = {"bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"}
MATCH_TABLES = ("matches", "innings", "batting", "bowling", "match_players")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")).strip("-")


def fmt_group(match_type, team_type, balls_per_over=6):
    if balls_per_over == 5:
        return "The Hundred"
    if match_type in ("Test", "ODI"):
        return match_type
    if match_type == "IT20" or (match_type == "T20" and team_type == "international"):
        return "T20I"
    if match_type == "T20":
        return "T20 league"
    return "One-day (other)" if match_type == "ODM" else "First-class"


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def event_detail(ev, match_type):
    parts = []
    if ev.get("stage"):
        parts.append(ev["stage"])
    if ev.get("group"):
        parts.append(f"Group {ev['group']}")
    if ev.get("match_number"):
        n = ev["match_number"]
        parts.append(f"{ordinal(n)} {match_type}" if match_type in ("Test", "ODI") and not parts else f"match {n}")
    return ", ".join(parts)


def margin_text(o):
    by = o.get("by", {})
    if "innings" in by:
        return f"an innings and {by.get('runs', 0)} runs"
    return " ".join(f"{v} {k if v != 1 else k.rstrip('s')}" for k, v in by.items() if k in ("runs", "wickets"))


def outcome_text(o):
    if "winner" in o:
        m = margin_text(o)
        extra = f" ({o['method']})" if o.get("method") in ("D/L", "VJD") else ""
        if o.get("eliminator"):
            return f"Tie; {o['eliminator']} won the super over"
        if o.get("bowl_out"):
            return f"Tie; {o['bowl_out']} won the bowl-out"
        return f"{o['winner']} won" + (f" by {m}" if m else "") + extra
    if o.get("result") == "tie" and o.get("eliminator"):
        return f"Tie; {o['eliminator']} won the super over"
    return {"draw": "Match drawn", "tie": "Match tied", "no result": "No result"}.get(o.get("result"), o.get("result", ""))


def dismissal(w, bowler):
    k, f = w["kind"], [x.get("name", "sub") for x in w.get("fielders", [])]
    b = bowler
    return {
        "caught": f"c {f[0] if f else '?'} b {b}", "caught and bowled": f"c & b {b}", "bowled": f"b {b}",
        "lbw": f"lbw b {b}", "stumped": f"st {f[0] if f else '?'} b {b}", "hit wicket": f"hit wicket b {b}",
        "run out": f"run out ({'/'.join(f)})" if f else "run out",
    }.get(k, k)


def parse_innings(inn, n, bpo, reg, team_players):
    team = inn["team"]
    runs = wkts = balls = extras = 0
    overs_rows, fow, parts = [], [], []
    bat, bowl, bat_order, bowl_order = {}, {}, [], []
    part = {"runs": 0, "balls": 0, "bat": {}}

    def batter(name):
        if name not in bat:
            bat[name] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "out": 0, "how": "not out", "kind": ""}
            bat_order.append(name)
        return bat[name]

    def bowler(name):
        if name not in bowl:
            bowl[name] = {"balls": 0, "maidens": 0, "runs": 0, "wkts": 0, "wides": 0, "noballs": 0, "dots": 0}
            bowl_order.append(name)
        return bowl[name]

    for ov in inn.get("overs", []):
        o_runs = o_wkts = 0
        over_conceded = {}
        legal_in_over = 0
        for d in ov["deliveries"]:
            ex = d.get("extras", {})
            r = d["runs"]
            b, ns, bw = batter(d["batter"]), batter(d["non_striker"]), bowler(d["bowler"])
            legal = "wides" not in ex and "noballs" not in ex
            conceded = r["batter"] + ex.get("wides", 0) + ex.get("noballs", 0)
            o_runs += r["total"]
            runs += r["total"]
            extras += r["extras"]
            if "wides" not in ex:
                b["balls"] += 1
            b["runs"] += r["batter"]
            if r["batter"] == 4 and not r.get("non_boundary"):
                b["fours"] += 1
            if r["batter"] == 6 and not r.get("non_boundary"):
                b["sixes"] += 1
            bw["runs"] += conceded
            bw["wides"] += ex.get("wides", 0)
            bw["noballs"] += ex.get("noballs", 0)
            over_conceded[d["bowler"]] = over_conceded.get(d["bowler"], 0) + conceded
            if legal:
                balls += 1
                legal_in_over += 1
                bw["balls"] += 1
                if r["total"] == 0:
                    bw["dots"] += 1
            part["runs"] += r["total"]
            part["balls"] += 1 if legal else 0
            for nm, add in ((d["batter"], r["batter"]), (d["non_striker"], 0)):
                part["bat"][nm] = part["bat"].get(nm, 0) + add
            for w in d.get("wickets", []):
                out = batter(w["player_out"])
                if w["kind"] in ("retired hurt", "retired not out"):
                    out["how"] = "retired hurt"
                    continue
                wkts += 1
                o_wkts += 1
                out.update(out=1, how=dismissal(w, d["bowler"]), kind=w["kind"])
                if w["kind"] in BOWLER_WICKETS:
                    bw["wkts"] += 1
                over_ball = f"{ov['over']}.{legal_in_over}"
                fow.append([wkts, runs, over_ball, reg.get(w["player_out"]), w["player_out"]])
                pb = list(part["bat"].items())[:2]
                parts.append([wkts, part["runs"], part["balls"]] + [x for nm, rr in pb for x in (reg.get(nm), rr)])
                part = {"runs": 0, "balls": 0, "bat": {nm: 0 for nm in (d["batter"], d["non_striker"]) if nm != w["player_out"]}}
        # A maiden: one bowler, a full over of legal balls, nothing conceded.
        if len(over_conceded) == 1 and legal_in_over >= bpo and sum(over_conceded.values()) == 0:
            bowl[next(iter(over_conceded))]["maidens"] += 1
        overs_rows.append([ov["over"] + 1, o_runs, o_wkts, runs, wkts])
    if part["balls"] or part["runs"]:
        pb = list(part["bat"].items())[:2]
        parts.append([None, part["runs"], part["balls"]] + [x for nm, rr in pb for x in (reg.get(nm), rr)])

    tgt = inn.get("target", {})
    inn_row = {
        "inn": n, "team": team, "runs": runs, "wkts": wkts, "balls": balls, "extras": extras,
        "declared": int(bool(inn.get("declared"))), "forfeited": int(bool(inn.get("forfeited"))),
        "super_over": int(bool(inn.get("super_over"))),
        "target_runs": tgt.get("runs"), "target_overs": tgt.get("overs"),
        "overs_json": json.dumps(overs_rows, separators=(",", ":")),
        "fow_json": json.dumps(fow, separators=(",", ":")),
        "partnerships_json": json.dumps(parts, separators=(",", ":")),
    }
    bat_rows = [{"inn": n, "pos": i + 1, "player_id": reg.get(nm), "name": nm, "team": team, **bat[nm]}
                for i, nm in enumerate(bat_order)]
    bowl_team = next((t for t in team_players if t != team), None)
    bowl_rows = [{"inn": n, "pos": i + 1, "player_id": reg.get(nm), "name": nm, "team": bowl_team, **bowl[nm]}
                 for i, nm in enumerate(bowl_order)]
    return inn_row, bat_rows, bowl_rows


def venue_key(venue, city):
    base = venue.split(",")[0].strip()
    return slug(base + ("-" + city if city and city.lower() not in base.lower() else ""))


def parse_match(mid, d):
    info = d["info"]
    reg = info.get("registry", {}).get("people", {})
    bpo = info.get("balls_per_over", 6)
    innings = d.get("innings", [])
    parsed = [parse_innings(inn, i + 1, bpo, reg, info.get("players", {})) for i, inn in enumerate(innings)]
    team_order = [p[0]["team"] for p in parsed if not p[0]["super_over"]]
    teams = info["teams"]
    team1 = team_order[0] if team_order else teams[0]
    team2 = next((t for t in teams if t != team1), teams[-1])
    ev = info.get("event", {})
    # Missing cities are filled from other matches at the same ground by fix_venues() afterwards.
    city = info.get("city") or info["venue"].split(",")[-1].strip()
    country = country_for(city, info["venue"]) or ""
    venue_id = venue_key(info["venue"], city)
    fmt = fmt_group(info["match_type"], info["team_type"], bpo)
    rain = classify(d)
    o = info["outcome"]
    summary = [{"team": p[0]["team"], "runs": p[0]["runs"], "wkts": p[0]["wkts"], "balls": p[0]["balls"],
                "declared": p[0]["declared"], "super_over": p[0]["super_over"]} for p in parsed]
    match = {
        "id": mid, "date": info["dates"][0], "end_date": info["dates"][-1], "season": str(info.get("season", "")),
        "match_type": info["match_type"], "fmt": fmt, "gender": info["gender"], "team_type": info["team_type"],
        "competition_id": slug(ev["name"]) if ev.get("name") else None, "event_name": ev.get("name"),
        "event_detail": event_detail(ev, info["match_type"]),
        "team1": team1, "team2": team2,
        "toss_winner": info.get("toss", {}).get("winner"), "toss_decision": info.get("toss", {}).get("decision"),
        "winner": o.get("winner"), "result": o.get("result"), "method": o.get("method"),
        "margin": margin_text(o), "outcome_text": outcome_text(o),
        "venue_id": venue_id, "venue": info["venue"], "city": city, "city_known": int(bool(info.get("city"))),
        "country": country,
        "overs": info.get("overs"), "balls_per_over": bpo,
        "player_of_match": json.dumps([reg.get(p, p) for p in info.get("player_of_match", [])]),
        "rain": rain["rain_affected"], "rain_reason": rain["reason"], "rain_stage": rain["stage"],
        "summary": json.dumps(summary, separators=(",", ":")),
        "officials": json.dumps(info.get("officials", {}), separators=(",", ":")),
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    players = [{"team": t, "player_id": reg.get(nm, nm), "name": nm} for t, names in info.get("players", {}).items() for nm in names]
    comp = {"id": match["competition_id"], "name": ev.get("name"), "team_type": info["team_type"],
            "gender": info["gender"], "fmt": fmt} if ev.get("name") else None
    return match, parsed, players, comp


def insert(cur, table, row):
    cols = ",".join(row)
    cur.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({','.join('?' * len(row))})", list(row.values()))


def iter_match_files(src):
    if src.endswith(".zip"):
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.endswith(".json"):
                    yield os.path.basename(n)[:-5], json.loads(z.read(n))
    else:
        for p in sorted(glob.glob(os.path.join(src, "*.json"))):
            with open(p) as f:
                yield os.path.basename(p)[:-5], json.load(f)


def ingest_matches(con, src):
    cur = con.cursor()
    changed = []
    for mid, d in iter_match_files(src):
        match, parsed, players, comp = parse_match(mid, d)
        for t in MATCH_TABLES:
            cur.execute(f"DELETE FROM {t} WHERE {'id' if t == 'matches' else 'match_id'} = ?", (mid,))
        insert(cur, "matches", match)
        for inn_row, bat_rows, bowl_rows in parsed:
            insert(cur, "innings", {"match_id": mid, **inn_row})
            for r in bat_rows:
                insert(cur, "batting", {"match_id": mid, **r})
            for r in bowl_rows:
                insert(cur, "bowling", {"match_id": mid, **r})
        for r in players:
            insert(cur, "match_players", {"match_id": mid, **r})
        if comp:
            insert(cur, "competitions", comp)
        changed.append(mid)
        if len(changed) % 2000 == 0:
            con.commit()
            print(f"  {len(changed)} matches")
    con.commit()
    changed += fix_venues(con)
    with open(CHANGED, "a") as f:
        f.writelines(m + "\n" for m in changed)
    return changed


def fix_venues(con):
    """Fill cities Cricsheet omitted from other matches at the same ground, then rebuild venues."""
    cur = con.cursor()
    known = dict(cur.execute("SELECT venue, city FROM matches WHERE city_known = 1 GROUP BY venue").fetchall())
    fixed = []
    for mid, venue, city in cur.execute("SELECT id, venue, city FROM matches WHERE city_known = 0").fetchall():
        new_city = known.get(venue)
        if new_city and new_city != city:
            cur.execute("UPDATE matches SET city = ?, country = ?, venue_id = ? WHERE id = ?",
                        (new_city, country_for(new_city, venue) or "", venue_key(venue, new_city), mid))
            fixed.append(mid)
    cur.execute("DELETE FROM venues")
    cur.execute("""INSERT INTO venues (id, name, city, country)
                   SELECT venue_id, MIN(venue), city, country FROM matches GROUP BY venue_id""")
    rows = cur.execute("SELECT id, name FROM venues").fetchall()
    cur.executemany("UPDATE venues SET name = ? WHERE id = ?", [(n.split(",")[0].strip(), i) for i, n in rows])
    con.commit()
    return fixed


def ingest_register(con, folder):
    cur = con.cursor()
    cur.execute("DELETE FROM people")
    cur.execute("DELETE FROM people_names")
    main = {"key_cricinfo", "key_cricketarchive", "key_bcci", "key_cricbuzz"}
    with open(os.path.join(folder, "people.csv"), newline="") as f:
        for r in csv.DictReader(f):
            other = {k: v for k, v in r.items() if k.startswith("key_") and k not in main and v}
            insert(cur, "people", {"id": r["identifier"], "name": r["name"], "unique_name": r["unique_name"],
                                   **{k: r.get(k) or None for k in main}, "keys_json": json.dumps(other) if other else None})
    with open(os.path.join(folder, "names.csv"), newline="") as f:
        for r in csv.DictReader(f):
            cur.execute("INSERT OR IGNORE INTO people_names (id, name) VALUES (?, ?)", (r["identifier"], r["name"]))
    con.commit()
    return cur.execute("SELECT COUNT(*) FROM people").fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", help="directory of Cricsheet JSON files, or a Cricsheet zip")
    ap.add_argument("--register", help="directory holding people.csv and names.csv")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.executescript(open(SCHEMA).read())
    if args.register:
        print(f"register: {ingest_register(con, args.register)} people")
    if args.matches:
        changed = ingest_matches(con, args.matches)
        print(f"matches: {len(changed)} ingested")
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        con.execute("INSERT OR REPLACE INTO meta VALUES ('last_ingest', ?)", (now,))
        con.execute("INSERT OR REPLACE INTO meta VALUES ('latest_match', (SELECT MAX(date) FROM matches))")
        con.commit()


if __name__ == "__main__":
    main()
