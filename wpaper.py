from textual.app import App

import config
from db.schema import initialize_db
from db.tasks import update_task
from models.note import Note
from models.task import NewTaskData, Task
from ui.external_editor import open_note_in_editor
from ui.screens.dashboard import DashboardScreen
from ui.screens.home import HomeScreen
from ui.screens.modals.task_modal import TaskModal
from ui.screens.writing import WritingScreen


class WpaperApp(App):
    TITLE = "wpaper"

    # default vertical scrollbar is 2 cells wide; every scrollable widget in the app
    # (note board, kanban columns, DataTable, ...) picks this up via the universal selector
    CSS = """
    * {
        scrollbar-size-vertical: 1;
    }
    """

    SCREENS = {
        "home": HomeScreen,
        "dashboard": DashboardScreen,
    }

    def __init__(self):
        super().__init__()
        self.config = config.load()

    def on_mount(self) -> None:
        initialize_db()
        if self.config["theme"] in self.available_themes:
            self.theme = self.config["theme"]
        else:
            self.notify(f"Unknown theme {self.config['theme']!r} in config.toml", severity="warning")
        self.push_screen("home")

    def watch_theme(self, theme: str) -> None:
        config.save(theme=theme)

    # shared by HomeScreen/DashboardScreen's "/" (global search): a screen further down
    # the stack, e.g. WritingScreen, never binds "/" at all, so its Footer never shows a
    # search shortcut that wouldn't do anything useful there anyway
    def open_hit(self, item: Note | Task | None) -> None:
        if item is None:
            return
        if isinstance(item, Note):
            self.open_note(item)
        else:
            self.push_screen(TaskModal(item), lambda data: self.on_task_edited(item.id, data))

    # the one place notes get opened, so force_alt_editor applies everywhere a note is opened
    def open_note(self, note: Note) -> None:
        if self.config["force_alt_editor"]:
            open_note_in_editor(self, note)
        else:
            self.push_screen(WritingScreen(note))

    def on_task_edited(self, task_id: int, data: NewTaskData | None) -> None:
        if data is None:
            return
        update_task(task_id, data)

if __name__ == "__main__":
    app = WpaperApp()
    app.run()
