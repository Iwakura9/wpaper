from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Static
from textual.widget import Widget

from db.notes import list_notes
from models.note import Note, NoteStatus
from ui.screens.writing import WritingScreen


class NoteCard(Static):
    # ponytail: opens on mouse click only, no keyboard nav between cards yet;
    # add arrow-key focus traversal (or swap to a ListView) if that's needed
    def __init__(self, note: Note, **kwargs):
        super().__init__(note.title, **kwargs)
        self.note = note

    def on_click(self) -> None:
        self.app.push_screen(WritingScreen(self.note))


class NoteBoard(Widget):
    view_mode: reactive[str] = reactive("grid", recompose=True)

    def toggle_view(self) -> None:
        self.view_mode = "kanban" if self.view_mode == "grid" else "grid"

    def compose(self) -> ComposeResult:
        notes = list_notes()

        if self.view_mode == "grid":
            yield Horizontal(
                *(NoteCard(note, classes="note_card") for note in notes),
                id="note_grid",
            )
            return

        yield Horizontal(
            *(
                Vertical(
                    Static(status.value, classes="kanban_column_title"),
                    *(
                        NoteCard(note, classes="note_card")
                        for note in notes
                        if note.status is status
                    ),
                    classes="kanban_column",
                )
                for status in NoteStatus
            ),
            id="note_kanban",
        )
