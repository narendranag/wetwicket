"""Daily update from Cricsheet: fetch what changed, ingest it, and write the D1 delta.

    python pipeline/update.py            # exits 0; prints CHANGED=1 or CHANGED=0 for CI

Downloads are conditional (If-Modified-Since against the last run), so a quiet day costs Cricsheet
two small HEAD-sized requests. If data/wetwicket.sqlite is missing (for example a cold CI cache),
the full archive is downloaded and the database rebuilt first.
"""
import email.utils
import os
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
DB = os.path.join(ROOT, "data", "wetwicket.sqlite")
CHANGED = os.path.join(ROOT, "data", "changed_matches.txt")
UA = "wetwicket-ingest/1.0 (+https://github.com/narendranag/wetwicket)"
BASE = "https://cricsheet.org"
# Seven days, not two, so a missed nightly run is caught up by the next one.
RECENT = f"{BASE}/downloads/recently_added_7_json.zip"
FULL = f"{BASE}/downloads/all_json.zip"
REGISTER = [f"{BASE}/register/people.csv", f"{BASE}/register/names.csv"]


def meta(key, value=None):
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    if value is None:
        row = con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None
    con.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, value))
    con.commit()


def fetch(url, dest, since=None):
    """Download url to dest unless it is unchanged since `since`. Returns its Last-Modified, or None."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, **({"If-Modified-Since": since} if since else {})})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
            return r.headers.get("Last-Modified") or email.utils.formatdate(usegmt=True)
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return None
        raise


def run(*args):
    subprocess.run([sys.executable, *args], check=True, cwd=ROOT)


def main():
    os.makedirs(os.path.join(RAW, "register"), exist_ok=True)
    if os.path.exists(CHANGED):
        os.remove(CHANGED)
    changed = register_changed = False

    if not os.path.exists(DB):
        print("No database: rebuilding from the full archive")
        full = os.path.join(RAW, "all_json.zip")
        fetch(FULL, full)
        for url in REGISTER:
            fetch(url, os.path.join(RAW, "register", os.path.basename(url)))
        run("pipeline/ingest.py", "--register", os.path.join(RAW, "register"), "--matches", full)
        changed = register_changed = True

    got = [fetch(url, os.path.join(RAW, "register", os.path.basename(url)), meta(f"lm:{url}")) for url in REGISTER]
    if any(got):
        for url, lm in zip(REGISTER, got):
            if not lm:  # one file changed and the other didn't: fetch both so the pair is consistent
                fetch(url, os.path.join(RAW, "register", os.path.basename(url)))
        run("pipeline/ingest.py", "--register", os.path.join(RAW, "register"))
        for url, lm in zip(REGISTER, got):
            meta(f"lm:{url}", lm or email.utils.formatdate(usegmt=True))
        changed = register_changed = True
        print("Register updated")

    recent = os.path.join(RAW, "recently_added.zip")
    lm = fetch(RECENT, recent, meta(f"lm:{RECENT}"))
    if lm:
        with zipfile.ZipFile(recent) as z:
            print(f"Recent matches: {sum(n.endswith('.json') for n in z.namelist())} files")
        run("pipeline/ingest.py", "--matches", recent)
        meta(f"lm:{RECENT}", lm)
        changed = True
    else:
        print("No new matches since the last run")

    if changed:
        run("pipeline/export_d1.py", "--changed", *(["--with-register"] if register_changed else []))
        run("pipeline/build_site.py", "--rain-only")
    print(f"CHANGED={int(changed)}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
