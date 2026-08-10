from db.connection import get_connection


def _set_tags(table: str, id_column: str, item_id: int, tags: list[str]) -> None:
    clean_tags = {tag.strip().lower() for tag in tags if tag.strip()}

    with get_connection() as con:
        con.execute(f"DELETE FROM {table} WHERE {id_column} = ?", (item_id,))
        con.executemany(
            f"INSERT INTO {table} ({id_column}, tag) VALUES (?, ?)",
            [(item_id, tag) for tag in clean_tags],
        )


def _tags_for(table: str, id_column: str, item_id: int) -> list[str]:
    with get_connection() as con:
        rows = con.execute(
            f"SELECT tag FROM {table} WHERE {id_column} = ? ORDER BY tag",
            (item_id,),
        ).fetchall()

    return [row["tag"] for row in rows]


def _all_tags(table: str) -> list[str]:
    with get_connection() as con:
        rows = con.execute(f"SELECT DISTINCT tag FROM {table} ORDER BY tag").fetchall()

    return [row["tag"] for row in rows]


def set_note_tags(note_id: int, tags: list[str]) -> None:
    _set_tags("note_tags", "note_id", note_id, tags)


def tags_for_note(note_id: int) -> list[str]:
    return _tags_for("note_tags", "note_id", note_id)


def all_note_tags() -> list[str]:
    return _all_tags("note_tags")


def set_task_tags(task_id: int, tags: list[str]) -> None:
    _set_tags("task_tags", "task_id", task_id, tags)


def tags_for_task(task_id: int) -> list[str]:
    return _tags_for("task_tags", "task_id", task_id)


def all_task_tags() -> list[str]:
    return _all_tags("task_tags")
