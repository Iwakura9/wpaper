from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Static
from textual.widget import Widget

from db.notes import list_notes
from models.note import NoteStatus


class NoteBoard(Widget):
    view_mode: reactive[str] = reactive("grid", recompose=True)

    def toggle_view(self) -> None:
        self.view_mode = "kanban" if self.view_mode == "grid" else "grid"

    def compose(self) -> ComposeResult:
        notes = list_notes()

        if self.view_mode == "grid":
            yield Horizontal(
                *(Static(note.title, classes="note_card") for note in notes),
                id="note_grid",
            )
            return

        yield Horizontal(
            *(
                Vertical(
                    Static(status.value, classes="kanban_column_title"),
                    *(
                        Static(note.title, classes="note_card")
                        for note in notes
                        if note.status is status
                    ),
                    classes="kanban_column",
                )
                for status in NoteStatus
            ),
            id="note_kanban",
        )
