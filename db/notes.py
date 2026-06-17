from datetime import datetime

from models.note import NewNoteData, Note, NoteStatus
from db.connection import get_connection

def now_timestamp() -> int:
    # função pra retornar data e horário em segundos
    return int(datetime.now().timestamp())

def create_note(data: NewNoteData) -> Note: # retorna ID
    now = now_timestamp()

    with get_connection() as con:
        cursor = con.execute("""
            INSERT INTO notes (
                title,
                content,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                data.title,
                "",
                data.status.value,
                now,
                now,
                # TODO: colocar linked_task_id
            ),
        )

        note_id = cursor.lastrowid

        if note_id is None:
            raise RuntimeError("Failed to create note")
        else:
            return Note(
                id=note_id,
                title=data.title,
                status=data.status,
                content="",
                created_at=now,
                updated_at=now,
                tags=data.tags,
            )


def update_note_content(note_id: int, content: str) -> None:
    with get_connection() as con:
        con.execute("""
            UPDATE notes
            SET content = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                content,
                now_timestamp(),
                note_id,
            ),
        )

def list_notes() -> list[Note]:
    with get_connection() as con:
        rows = con.execute("""
            SELECT
                id,
                title,
                content,
                status,
                created_at,
                updated_at
            FROM notes
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

    return [
        Note(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            status=NoteStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=None,
        )
        for row in rows
    ]
