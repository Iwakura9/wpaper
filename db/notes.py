import re
from datetime import datetime
from pathlib import Path

from config import NOTES_DIR
from models.note import NewNoteData, Note, NoteStatus
from db.connection import get_connection
from db.tags import set_note_tags, tags_for_note

def now_timestamp() -> int:
    # função pra retornar data e horário em segundos
    return int(datetime.now().timestamp())

def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

def note_path(note: Note) -> Path:
    return NOTES_DIR / note.filename

def read_content(note: Note) -> str:
    return note_path(note).read_text(encoding="utf-8")

def write_content(note: Note, content: str) -> None:
    note_path(note).write_text(content, encoding="utf-8")

    with get_connection() as con:
        con.execute(
            "UPDATE notes SET updated_at = ? WHERE id = ?",
            (now_timestamp(), note.id),
        )

def create_note(data: NewNoteData) -> Note: # retorna ID
    now = now_timestamp()

    with get_connection() as con:
        cursor = con.execute("""
            INSERT INTO notes (
                title,
                status,
                created_at,
                updated_at,
                linked_task_id
            )
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                data.title,
                data.status.value,
                now,
                now,
                data.linked_task_id,
            ),
        )

        note_id = cursor.lastrowid

        if note_id is None:
            raise RuntimeError("Failed to create note")

        slug = slugify(data.title)
        filename = f"{note_id}-{slug}.md" if slug else f"{note_id}.md"

        con.execute("UPDATE notes SET filename = ? WHERE id = ?", (filename, note_id))

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    (NOTES_DIR / filename).write_text("", encoding="utf-8")

    tags = data.tags or []
    set_note_tags(note_id, tags)

    return Note(
        id=note_id,
        title=data.title,
        status=data.status,
        filename=filename,
        created_at=now,
        updated_at=now,
        tags=tags_for_note(note_id),
        linked_task_id=data.linked_task_id,
    )


def list_notes() -> list[Note]:
    with get_connection() as con:
        rows = con.execute("""
            SELECT
                id,
                title,
                filename,
                status,
                created_at,
                updated_at,
                linked_task_id
            FROM notes
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

    return [
        Note(
            id=row["id"],
            title=row["title"],
            filename=row["filename"],
            status=NoteStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=tags_for_note(row["id"]),
            linked_task_id=row["linked_task_id"],
        )
        for row in rows
    ]
