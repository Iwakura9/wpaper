from db.connection import get_connection


def initialize_db() -> None:
    with get_connection() as con:
        con.execute("""
           CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            importance INTEGER NOT NULL DEFAULT 3,
            status TEXT NOT NULL DEFAULT 'pending',
            description TEXT NOT NULL DEFAULT '',
            deadline INTEGER,
            created_at INTEGER NOT NULL
           )
        """)

        con.execute("""
           CREATE TABLE IF NOT EXISTS task_tags (
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            PRIMARY KEY (task_id, tag)
           )
        """)

        con.execute("""
           CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'writing',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            linked_task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL
           )
        """)

        con.execute("""
           CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            PRIMARY KEY (note_id, tag)
           )
        """)

        # ponytail: ad-hoc migration, real migration system when a destructive change lands
        columns = {row["name"] for row in con.execute("PRAGMA table_info(notes)")}
        if "linked_task_id" not in columns:
            con.execute(
                "ALTER TABLE notes ADD COLUMN linked_task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL"
            )
