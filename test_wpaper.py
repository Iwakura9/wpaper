import os
import tempfile

_tmpdir = tempfile.TemporaryDirectory()
os.environ["WPAPER_DATA_DIR"] = _tmpdir.name

import re

from config import NOTES_DIR
from db.connection import get_connection
from db.schema import initialize_db, _m01_notes
from db.notes import slugify, create_note, write_content, read_content
from models.note import NewNoteData, NoteStatus


def test_slugify():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  Multiple   spaces  ") == "multiple-spaces"
    accented = slugify("Título com Acentuação")
    assert re.fullmatch(r"[a-z0-9-]*", accented), accented
    assert accented


def test_migration_preserves_content():
    # simulate a pre-existing db that only has the original notes schema
    with get_connection() as con:
        _m01_notes(con)
        con.execute(
            "INSERT INTO notes (title, content, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("My Note", "hello disk", "writing", 1, 1),
        )
        con.execute("PRAGMA user_version = 1")

    initialize_db()  # should run _m02_notes_to_files and move content to disk

    with get_connection() as con:
        row = con.execute("SELECT id, filename FROM notes").fetchone()

    assert row["filename"] == f"{row['id']}-my-note.md"
    assert (NOTES_DIR / row["filename"]).read_text(encoding="utf-8") == "hello disk"


def test_roundtrip():
    note = create_note(NewNoteData(title="Round Trip", status=NoteStatus.WRITING))
    assert read_content(note) == ""

    write_content(note, "some content")
    assert read_content(note) == "some content"


if __name__ == "__main__":
    test_slugify()
    test_migration_preserves_content()
    test_roundtrip()
    print("All tests passed.")
    _tmpdir.cleanup()
