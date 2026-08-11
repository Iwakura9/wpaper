from textual.screen import Screen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Footer, Static, TextArea
from datetime import datetime

from models.note import Note, NoteStatus
from db.notes import read_note_content, update_note_content, update_note_metadata
from ui.screens.modals.edit_note_modal import EditNoteModal

class WritingScreen(Screen):
    CSS_PATH = "writing.tcss"

    BINDINGS = [
        ("ctrl+s", "save_note", "Save"),
        ("ctrl+c", "quit_no_save", "Quit"), # temporário, depois tirar
        ("escape", "open_menu", "Menu"),
    ]

    def __init__(self, note: Note):
        super().__init__()
        self.note = note

    def compose(self) -> ComposeResult:
        yield Vertical(
            Vertical(
                Static(self.note.title, id="note_title"),
                Static(datetime.now().strftime("%d %b, %Y"), id="note_date"),
                id="header"
            ),
            TextArea(
                text=read_note_content(self.note),
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

        self.notify("Note saved!")

        # Futuramente salvar os metadados no SQLite e depois excluir essa bosta
        # self.notify("Save is not implemented yet", severity="warning")

    def action_open_menu(self) -> None:
        self.app.push_screen(EditNoteModal(self.note), self.on_note_edited)

    def on_note_edited(self, result: tuple[str, NoteStatus] | None) -> None:
        if result is None:
            return

        title, status = result
        new_file_path = update_note_metadata(self.note.id, title, status)
        self.note.title = title
        self.note.status = status
        self.note.file_path = new_file_path

        self.query_one("#note_title", Static).update(title)

    def action_quit_no_save(self) -> None:
        self.app.pop_screen()
