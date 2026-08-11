from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from models.task import NewTaskData, Task
from db.tasks import create_task, delete_task, format_deadline, list_tasks, update_task
from ui.screens.modals.confirm_modal import ConfirmModal
from ui.screens.modals.task_modal import TaskModal

STATUS_LABELS = {
    "pending": "pending",
    "in_progress": "in progress",
    "complete": "complete",
    "abandoned": "abandoned",
}


class TasksScreen(Screen):
    CSS_PATH = "tasks.tcss"

    BINDINGS = [
        ("n", "new_task", "New"),
        ("f2", "edit_task", "Edit"),
        ("d", "delete_task", "Delete"),
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Tasks", id="tasks_title"),
            DataTable(id="tasks_table", cursor_type="row", zebra_stripes=True),
            id="tasks_screen",
        )
        yield Footer(compact=True)

    def on_mount(self) -> None:
        table = self.query_one("#tasks_table", DataTable)
        table.add_columns("!", "Title", "Status", "Deadline", "Tags")
        self.refresh_tasks()
        table.focus()

    def refresh_tasks(self) -> None:
        table = self.query_one("#tasks_table", DataTable)
        table.clear()

        self.tasks: dict[str, Task] = {}
        for task in list_tasks():
            key = str(task.id)
            self.tasks[key] = task
            table.add_row(
                str(task.importance),
                task.title,
                STATUS_LABELS[task.status.value],
                format_deadline(task.deadline) or "-",
                ", ".join(task.tags or []) or "-",
                key=key,
            )

    def selected_task(self) -> Task | None:
        table = self.query_one("#tasks_table", DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        return self.tasks.get(str(row_key.value))

    def action_new_task(self) -> None:
        self.app.push_screen(TaskModal(), self.on_task_created)

    def on_task_created(self, data: NewTaskData | None) -> None:
        if data is None:
            return
        create_task(data)
        self.refresh_tasks()

    def action_edit_task(self) -> None:
        task = self.selected_task()
        if task is None:
            return
        # held across the modal: the cursor may sit elsewhere by the time it dismisses
        self.pending = task
        self.app.push_screen(TaskModal(task), self.on_task_edited)

    def on_task_edited(self, data: NewTaskData | None) -> None:
        if data is None:
            return
        update_task(self.pending.id, data)
        self.refresh_tasks()

    def action_delete_task(self) -> None:
        task = self.selected_task()
        if task is None:
            return
        self.pending = task
        self.app.push_screen(ConfirmModal(f'Delete "{task.title}"?'), self.on_delete_confirmed)

    def on_delete_confirmed(self, confirmed: bool | None) -> None:
        if not confirmed:
            return
        delete_task(self.pending.id)
        self.refresh_tasks()
        self.notify("Task deleted")

    def action_go_back(self) -> None:
        self.app.pop_screen()
