from db.connection import get_connection


def initialize_db() -> None:
    with get_connection() as con:
        con.execute("""
           CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'writing',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
           )
        """)  # TODO: Colocar o linked_task_id

        con.execute("""
           CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            PRIMARY KEY (note_id, tag)
           )
        """)
