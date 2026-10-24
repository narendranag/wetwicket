"""Provisional recent matches from CricketData.org, until Cricsheet publishes them.

    CRICKETDATA_API_KEY=… python pipeline/fetch_recent.py            # writes data/d1/provisional.sql
    python pipeline/fetch_recent.py --from-file matches.json          # the same, from a saved API response

Cricsheet publishes in batches, sometimes a week or more apart. This fills the gap from the
CricketData.org match list: result, toss, venue and each innings' runs, wickets and overs. No
scorecards or ball-by-ball: on the free plan they cost 10 calls each (decision 2026-10-24).

Provisional matches live only in D1, never in data/wetwicket.sqlite, so nothing derived from the
SQLite (rain.json, replay.json, the open datasets) ever includes them. Their ids are `cd-<uuid>`;
Cricsheet's are numeric. provisional.sql deletes every `cd-` row and inserts the current set, leaving
out any match Cricsheet already has (same teams, start date within a day), so a Cricsheet match
replaces its provisional twin on the next run.

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

API = "https://api.cricapi.com/v1/matches"
UA = "wetwicket-ingest/1.0 (+https://github.com/narendranag/wetwicket)"
DAYS = 14      # how far back to look; Cricsheet normally catches up well within this
MAX_PAGES = 8  # 25 matches a call; the free plan allows 100 calls a day
FMT = {  # CricketData matchType -> (format, Cricsheet match_type), for international and other matches
    "test": (("Test", "Test"), ("First-class", "MDM")),
    "odi": (("ODI", "ODI"), ("One-day (other)", "ODM")),
    "t20": (("T20I", "IT20"), ("T20 league", "T20")),
}
ENDED = re.compile(r"\b(won|drawn|draw|tied|tie|no result|abandoned)\b", re.I)


def fetch_pages(key, since):
    """Pages of the match list until a whole page is older than `since`, or the budget runs out."""
    out = []
    for page in range(MAX_PAGES):
        url = f"{API}?{urllib.parse.urlencode({'apikey': key, 'offset': page * 25})}"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            body = json.load(r)
        if body.get("status") != "success":
            sys.exit(f"CricketData: {body.get('status')}: {body.get('reason') or body.get('info')}")
        rows = body.get("data") or []
        out += rows
        info = body.get("info") or {}
        print(f"page {page}: {len(rows)} matches (hits {info.get('hitsToday')}/{info.get('hitsLimit')})")
        if not rows or all((m.get("date") or "") < since for m in rows):
            break
        if info.get("hitsLimit") and info.get("hitsToday", 0) >= info["hitsLimit"] - 1:
            break
    return out


def norm(team):
    """Team name as Cricsheet writes it, and the gender: CricketData adds ' Women' to women's sides."""
    team = team.strip()
    if team.endswith(" Women"):
        return team[: -len(" Women")], "female"
    return team, "male"


def balls(overs, bpo=6):
    """Overs as CricketData gives them (46.3) to balls."""
    whole, part = divmod(round(float(overs or 0) * 10), 10)
    return whole * bpo + part


def to_rows(m, intl):
    """One API match -> (matches row, [innings rows]), or None when it can't be placed."""
    teams = [norm(t) for t in m.get("teams") or []]
    if len(teams) != 2 or m.get("matchType") not in FMT:
        return None
    (t_a, g_a), (t_b, g_b) = teams
    gender = "female" if "female" in (g_a, g_b) else "male"
    score = m.get("score") or []
    # Team 1 batted first: the first innings listed, named "<Team> Inning 1".
    first = norm(re.sub(r"\s+Inning\s+\d+$", "", score[0]["inning"]))[0] if score else t_a
    team1, team2 = (t_a, t_b) if first == t_a else (t_b, t_a)
    international = team1 in intl and team2 in intl
    fmt, match_type = FMT[m["matchType"]][0 if international else 1]
    status = (m.get("status") or "").strip()
    win = re.match(r"^(.+?) won\b", status)
    winner = norm(win.group(1))[0] if win else None
    result = ("draw" if re.search(r"\bdrawn?\b", status, re.I) else "tie" if re.search(r"\btied?\b", status, re.I)
              else "no result" if re.search(r"no result|abandoned", status, re.I) else None)
    detail = m.get("name", "").split(",", 1)[1].strip() if "," in m.get("name", "") else None
    mid = f"cd-{m['id']}"
    inns, summary = [], []
    for n, s in enumerate(score, 1):
        team = norm(re.sub(r"\s+Inning\s+\d+$", "", s.get("inning", "")))[0]
        b = balls(s.get("o"))
        inns.append({"match_id": mid, "inn": n, "team": team, "runs": s.get("r"), "wkts": s.get("w"), "balls": b})
        summary.append({"team": team, "runs": s.get("r"), "wkts": s.get("w"), "balls": b, "declared": 0, "super_over": 0})
    venue = m.get("venue") or ""
    return ({
        "id": mid, "date": m["date"][:10], "end_date": m["date"][:10], "season": m["date"][:4],
        "match_type": match_type, "fmt": fmt, "gender": gender,
        "team_type": "international" if international else "club",
        "event_detail": detail, "team1": team1, "team2": team2,
        "toss_winner": norm(m["tossWinner"])[0] if m.get("tossWinner") else None,
        "toss_decision": (m.get("tossChoice") or "").lower() or None,
        "winner": winner, "result": result, "outcome_text": status,
        "venue": venue, "city": venue.rsplit(",", 1)[1].strip() if "," in venue else None,
        "rain": "", "summary": json.dumps(summary, separators=(",", ":")),
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }, inns)


def insert(table, row):
    return f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join(quote(v) for v in row.values())});\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file", help="a saved /v1/matches response (or a JSON list of them) instead of the API")
    ap.add_argument("--days", type=int, default=DAYS)
    args = ap.parse_args()
    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()

    if args.from_file:
        raw = json.load(open(args.from_file))
        pages = raw if isinstance(raw, list) else [raw]
        matches = [m for p in pages for m in (p.get("data") or [])]
    else:
        key = os.environ.get("CRICKETDATA_API_KEY")
        if not key:
            sys.exit("CRICKETDATA_API_KEY is not set")
        matches = fetch_pages(key, since)

    con = sqlite3.connect(DB)
    intl = {r[0] for r in con.execute(
        "SELECT team1 FROM matches WHERE team_type = 'international' UNION SELECT team2 FROM matches WHERE team_type = 'international'")}

    def in_cricsheet(row):
        return con.execute(
            """SELECT 1 FROM matches WHERE gender = ? AND date BETWEEN date(?, '-1 day') AND date(?, '+1 day')
               AND ((team1 = ? AND team2 = ?) OR (team1 = ? AND team2 = ?)) LIMIT 1""",
            (row["gender"], row["date"], row["date"], row["team1"], row["team2"], row["team2"], row["team1"])).fetchone()

    kept, seen, skipped = [], set(), {"unfinished": 0, "old": 0, "unplaced": 0, "in Cricsheet": 0}
    for m in matches:
        if m.get("id") in seen:
            continue
        seen.add(m.get("id"))
        if not (m.get("matchEnded") or ENDED.search(m.get("status") or "")):
            skipped["unfinished"] += 1
        elif (m.get("date") or "") < since:
            skipped["old"] += 1
        elif not (rows := to_rows(m, intl)):
            skipped["unplaced"] += 1
        elif in_cricsheet(rows[0]):
            skipped["in Cricsheet"] += 1
        else:
            kept.append(rows)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "provisional.sql")
    with open(path, "w") as f:
        f.write("DELETE FROM innings WHERE match_id LIKE 'cd-%';\nDELETE FROM matches WHERE id LIKE 'cd-%';\n")
        for match, inns in kept:
            f.write(insert("matches", match))
            f.writelines(insert("innings", i) for i in inns)
    print(f"{len(kept)} provisional matches; skipped {', '.join(f'{v} {k}' for k, v in skipped.items() if v) or 'none'}")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
