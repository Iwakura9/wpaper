from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

from models.note import NoteStatus, NewNoteData
from db.notes import create_note
from db.tasks import list_tasks


class NewNoteModal(ModalScreen):
    CSS_PATH = "new_note_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
        ("e", "edit_note"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Input(placeholder="Title", id="title"),
            Horizontal(
                Select(
                    [
                        ("writing", NoteStatus.WRITING),
                        ("done", NoteStatus.DONE),
                        ("hiatus", NoteStatus.HIATUS),
                        ("abandoned", NoteStatus.ABANDONED),
                    ],
                    value=NoteStatus.WRITING,
                    allow_blank=False,
                    compact=True,
                    id="status",
                ),
                Label(datetime.now().strftime("%d %b, %Y"), id="date"),
                id="date_and_status_row",
            ),
            Select(
                [(task.title, task.id) for task in list_tasks()],
                prompt="No task",
                allow_blank=True,
                compact=True,
                id="task",
            ),
            Input(placeholder="Tags, separated by commas", compact=True, id="tags"),
            Horizontal(
                Button("Cancel", id="cancel_button"),
                Button("Create", variant="primary", id="create_note_button"),
                id="modal_buttons",
            ),
            id="new_note_modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_button":
            self.dismiss()
            return
        if event.button.id == "create_note_button":
            self.create_note()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.create_note()

    def action_cancel(self) -> None:
        self.dismiss()

    def action_edit_note(self) -> None:
        pass

    def create_note(self) -> None:
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

        note_data = NewNoteData(
            title=title,
            status=status,
            # create_note normalizes (strip, lower, dedupe) via normalize_tags
            tags=self.query_one("#tags", Input).value.split(","),
            linked_task_id=linked_task_id,
        )

        note = create_note(note_data)

        self.dismiss(note)
