import tempfile
from pathlib import Path

import db.connection
import db.notes

TMP_DIR = Path(tempfile.mkdtemp())

# get_connection reads DB_PATH at call time, so pointing it at a temp file is enough.
# db.notes imported DATA_DIR by value, so it needs its own patch to keep the real
# ~/Documents/wpaper untouched.
db.connection.DB_PATH = TMP_DIR / "test.sqlite"
db.connection.DATA_DIR = TMP_DIR
db.notes.DATA_DIR = TMP_DIR

from db.schema import initialize_db
from db.tasks import (
    create_task,
    delete_task,
    format_deadline,
    list_tasks,
    parse_deadline,
    update_task,
)
from models.task import NewTaskData, TaskStatus


def test_deadline_roundtrip() -> None:
    assert parse_deadline("") is None
    assert parse_deadline("   ") is None
    assert format_deadline(None) == ""

    stamp = parse_deadline("2026-09-01")
    assert stamp is not None
    assert format_deadline(stamp) == "2026-09-01"

    try:
        parse_deadline("01/09/2026")
    except ValueError:
        pass
    else:
        raise AssertionError("parse_deadline accepted a bad format")


def test_task_crud() -> None:
    initialize_db()
    assert list_tasks() == []

    task = create_task(
        NewTaskData(
            title="Write the report",
            importance=1,
            status=TaskStatus.PENDING,
            description="due before the meeting",
            deadline=parse_deadline("2026-09-01"),
            tags=["Work", "  work ", "URGENT"],
        )
    )
    assert task.tags == ["work", "urgent"], task.tags

    (stored,) = list_tasks()
    assert stored.id == task.id
    assert stored.title == "Write the report"
    assert stored.importance == 1
    assert stored.status is TaskStatus.PENDING
    assert stored.description == "due before the meeting"
    assert format_deadline(stored.deadline) == "2026-09-01"
    assert stored.tags == ["urgent", "work"], stored.tags  # list_tasks orders tags

    update_task(
        task.id,
        NewTaskData(
            title="Write the report v2",
            importance=4,
            status=TaskStatus.COMPLETE,
            description="",
            deadline=None,
            tags=["done"],
        ),
    )

    (stored,) = list_tasks()
    assert stored.title == "Write the report v2"
    assert stored.importance == 4
    assert stored.status is TaskStatus.COMPLETE
    assert stored.deadline is None
    assert stored.tags == ["done"], stored.tags

    delete_task(task.id)
    assert list_tasks() == []

    with db.connection.get_connection() as con:
        leftover = con.execute("SELECT COUNT(*) AS n FROM task_tags").fetchone()["n"]
    assert leftover == 0, "task_tags did not cascade"


def test_list_order() -> None:
    for title, importance, status, deadline in [
        ("open low", 5, TaskStatus.PENDING, None),
        ("open high", 1, TaskStatus.IN_PROGRESS, None),
        ("open high soon", 1, TaskStatus.PENDING, parse_deadline("2026-01-01")),
        ("finished top", 1, TaskStatus.COMPLETE, None),
    ]:
        create_task(
            NewTaskData(title=title, importance=importance, status=status, deadline=deadline)
        )

    titles = [task.title for task in list_tasks()]
    # open first, then most important, then nearest deadline; done sinks to the bottom
    assert titles == ["open high soon", "open high", "open low", "finished top"], titles

    for task in list_tasks():
        delete_task(task.id)


def test_notes_still_work() -> None:
    from db.notes import create_note, list_notes, read_note_content, update_note_content
    from models.note import NewNoteData, NoteStatus

    # writes into TMP_DIR/notes, not the real data dir
    note = create_note(NewNoteData(title="A note", status=NoteStatus.WRITING, tags=["Alpha"]))
    update_note_content(note.id, "hello")
    assert read_note_content(note) == "hello"
    assert [n.tags for n in list_notes()] == [["alpha"]]

    with db.connection.get_connection() as con:
        columns = {row["name"] for row in con.execute("PRAGMA table_info(notes)")}
    assert "linked_task_id" in columns


if __name__ == "__main__":
    test_deadline_roundtrip()
    test_task_crud()
    test_list_order()
    test_notes_still_work()
    print("ok")
