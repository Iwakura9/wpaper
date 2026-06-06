from dataclasses import dataclass
from datetime import date
from enum import Enum
from functools import Placeholder
from statistics import variance

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

class NoteStatus(Enum):
    WRITING = "writing"
    DONE = "done"
    HIATUS = "hiatus"
    ABANDONED = "abandoned"

@dataclass
class NewNoteData:
    title: str
    status: NoteStatus
    # task: str  # possívelmente vai ter que mudar aqui no futuro
    tags: str | None =None

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
                Label(date.today().strftime("%d %b, %Y")),
                Select(
                    [
                        ("writing", NoteStatus.WRITING),
                        ("done", NoteStatus.DONE),
                        ("hiatus", NoteStatus.HIATUS),
                        ("abandoned", NoteStatus.ABANDONED),
                    ],
                    value=NoteStatus.WRITING,
                    allow_blank=False,
                    id="status",
                ),
                id="date_and_status_row",
            ),
            Input(placeholder="Tags", id="tags"),
            Horizontal(
                Button("Cancel", id="cancel_button"),
                Button("Create", variant="primary", id="create_note_button"),
                id="modal-buttons",
            ),
            id="new-note-modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
            return
        if event.button.id == "create_note_button":
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

        tags = self.query_one("#tags", Input).value.strip() or None

        self.dismiss(
            NewNoteData(
                title=title,
                status=status,
                tags=tags,
            )
        )
