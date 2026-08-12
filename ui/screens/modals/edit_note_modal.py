from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select

from models.note import NewNoteData, Note, NoteStatus
from db.tasks import list_tasks


class EditNoteModal(ModalScreen):
    CSS_PATH = "edit_note_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
    ]

    def __init__(self, note: Note):
        super().__init__()
        self.note = note

    def compose(self) -> ComposeResult:
        linked = self.note.linked_task_id
        yield Vertical(
            Input(value=self.note.title, placeholder="Title", id="title"),
            Select(
                [
                    ("writing", NoteStatus.WRITING),
                    ("done", NoteStatus.DONE),
                    ("hiatus", NoteStatus.HIATUS),
                    ("abandoned", NoteStatus.ABANDONED),
                ],
                value=self.note.status,
                allow_blank=False,
                compact=True,
                id="status",
            ),
            Select(
                [(task.title, task.id) for task in list_tasks()],
                # a deleted task nulls the link (ON DELETE SET NULL), so any id here still exists
                value=Select.NULL if linked is None else linked,
                prompt="No task",
                allow_blank=True,
                compact=True,
                id="task",
            ),
            Input(
                value=", ".join(self.note.tags or []),
                placeholder="Tags, separated by commas",
                compact=True,
                id="tags",
            ),
            Horizontal(
                Button("Cancel", id="cancel_button"),
                Button("Save", variant="primary", id="save_button"),
                id="modal_buttons",
            ),
            id="edit_note_modal"
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

        status = self.query_one("#status", Select).value
        if not isinstance(status, NoteStatus):
            status = NoteStatus.WRITING

        linked_task_id = self.query_one("#task", Select).value
        if not isinstance(linked_task_id, int):  # Select.NULL
            linked_task_id = None

        self.dismiss(
            NewNoteData(
                title=title,
                status=status,
                # update_note_metadata normalizes (strip, lower, dedupe) via normalize_tags
                tags=self.query_one("#tags", Input).value.split(","),
                linked_task_id=linked_task_id,
            )
        )
