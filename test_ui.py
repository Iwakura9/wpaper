import asyncio
import tempfile
from pathlib import Path

import db.connection
import db.notes

TMP_DIR = Path(tempfile.mkdtemp())
db.connection.DB_PATH = TMP_DIR / "test.sqlite"
db.connection.DATA_DIR = TMP_DIR
db.notes.DATA_DIR = TMP_DIR

from textual.widgets import Button, Input, Select, TextArea

from db.tasks import list_tasks
from models.task import TaskStatus
from ui.screens.modals.task_modal import TaskModal
from wpaper import WpaperApp


def screen_name(app) -> str:
    return type(app.screen).__name__


def press_button(app, button_id: str) -> None:
    # not pilot.click: the notification toast docks bottom-right over docked buttons
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

        # --- prefill: no screen opens this yet, the dashboard will ---
        app.push_screen(TaskModal(task))
        await pilot.pause()
        assert app.screen.query_one("#title", Input).value == "Write report"
        assert app.screen.query_one("#deadline", Input).value == "2026-09-01"
        assert app.screen.query_one("#tags", Input).value == "urgent, work"
        assert app.screen.query_one("#description", TextArea).text == "before the meeting"
        assert app.screen.query_one("#importance", Select).value == 1
        assert app.screen.query_one("#status", Select).value is TaskStatus.PENDING
        await pilot.press("escape")
        await pilot.pause()

        # --- notes still work ---
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
