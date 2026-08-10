from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.widget import Widget

from db.tasks import list_tasks
from models.task import TaskStatus


def days_remaining(deadline: int) -> int:
    delta = datetime.fromtimestamp(deadline) - datetime.now()
    return delta.days


class TaskList(Widget):
    def compose(self) -> ComposeResult:
        yield DataTable(id="task_table", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("!", "Title", "Status", "Days left", "Deadline")

        open_tasks = [
            task
            for task in list_tasks()
            if task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        ]

        for task in open_tasks:
            if task.deadline is None:
                days_left, deadline_str = "", ""
            else:
                days_left = str(days_remaining(task.deadline))
                deadline_str = datetime.fromtimestamp(task.deadline).strftime("%d %b")

            table.add_row(
                str(task.importance),
                task.title,
                task.status.value,
                days_left,
                deadline_str,
                key=str(task.id),
            )
