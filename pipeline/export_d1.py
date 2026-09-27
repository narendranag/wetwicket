"""Write SQL that loads data/wetwicket.sqlite into Cloudflare D1.

    python pipeline/export_d1.py --full      # data/d1/full.sql: schema + every row
    python pipeline/export_d1.py --changed   # data/d1/delta.sql: matches in data/changed_matches.txt,
                                             # plus venues, competitions and meta; --with-register adds people

Apply with: wrangler d1 execute wetwicket --remote --file data/d1/<file>.sql  (or --local)
"""
import argparse
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "wetwicket.sqlite")
OUT = os.path.join(ROOT, "data", "d1")
CHANGED = os.path.join(ROOT, "data", "changed_matches.txt")
MATCH_TABLES = {"matches": "id", "innings": "match_id", "batting": "match_id", "bowling": "match_id",
                "match_players": "match_id"}
SMALL_TABLES = ["venues", "competitions", "meta"]
REGISTER_TABLES = ["people", "people_names"]
MAX_STMT = 90_000  # D1 caps a single statement at 100 KB


def quote(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def inserts(con, table, where="", params=()):
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
    head = f"INSERT INTO {table} ({','.join(cols)}) VALUES "
    batch, size = [], len(head)
    for row in con.execute(f"SELECT {','.join(cols)} FROM {table} {where}", params):
        v = "(" + ",".join(quote(x) for x in row) + ")"
        if batch and size + len(v) > MAX_STMT:
            yield head + ",".join(batch) + ";\n"
            batch, size = [], len(head)
        batch.append(v)
        size += len(v) + 1
    if batch:
        yield head + ",".join(batch) + ";\n"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--full", action="store_true")
    g.add_argument("--changed", action="store_true")
    ap.add_argument("--with-register", action="store_true", help="also resend the Cricsheet Register tables")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    con = sqlite3.connect(DB)
    if args.full:
        path = os.path.join(OUT, "full.sql")
        with open(path, "w") as f:
            for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                f.write(f"DROP TABLE IF EXISTS {table};\n")
            f.write(open(os.path.join(ROOT, "db", "schema.sql")).read() + "\n")
            for table in [*MATCH_TABLES, *SMALL_TABLES, *REGISTER_TABLES]:
                f.writelines(inserts(con, table))
    else:
        ids = sorted(set(open(CHANGED).read().split())) if os.path.exists(CHANGED) else []
        path = os.path.join(OUT, "delta.sql")
        with open(path, "w") as f:
            for i in range(0, len(ids), 200):
                chunk = ids[i:i + 200]
                marks = ",".join(quote(x) for x in chunk)
                for table, key in MATCH_TABLES.items():
                    f.write(f"DELETE FROM {table} WHERE {key} IN ({marks});\n")
                    f.writelines(inserts(con, table, f"WHERE {key} IN ({','.join('?' * len(chunk))})", chunk))
            for table in SMALL_TABLES + (REGISTER_TABLES if args.with_register else []):
                f.write(f"DELETE FROM {table};\n")
                f.writelines(inserts(con, table))
        print(f"{len(ids)} changed matches")
    print(f"-> {path} ({os.path.getsize(path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
