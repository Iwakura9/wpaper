import asyncio
import tempfile
from pathlib import Path

import db.connection
import db.notes

TMP_DIR = Path(tempfile.mkdtemp())
db.connection.DB_PATH = TMP_DIR / "test.sqlite"
db.connection.DATA_DIR = TMP_DIR
db.notes.DATA_DIR = TMP_DIR

from textual.widgets import Button, DataTable, Input, Select, TextArea

from db.tasks import list_tasks
from models.task import TaskStatus
from wpaper import WpaperApp


def screen_name(app) -> str:
    return type(app.screen).__name__


def press_button(app, button_id: str) -> None:
    # not pilot.click: the notification toast docks bottom-right and covers docked buttons
    app.screen.query_one(f"#{button_id}", Button).press()


async def drive() -> None:
    app = WpaperApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert screen_name(app) == "HomeScreen", screen_name(app)

        # --- create a task from Home ---
        await pilot.press("t")
        await pilot.pause()
        assert screen_name(app) == "TaskModal", screen_name(app)

        app.screen.query_one("#title", Input).value = "Write report"
        app.screen.query_one("#deadline", Input).value = "not-a-date"
        app.screen.query_one("#tags", Input).value = "Work,  WORK , Urgent"
        app.screen.query_one("#description", TextArea).text = "before the meeting"
        app.screen.query_one("#importance", Select).value = 1

        press_button(app, "save_button")
        await pilot.pause()
        assert screen_name(app) == "TaskModal", "a bad deadline must keep the modal open"
        assert list_tasks() == []

        app.screen.query_one("#deadline", Input).value = "2026-09-01"
        press_button(app, "save_button")
        await pilot.pause()
        assert screen_name(app) == "HomeScreen", screen_name(app)

        (task,) = list_tasks()
        assert task.title == "Write report"
        assert task.importance == 1
        assert task.status is TaskStatus.PENDING
        assert task.description == "before the meeting"
        assert task.tags == ["urgent", "work"], task.tags

        # empty title is rejected too
        await pilot.press("t")
        await pilot.pause()
        press_button(app, "save_button")
        await pilot.pause()
        assert screen_name(app) == "TaskModal", "an empty title must keep the modal open"
        await pilot.press("escape")
        await pilot.pause()
        assert len(list_tasks()) == 1

        # --- tasks list ---
        await pilot.press("T")
        await pilot.pause()
        assert screen_name(app) == "TasksScreen", screen_name(app)
        table = app.screen.query_one("#tasks_table", DataTable)
        assert table.row_count == 1, table.row_count
        row = table.get_row_at(0)
        assert row[0] == "1" and row[1] == "Write report", row
        assert row[3] == "2026-09-01", row
        assert row[4] == "urgent, work", row

        # --- create from inside the list ---
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#title", Input).value = "Second task"
        app.screen.query_one("#importance", Select).value = 5
        press_button(app, "save_button")
        await pilot.pause()
        assert table.row_count == 2, table.row_count
        assert table.get_row_at(0)[1] == "Write report", "importance 1 should sort first"

        # --- edit the selected task ---
        await pilot.press("f2")
        await pilot.pause()
        assert screen_name(app) == "TaskModal", screen_name(app)
        assert app.screen.query_one("#title", Input).value == "Write report", "not prefilled"
        assert app.screen.query_one("#deadline", Input).value == "2026-09-01"
        assert app.screen.query_one("#tags", Input).value == "urgent, work"
        assert app.screen.query_one("#description", TextArea).text == "before the meeting"
        app.screen.query_one("#status", Select).value = TaskStatus.COMPLETE
        press_button(app, "save_button")
        await pilot.pause()

        assert table.row_count == 2
        # completed sinks below the open one even though it is importance 1
        assert table.get_row_at(0)[1] == "Second task", table.get_row_at(0)
        assert table.get_row_at(1)[2] == "complete", table.get_row_at(1)

        # --- delete: cancel, then confirm ---
        await pilot.press("d")
        await pilot.pause()
        assert screen_name(app) == "ConfirmModal", screen_name(app)
        press_button(app, "cancel_button")
        await pilot.pause()
        assert table.row_count == 2, "cancelling deleted the task anyway"

        await pilot.press("d")
        await pilot.pause()
        press_button(app, "confirm_button")
        await pilot.pause()
        assert table.row_count == 1, table.row_count
        assert [t.title for t in list_tasks()] == ["Write report"]

        # --- back home, notes still work ---
        await pilot.press("escape")
        await pilot.pause()
        assert screen_name(app) == "HomeScreen", screen_name(app)

        await pilot.press("n")
        await pilot.pause()
        assert screen_name(app) == "NewNoteModal", screen_name(app)
        app.screen.query_one("#title", Input).value = "A note"
        press_button(app, "create_note_button")
        await pilot.pause()
        assert screen_name(app) == "WritingScreen", screen_name(app)


if __name__ == "__main__":
    asyncio.run(drive())
    print("ok")
