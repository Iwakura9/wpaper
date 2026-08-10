from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select

from models.task import TaskStatus, NewTaskData
from db.tasks import create_task


class NewTaskModal(ModalScreen):
    CSS_PATH = "new_task_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Input(placeholder="Title", id="title"),
            Horizontal(
                Select(
                    [
                        ("pending", TaskStatus.PENDING),
                        ("in progress", TaskStatus.IN_PROGRESS),
                        ("complete", TaskStatus.COMPLETE),
                        ("abandoned", TaskStatus.ABANDONED),
                    ],
                    value=TaskStatus.PENDING,
                    allow_blank=False,
                    compact=True,
                    id="status",
                ),
                Select(
                    [(str(n), n) for n in range(1, 6)],
                    value=3,
                    allow_blank=False,
                    compact=True,
                    id="importance",
                ),
                id="status_and_importance_row",
            ),
            Input(placeholder="Deadline (YYYY-MM-DD, optional)", compact=True, id="deadline"),
            Input(placeholder="Description", compact=True, id="description"),
            Input(placeholder="Tags, separated by commas", compact=True, id="tags"),
            Horizontal(
                Button("Cancel", id="cancel_button"),
                Button("Create", variant="primary", id="create_task_button"),
                id="modal_buttons",
            ),
            id="new_task_modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_button":
            self.dismiss()
            return
        if event.button.id == "create_task_button":
            self.create_task()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.create_task()

    def action_cancel(self) -> None:
        self.dismiss()

    def create_task(self) -> None:
        title = self.query_one("#title", Input).value.strip()
        if not title:
            self.notify("Title is required", severity="error")
            return

        status = self.query_one("#status", Select).value
        if not isinstance(status, TaskStatus):
            status = TaskStatus.PENDING

        importance = self.query_one("#importance", Select).value
        if not isinstance(importance, int):
            importance = 3

        deadline_input = self.query_one("#deadline", Input).value.strip()
        deadline = None
        if deadline_input:
            try:
                deadline = int(datetime.strptime(deadline_input, "%Y-%m-%d").timestamp())
            except ValueError:
                self.notify("Deadline must be in YYYY-MM-DD format", severity="error")
                return

        description = self.query_one("#description", Input).value.strip()

        tags_input = self.query_one("#tags", Input).value.strip()
        tags = []
        for tag in tags_input.split(","):
            if tag.strip():
                tags.append(tag.strip().lower())

        task_data = NewTaskData(
            title=title,
            status=status,
            importance=importance,
            description=description,
            deadline=deadline,
            tags=tags,
        )

        task = create_task(task_data)

        self.dismiss(task)
