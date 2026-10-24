"""Provisional recent matches from CricketData.org, until Cricsheet publishes them.

    CRICKETDATA_API_KEY=… python pipeline/fetch_recent.py      # writes data/d1/provisional.sql
    python pipeline/fetch_recent.py --from-file cricscore.json   # the same, from a saved API response

Cricsheet publishes in batches, sometimes a week or more apart. This fills the gap from
CricketData.org's cricScore feed: one call returns every match of the last 7 days with the teams,
each side's score as text ("181/6 (19.5)"), the status and the series. No venue, toss or scorecard:
on the free plan a scorecard costs 10 calls (decision 2026-10-24).

The feed only reaches back 7 days, so finished matches are kept in a `provisional` table in
data/wetwicket.sqlite, which the nightly caches. That table is not one of the match tables, so
nothing derived from them (rain.json, replay.json, the open datasets) ever includes a provisional
match, and export_d1.py never sends it. A match leaves the table when Cricsheet has it (same teams,
start date within a day) or after KEEP_DAYS.

provisional.sql deletes every `cd-<id>` row in D1 and inserts the table's current set, so a match
Cricsheet has delivered disappears from the site the same night. Cricsheet's ids are numeric.

Apply with: wrangler d1 execute wetwicket --remote --file data/d1/provisional.sql
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_d1 import DB, OUT, quote  # noqa: E402

API = "https://api.cricapi.com/v1/cricScore"
UA = "wetwicket-ingest/1.0 (+https://github.com/narendranag/wetwicket)"
KEEP_DAYS = 60  # a match Cricsheet still hasn't published after this is dropped
FMT = {  # CricketData matchType -> (format, Cricsheet match_type), for international and other matches
    "test": (("Test", "Test"), ("First-class", "MDM")),
    "odi": (("ODI", "ODI"), ("One-day (other)", "ODM")),
    "t20": (("T20I", "IT20"), ("T20 league", "T20")),
}
# Only a final status counts: a Test at "Day 1: Stumps" is listed with ms='result' too.
ENDED = re.compile(r"\b(won by|match drawn|drawn|match tied|tied|no result|abandoned)\b", re.I)
INNINGS = re.compile(r"(\d+)(?:/(\d+))?(d)?(?:\s*\((\d+(?:\.\d)?)\))?")


def fetch(key):
    url = f"{API}?{urllib.parse.urlencode({'apikey': key})}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        body = json.load(r)
    if body.get("status") != "success":
        sys.exit(f"CricketData: {body.get('status')}: {body.get('reason') or body.get('info')}")
    info = body.get("info") or {}
    print(f"cricScore: {len(body.get('data') or [])} matches (hits {info.get('hitsToday')}/{info.get('hitsLimit')})")
    return body.get("data") or []


def norm(team):
    """'India Women [INDW]' -> ('India', 'female'): Cricsheet's name for the side, and the gender."""
    team = re.sub(r"\s*\[[^\]]*\]\s*$", "", team or "").strip()
    if team.endswith(" Women"):
        return team[: -len(" Women")], "female"
    return team, "male"


def balls(overs, bpo=6):
    whole, part = divmod(round(float(overs) * 10), 10)
    return whole * bpo + part


def innings(text):
    """'250/10 & 180/4 (60)' -> [(250, 10, None, 0), (180, 4, 360, 0)]: runs, wickets, balls, declared."""
    out = []
    for part in (text or "").split("&"):
        if (m := INNINGS.search(part)):
            r, w, d, o = m.groups()
            out.append((int(r), int(w) if w is not None else 10, balls(o) if o else None, 1 if d else 0))
    return out


def match_type(m, inns):
    """The feed leaves matchType empty for some matches; a final over past 20 means 50 overs."""
    if m.get("matchType") in FMT:
        return m["matchType"]
    if re.search(r"\bDay \d|drawn|\bTest\b|first.class", f"{m.get('status')} {m.get('series')}", re.I) or len(inns) > 2:
        return "test"
    most = max((i[2] or 0 for i in inns), default=0)
    return "odi" if most > 20 * 6 else "t20" if most else None


def to_rows(m, intl):
    """One cricScore match -> (matches row, [innings rows]), or None when it can't be placed."""
    (t_a, g_a), (t_b, g_b) = norm(m.get("t1")), norm(m.get("t2"))
    if not t_a or not t_b:
        return None
    gender = "female" if "female" in (g_a, g_b) else "male"
    sides = {t_a: innings(m.get("t1s")), t_b: innings(m.get("t2s"))}
    status = (m.get("status") or "").strip()
    if gender == "male" and "Afghanistan" in (t_a, t_b):
        return None  # Cricsheet withholds Afghanistan men's matches, and so does the Archive (/data)
    win = re.match(r"^(.+?) won by\b(.*)$", status)
    winner, how = (norm(win.group(1))[0], win.group(2)) if win else (None, "")
    # Who batted first: "won by N runs" means the winner did; "won by N wkts" means the winner chased.
    # Otherwise the side with no score batted second, and failing that the feed's order stands.
    if winner in sides and re.search(r"\brun", how) and "innings" not in how:
        team1 = winner
    elif winner in sides and re.search(r"\bwkt|\bwicket", how):
        team1 = t_b if winner == t_a else t_a
    elif not sides[t_a] and sides[t_b]:
        team1 = t_b
    else:
        team1 = t_a
    team2 = t_b if team1 == t_a else t_a
    order = [(team1, i) for i in sides[team1]] + [(team2, i) for i in sides[team2]]
    if len(sides[team1]) == 2 and len(sides[team2]) >= 1:  # a two-innings match alternates
        order = [(team1, sides[team1][0]), (team2, sides[team2][0]), (team1, sides[team1][1])] + \
                [(team2, i) for i in sides[team2][1:]]
    kind = "test" if "innings" in how else match_type(m, [i for _, i in order])
    if kind is None:
        return None
    if kind == "test":
        order = []  # the feed shows one innings a side for multi-day matches: give the result only
    international = team1 in intl and team2 in intl
    fmt, mtype = FMT[kind][0 if international else 1]
    result = ("draw" if re.search(r"\bdrawn\b", status, re.I) else "tie" if re.search(r"\btied\b", status, re.I)
              else "no result" if re.search(r"no result|abandoned", status, re.I) else None)
    mid, date = f"cd-{m['id']}", m["dateTimeGMT"][:10]
    inns = [{"match_id": mid, "inn": n, "team": t, "runs": r, "wkts": w, "balls": b, "declared": d}
            for n, (t, (r, w, b, d)) in enumerate(order, 1)]
    summary = [{"team": i["team"], "runs": i["runs"], "wkts": i["wkts"], "balls": i["balls"] or 0,
                "declared": i["declared"], "super_over": 0} for i in inns]
    return ({
        "id": mid, "date": date, "end_date": date, "season": date[:4], "match_type": mtype, "fmt": fmt,
        "gender": gender, "team_type": "international" if international else "club",
        "event_name": (m.get("series") or "").strip() or None, "team1": team1, "team2": team2,
        "winner": winner, "result": result, "method": "D/L" if re.search(r"\bDLS?\b|D/L", status) else None,
        "outcome_text": re.sub(r"\s*-\s*\d+(st|nd|rd|th) Inning$", "", status), "rain": "",
        "summary": json.dumps(summary, separators=(",", ":")),
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }, inns)


def insert(table, row):
    return f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join(quote(v) for v in row.values())});\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file", help="a saved cricScore response instead of calling the API")
    args = ap.parse_args()
    if args.from_file:
        feed = json.load(open(args.from_file)).get("data") or []
    else:
        if not (key := os.environ.get("CRICKETDATA_API_KEY")):
            sys.exit("CRICKETDATA_API_KEY is not set")
        feed = fetch(key)

    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS provisional (id TEXT PRIMARY KEY, date TEXT, match TEXT, innings TEXT)")
    intl = {r[0] for r in con.execute(
        "SELECT team1 FROM matches WHERE team_type = 'international' UNION SELECT team2 FROM matches WHERE team_type = 'international'")}

    counts = {"new or updated": 0, "unfinished": 0, "unplaced": 0}
    for m in feed:
        if m.get("ms") != "result" or not ENDED.search(m.get("status") or ""):
            counts["unfinished"] += 1
        elif not (rows := to_rows(m, intl)):
            counts["unplaced"] += 1
        else:
            con.execute("INSERT OR REPLACE INTO provisional VALUES (?, ?, ?, ?)",
                        (rows[0]["id"], rows[0]["date"], json.dumps(rows[0]), json.dumps(rows[1])))
            counts["new or updated"] += 1

    # Drop what Cricsheet now has, and anything it still hasn't published after KEEP_DAYS.
    cutoff = (dt.date.today() - dt.timedelta(days=KEEP_DAYS)).isoformat()
    kept = []
    for pid, date, match, inns in con.execute("SELECT id, date, match, innings FROM provisional ORDER BY date").fetchall():
        row = json.loads(match)
        delivered = con.execute(
            """SELECT 1 FROM matches WHERE gender = ? AND date BETWEEN date(?, '-1 day') AND date(?, '+1 day')
               AND ((team1 = ? AND team2 = ?) OR (team1 = ? AND team2 = ?)) LIMIT 1""",
            (row["gender"], date, date, row["team1"], row["team2"], row["team2"], row["team1"])).fetchone()
        if delivered or date < cutoff:
            con.execute("DELETE FROM provisional WHERE id = ?", (pid,))
            counts["replaced by Cricsheet" if delivered else "expired"] = counts.get(
                "replaced by Cricsheet" if delivered else "expired", 0) + 1
        else:
            kept.append((row, json.loads(inns)))
    con.commit()

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "provisional.sql")
    with open(path, "w") as f:
        f.write("DELETE FROM innings WHERE match_id LIKE 'cd-%';\nDELETE FROM matches WHERE id LIKE 'cd-%';\n")
        for match, inns in kept:
            f.write(insert("matches", match))
            f.writelines(insert("innings", i) for i in inns)
    print(f"{len(kept)} provisional matches; " + ", ".join(f"{v} {k}" for k, v in counts.items() if v))
    print(f"-> {path}")


if __name__ == "__main__":
    main()
