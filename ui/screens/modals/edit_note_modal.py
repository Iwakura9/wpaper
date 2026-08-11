from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select

from models.note import Note, NoteStatus


class EditNoteModal(ModalScreen):
    CSS_PATH = "edit_note_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
    ]

    def __init__(self, note: Note):
        super().__init__()
        self.note = note

    def compose(self) -> ComposeResult:
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

        self.dismiss((title, status))
