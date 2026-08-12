import re
from pathlib import Path

from models.note import NewNoteData, Note, NoteStatus
from db.connection import get_connection, normalize_tags, now_timestamp, DATA_DIR

def get_notes_dir() -> Path:
    notes_dir = DATA_DIR / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir

def _build_filename(note_id: int, title: str) -> str:
    safe_title = title.strip().replace("/", "-")
    safe_title = re.sub(r"\s+", "_", safe_title)
    safe_title = re.sub(r'[\\:*?"<>|\x00-\x1f]', "", safe_title)
    return f"{note_id}-{safe_title[:200]}.md"

def _replace_tags(con, note_id: int, tags: list[str]) -> None:
    con.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
    for tag in tags:
        con.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag) VALUES (?, ?)",
            (note_id, tag),
        )

def create_note(data: NewNoteData) -> Note: # retorna ID
    now = now_timestamp()

    with get_connection() as con:
        cursor = con.execute("""
            INSERT INTO notes (
                title,
                file_path,
                status,
                created_at,
                updated_at,
                linked_task_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                data.title,
                "",
                data.status.value,
                now,
                now,
                data.linked_task_id,
            ),
        )

        note_id = cursor.lastrowid

        if note_id is None:
            raise RuntimeError("Failed to create note")

        file_path = _build_filename(note_id, data.title)
        (get_notes_dir() / file_path).write_text("", encoding="utf-8")

        con.execute("UPDATE notes SET file_path = ? WHERE id = ?", (file_path, note_id))

        tags = normalize_tags(data.tags)
        _replace_tags(con, note_id, tags)

        return Note(
            id=note_id,
            title=data.title,
            status=data.status,
            file_path=file_path,
            created_at=now,
            updated_at=now,
            tags=tags,
            linked_task_id=data.linked_task_id,
        )


def update_note_metadata(note_id: int, data: NewNoteData) -> str:
    with get_connection() as con:
        row = con.execute("SELECT file_path FROM notes WHERE id = ?", (note_id,)).fetchone()

        new_file_path = _build_filename(note_id, data.title)
        if new_file_path != row["file_path"]:
            (get_notes_dir() / row["file_path"]).rename(get_notes_dir() / new_file_path)

        con.execute(
            """
            UPDATE notes
            SET title = ?, status = ?, file_path = ?, updated_at = ?, linked_task_id = ?
            WHERE id = ?
            """,
            (
                data.title,
                data.status.value,
                new_file_path,
                now_timestamp(),
                data.linked_task_id,
                note_id,
            ),
        )

        _replace_tags(con, note_id, normalize_tags(data.tags))

        return new_file_path


def update_note_content(note_id: int, content: str) -> None:
    with get_connection() as con:
        row = con.execute("SELECT file_path FROM notes WHERE id = ?", (note_id,)).fetchone()
        (get_notes_dir() / row["file_path"]).write_text(content, encoding="utf-8")

        con.execute("""
            UPDATE notes
            SET updated_at = ?
            WHERE id = ?
            """,
            (
                now_timestamp(),
                note_id,
            ),
        )

def read_note_content(note: Note) -> str:
    file_path = get_notes_dir() / note.file_path
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")

def delete_note(note_id: int) -> None:
    with get_connection() as con:
        row = con.execute("SELECT file_path FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is not None:
            (get_notes_dir() / row["file_path"]).unlink(missing_ok=True)

        con.execute("DELETE FROM notes WHERE id = ?", (note_id,))

def list_note_tags() -> list[str]:
    with get_connection() as con:
        rows = con.execute("SELECT DISTINCT tag FROM note_tags ORDER BY tag").fetchall()
    return [row["tag"] for row in rows]

def list_notes() -> list[Note]:
    with get_connection() as con:
        rows = con.execute("""
            SELECT
                id,
                title,
                file_path,
                status,
                created_at,
                updated_at,
                linked_task_id
            FROM notes
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

        note_ids = [row["id"] for row in rows]
        tags_by_note: dict[int, list[str]] = {}
        if note_ids:
            placeholders = ",".join("?" * len(note_ids))
            tag_rows = con.execute(
                f"SELECT note_id, tag FROM note_tags WHERE note_id IN ({placeholders}) ORDER BY tag",
                note_ids,
            ).fetchall()
            for tag_row in tag_rows:
                tags_by_note.setdefault(tag_row["note_id"], []).append(tag_row["tag"])

    return [
        Note(
            id=row["id"],
            title=row["title"],
            file_path=row["file_path"],
            status=NoteStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=tags_by_note.get(row["id"], []),
            linked_task_id=row["linked_task_id"],
        )
        for row in rows
    ]
