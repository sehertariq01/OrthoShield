"""
Migration 001 — Add quarantine_path and incomplete_scan to scan_logs
=====================================================================
Run this ONCE against the existing orthoshield.db to bring the schema
in line with models.py after the Fix 2 / Fix 3 changes.

Usage:
    python backend/migrations/001_quarantine_columns.py

The script is idempotent: it checks whether the columns already exist
before attempting to add them, so it is safe to run more than once.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "orthoshield.db")


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def run() -> None:
    if not os.path.exists(DB_PATH):
        print(f"[001] Database not found at {DB_PATH} — nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    added = []

    # ALTER TABLE scan_logs ADD COLUMN quarantine_path VARCHAR(500);
    if not column_exists(cur, "scan_logs", "quarantine_path"):
        cur.execute("ALTER TABLE scan_logs ADD COLUMN quarantine_path VARCHAR(500)")
        added.append("quarantine_path")

    # ALTER TABLE scan_logs ADD COLUMN incomplete_scan BOOLEAN DEFAULT 0;
    if not column_exists(cur, "scan_logs", "incomplete_scan"):
        cur.execute("ALTER TABLE scan_logs ADD COLUMN incomplete_scan BOOLEAN DEFAULT 0")
        added.append("incomplete_scan")

    conn.commit()
    conn.close()

    if added:
        print(f"[001] Migration applied — added columns: {', '.join(added)}")
    else:
        print("[001] Nothing to do — columns already exist.")


if __name__ == "__main__":
    run()
