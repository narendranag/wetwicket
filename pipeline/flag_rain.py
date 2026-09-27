"""Flag rain/weather-affected cricket matches in the Cricsheet JSON archive.

Source: https://cricsheet.org/downloads/all_json.zip (unzipped to data/raw/all_json).
Host country comes from the hand-built city map in countries.py.

Cricsheet has no explicit "rain" field, so we infer from what weather leaves behind:

Limited-overs (T20, IT20, ODI, ODM, club T20 leagues):
  confirmed  - result decided by D/L(S) or VJD method
  confirmed  - chasing side's target set over fewer overs than scheduled (match shortened)
  likely     - "no result" (abandoned; nearly always weather, occasionally pitch/bad light)
Multi-day (Test, MDM):
  likely     - drawn with < 70% of the available overs bowled (lost days/sessions)
"""
import csv
import glob
import json
import os

from countries import country_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "all_json")
OUT_ALL = os.path.join(ROOT, "data", "matches_rain_flags.csv")
OUT_RAIN = os.path.join(ROOT, "data", "rain_affected_matches.csv")

MULTI_DAY = {"Test", "MDM"}
OVERS_PER_DAY = 90
MULTI_DAY_THRESHOLD = 0.70


def innings_stats(inn, bpo):
    """Legal balls bowled and wickets fallen in an innings."""
    balls = wickets = 0
    for over in inn.get("overs", []):
        for d in over["deliveries"]:
            extras = d.get("extras", {})
            if "wides" not in extras and "noballs" not in extras:
                balls += 1
            wickets += len(d.get("wickets", []))
    return balls, wickets


def fmt_overs(balls, bpo):
    return f"{balls // bpo}.{balls % bpo}" if balls % bpo else str(balls // bpo)


def classify(d):
    info = d["info"]
    outcome = info["outcome"]
    bpo = info["balls_per_over"]
    innings = [i for i in d.get("innings", []) if not i.get("super_over")]
    stats = [innings_stats(i, bpo) for i in innings]
    total_balls = sum(b for b, _ in stats)
    method = outcome.get("method")
    result = outcome.get("result")

    row = {
        "total_overs_bowled": fmt_overs(total_balls, bpo),
        "method": method or "",
        "scheduled_overs": info.get("overs", ""),
        "revised_target_overs": "",
        "revised_target_runs": "",
    }

    if info["match_type"] in MULTI_DAY:
        days = 5 if info["match_type"] == "Test" else max(len(info["dates"]), 3)
        available = days * OVERS_PER_DAY * 6
        pct = total_balls / available
        row["pct_overs_possible"] = f"{pct:.0%}"
        if result == "draw" and pct < MULTI_DAY_THRESHOLD:
            return row | {"rain_affected": "likely", "stage": "",
                          "reason": f"Draw with only {row['total_overs_bowled']} of ~{days * OVERS_PER_DAY} overs bowled ({pct:.0%})"}
        return row | {"rain_affected": "", "stage": "", "reason": ""}

    row["pct_overs_possible"] = ""
    scheduled = info.get("overs")
    if info["match_type"] in ("T20", "IT20") and scheduled:
        scheduled = min(scheduled, 20)  # a few T20s are mis-recorded as 50-over games
        row["scheduled_overs"] = scheduled
    target = innings[1].get("target", {}) if len(innings) > 1 else {}
    if target:
        row["revised_target_overs"] = target.get("overs", "")
        row["revised_target_runs"] = target.get("runs", "")

    reasons, stage = [], ""
    reduced = scheduled and target.get("overs") and target["overs"] < scheduled
    if reduced:
        # If the 1st innings faced no more than the chase allocation, both sides were cut
        # (rain before/during the 1st innings); otherwise only the chase was cut.
        stage = "before/during 1st innings" if stats[0][0] <= target["overs"] * bpo else "between/during 2nd innings"
        reasons.append(f"Chase reduced to {target['overs']} overs (target {target.get('runs')}) from {scheduled}")
    if method in ("D/L", "VJD"):
        if not stage:
            stage = "during 2nd innings"
        reasons.insert(0, f"Result by {'DLS' if method == 'D/L' else 'VJD'} method")
    if reasons:
        return row | {"rain_affected": "confirmed", "stage": stage, "reason": "; ".join(reasons)}
    if result == "no result":
        stage = "no play" if total_balls == 0 else ("abandoned in 1st innings" if len(innings) <= 1 else "abandoned in 2nd innings")
        return row | {"rain_affected": "likely", "stage": stage,
                      "reason": f"No result (abandoned after {row['total_overs_bowled']} overs)"}
    return row | {"rain_affected": "", "stage": "", "reason": ""}


def winner(outcome):
    if "winner" in outcome:
        by = outcome.get("by", {})
        margin = " ".join(f"{v} {k}" for k, v in by.items())
        return f"{outcome['winner']} won by {margin}".strip()
    return outcome.get("result", "")


def main():
    rows = []
    for path in glob.glob(os.path.join(SRC, "*.json")):
        with open(path) as f:
            d = json.load(f)
        info = d["info"]
        rows.append({
            "match_id": os.path.basename(path)[:-5],
            "date": info["dates"][0],
            "match_type": info["match_type"],
            "gender": info["gender"],
            "team_type": info["team_type"],
            "event": info.get("event", {}).get("name", ""),
            "team1": info["teams"][0],
            "team2": info["teams"][1],
            "venue": info["venue"],
            "city": info.get("city", ""),
            "outcome": winner(info["outcome"]),
            **classify(d),
            "cricsheet_url": f"https://cricsheet.org/matches/{os.path.basename(path)[:-5]}/",
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    # Cricsheet omits city for some matches: borrow it from the same venue elsewhere,
    # else take the part after the last comma ("Guyana National Stadium, Providence").
    venue_city = {r["venue"]: r["city"] for r in rows if r["city"]}
    for r in rows:
        city = r["city"] or venue_city.get(r["venue"]) or r["venue"].split(",")[-1].strip()
        r["country"] = country_for(city, r["venue"]) or ""
    fields = list(rows[0].keys())
    for out, subset in ((OUT_ALL, rows), (OUT_RAIN, [r for r in rows if r["rain_affected"]])):
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(subset)
    print(f"{len(rows)} matches -> {OUT_ALL}")
    print(f"{sum(1 for r in rows if r['rain_affected'])} rain-affected -> {OUT_RAIN}")


if __name__ == "__main__":
    main()
