from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Static, TextArea

from models.task import NewTaskData, Task, TaskStatus
from db.notes import list_notes
from db.tasks import format_deadline, list_task_tags, parse_deadline
from ui.screens.modals.tag_suggester import TagSuggester

IMPORTANCE_OPTIONS = [
    ("1 - highest", 1),
    ("2 - high", 2),
    ("3 - medium", 3),
    ("4 - low", 4),
    ("5 - lowest", 5),
]

STATUS_OPTIONS = [
    ("pending", TaskStatus.PENDING),
    ("in progress", TaskStatus.IN_PROGRESS),
    ("complete", TaskStatus.COMPLETE),
    ("abandoned", TaskStatus.ABANDONED),
]


class TaskModal(ModalScreen):
    """Creates a task when opened without one, edits it when given one."""

    CSS_PATH = "task_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
    ]

    def __init__(self, task: Task | None = None):
        super().__init__()
        self.edited_task = task

    def linked_notes_line(self) -> str:
        if self.edited_task is None:
            return ""
        titles = [
            note.title for note in list_notes()
            if note.linked_task_id == self.edited_task.id
        ]
        return f"Linked notes: {', '.join(titles)}" if titles else ""

    def compose(self) -> ComposeResult:
        task = self.edited_task

        yield Vertical(
            Input(
                value=task.title if task else "",
                placeholder="Title",
                id="title",
            ),
            Horizontal(
                Select(
                    IMPORTANCE_OPTIONS,
                    value=task.importance if task else 3,
                    allow_blank=False,
                    compact=True,
                    id="importance",
                ),
                Select(
                    STATUS_OPTIONS,
                    value=task.status if task else TaskStatus.PENDING,
                    allow_blank=False,
                    compact=True,
                    id="status",
                ),
                id="importance_and_status_row",
            ),
            Input(
                value=format_deadline(task.deadline) if task else "",
                placeholder="Deadline (DD-MM-YYYY)",
                compact=True,
                id="deadline",
            ),
            Input(
                value=", ".join(task.tags or []) if task else "",
                placeholder="Tags, separated by commas",
                suggester=TagSuggester(list_task_tags()),
                compact=True,
                id="tags",
            ),
            TextArea(
                text=task.description if task else "",
                soft_wrap=True,
                placeholder="Description",
                id="description",
            ),
            # read-only: the link lives on the note, so it is edited from the note modals
            Static(self.linked_notes_line(), id="linked_notes"),
            Horizontal(
                Button("Cancel", id="cancel_button"),
                Button("Save" if task else "Create", variant="primary", id="save_button"),
                id="modal_buttons",
            ),
            id="task_modal",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_button":
            self.dismiss(None)
            return
        if event.button.id == "save_button":
            self.save()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.save()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def save(self) -> None:
        title = self.query_one("#title", Input).value.strip()
        if not title:
            self.notify("Title is required", severity="error")
            return

        try:
            deadline = parse_deadline(self.query_one("#deadline", Input).value)
        except ValueError:
            self.notify("Deadline must be DD-MM-YYYY", severity="error")
            return

        importance = self.query_one("#importance", Select).value
        if not isinstance(importance, int):
            importance = 3

        status = self.query_one("#status", Select).value
        if not isinstance(status, TaskStatus):
            status = TaskStatus.PENDING

        self.dismiss(
            NewTaskData(
                title=title,
                importance=importance,
                status=status,
                description=self.query_one("#description", TextArea).text,
                deadline=deadline,
                # create_task/update_task normalize (strip, lower, dedupe) via normalize_tags
                tags=self.query_one("#tags", Input).value.split(","),
            )
        )
