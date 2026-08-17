from textual.app import App

from db.schema import initialize_db
from db.tasks import update_task
from models.note import Note
from models.task import NewTaskData, Task
from ui.screens.dashboard import DashboardScreen
from ui.screens.home import HomeScreen
from ui.screens.modals.task_modal import TaskModal
from ui.screens.writing import WritingScreen


class WpaperApp(App):
    TITLE = "wpaper"

    SCREENS = {
        "home": HomeScreen,
        "dashboard": DashboardScreen,
    }

    def on_mount(self) -> None:
        initialize_db()
        self.push_screen("home")

    # shared by HomeScreen/DashboardScreen's "/" (global search): a screen further down
    # the stack, e.g. WritingScreen, never binds "/" at all, so its Footer never shows a
    # search shortcut that wouldn't do anything useful there anyway
    def open_hit(self, item: Note | Task | None) -> None:
        if item is None:
            return
        if isinstance(item, Note):
            self.push_screen(WritingScreen(item))
        else:
            self.push_screen(TaskModal(item), lambda data: self.on_task_edited(item.id, data))

    def on_task_edited(self, task_id: int, data: NewTaskData | None) -> None:
        if data is None:
            return
        update_task(task_id, data)

if __name__ == "__main__":
    app = WpaperApp()
    app.run()
