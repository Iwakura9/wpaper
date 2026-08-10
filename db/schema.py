import re
import sqlite3

from config import NOTES_DIR
from db.connection import get_connection


def _m01_notes(con: sqlite3.Connection) -> None:
    con.execute("""
       CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'writing',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
       )
    """)


def _m02_notes_to_files(con: sqlite3.Connection) -> None:
    con.execute("ALTER TABLE notes ADD COLUMN filename TEXT NOT NULL DEFAULT ''")

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    rows = con.execute("SELECT id, title, content FROM notes").fetchall()
    for row in rows:
        slug = re.sub(r"[^a-z0-9]+", "-", row["title"].lower()).strip("-")
        filename = f"{row['id']}-{slug}.md" if slug else f"{row['id']}.md"
        (NOTES_DIR / filename).write_text(row["content"], encoding="utf-8")
        con.execute("UPDATE notes SET filename = ? WHERE id = ?", (filename, row["id"]))

    con.execute("ALTER TABLE notes DROP COLUMN content")


MIGRATIONS = [_m01_notes, _m02_notes_to_files]


def initialize_db() -> None:
    with get_connection() as con:
        version = con.execute("PRAGMA user_version").fetchone()[0]
        for i, migrate in enumerate(MIGRATIONS[version:], start=version):
            migrate(con)
            con.execute(f"PRAGMA user_version = {i + 1}")
