from textual.screen import Screen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Footer, Static, TextArea
from datetime import datetime

from models.note import NewNoteData, Note
from db.connection import normalize_tags
from db.notes import read_note_content, update_note_content, update_note_metadata
from ui.external_editor import open_note_in_editor
from ui.screens.modals.confirm_modal import ConfirmModal
from ui.screens.modals.edit_note_modal import EditNoteModal

class WritingScreen(Screen):
    CSS_PATH = "writing.tcss"

    BINDINGS = [
        ("ctrl+s", "save_note", "Save"),
        ("escape", "back", "Back"),
        ("f2", "open_menu", "Menu"),
        ("f3", "edit_external", "Editor"),
    ]

    def __init__(self, note: Note):
        super().__init__()
        self.note = note
        self.saved_body = read_note_content(note)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Vertical(
                Static(self.note.title, id="note_title"),
                Static(datetime.fromtimestamp(self.note.updated_at).strftime("%d %b, %Y"), id="note_date"),
                id="header"
            ),
            TextArea(
                text=self.saved_body,
                language="markdown",
                soft_wrap=True,
                show_line_numbers=True,
                placeholder="Start writing...",
                id="note_body",
            ),
            id="writing_screen"
        )
        yield Footer(compact=True)

    def on_mount(self) -> None:
        self.query_one("#note_body", TextArea).focus()

    def action_save_note(self): # -> None (?):
        # puxa o que estiver escrito na area de texto
        body = self.query_one("#note_body", TextArea).text
        # e manda pra funçao de atualizar o conteudo, que pede id e o texto
        update_note_content(self.note.id, body)
        self.saved_body = body
        self.note.updated_at = int(datetime.now().timestamp())
        self.query_one("#note_date", Static).update(
            datetime.fromtimestamp(self.note.updated_at).strftime("%d %b, %Y")
        )

        self.notify("Note saved!")

    def action_edit_external(self) -> None:
        body = self.query_one("#note_body", TextArea)
        update_note_content(self.note.id, body.text)
        if open_note_in_editor(self.app, self.note):
            body.text = read_note_content(self.note)
            self.saved_body = body.text

    def action_open_menu(self) -> None:
        self.app.push_screen(EditNoteModal(self.note), self.on_note_edited)

    def on_note_edited(self, result: NewNoteData | None) -> None:
        if result is None:
            return

        self.note.file_path = update_note_metadata(self.note.id, result)
        self.note.title = result.title
        self.note.status = result.status
        self.note.tags = normalize_tags(result.tags)
        self.note.linked_task_id = result.linked_task_id

        self.query_one("#note_title", Static).update(result.title)

    def action_back(self) -> None:
        if self.query_one("#note_body", TextArea).text == self.saved_body:
            self.app.pop_screen()
            return
        self.app.push_screen(ConfirmModal("Discard unsaved changes?"), self.on_discard_confirmed)

    def on_discard_confirmed(self, confirmed: bool | None) -> None:
        if confirmed:
            self.app.pop_screen()
