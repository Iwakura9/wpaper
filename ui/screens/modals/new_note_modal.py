from dataclasses import dataclass
from enum import Enum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

class NoteStatus(Enum):
    WRITING = "writing"
    DONE = "done"
    HIATUS = "hiatus"
    ABANDONED = "abandoned"

@dataclass
class NewNoteData:
    title: str
    status: NoteStatus
    task: str  # possívelmente vai ter que mudar aqui no futuro
    tag: str  # aqui também

class NewNoteModal(ModalScreen):

    CSS_PATH = "new_note_modal.tcss"

    BINDINGS = [
        ("escape", "cancel")
    ]


    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Teste ok (WIP)", id="modal-title"),
            Button("OK", id="ok"),
            id="new-note-modal",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()
