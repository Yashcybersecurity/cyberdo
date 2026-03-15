#!/usr/bin/env python3
"""
CyberSentinel — Database Initialiser
Run once to create the SQLite database and load seed data.

Usage:
    python3 init_db.py
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "cybersentinel.db")

def init():
    print("CyberSentinel — Database Initialiser")
    print("=" * 42)

    # remove existing db for a clean start
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✓ Removed existing database")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")

    # apply schema
    schema_path = os.path.join(BASE_DIR, "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        con.executescript(f.read())
    print("✓ Schema applied (13 tables, indexes, triggers)")

    # load seed data
    seed_path = os.path.join(BASE_DIR, "seed.sql")
    if os.path.exists(seed_path):
        with open(seed_path, encoding="utf-8") as f:
            con.executescript(f.read())
        print("✓ Seed data loaded")
    else:
        print("(No seed.sql found, skipping seed data)")

    # verification
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    print(f"\n  Tables created ({len(tables)}):")
    for t in tables:
        cnt = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"    {t:<30} {cnt:>4} rows")

    con.close()
    print(f"\n✓ Database ready → {DB_PATH}")
    print("\nTo start the API server:")
    print("  python3 api.py")

if __name__ == "__main__":
    init()
