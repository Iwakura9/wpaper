from datetime import datetime

from models.note import NewNoteData, NoteStatus
from db.connection import get_connection

def now_timestamp() -> int:
    # função pra retornar data e horário em segundos
    return int(datetime.now().timestamp())

def create_note(note: NewNoteData, content: str="") -> int: # retorna ID
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
                note.title,
                content,
                note.status.value,
                now,
                now,
                # TODO: colocar linked_task_id
            ),
        )

        note_id = cursor.lastrowid

        if note_id is None:
            raise RuntimeError("Failed to create note")
        else:
            return note_id


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
