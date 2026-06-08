from textual.screen import Screen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Footer, Static, TextArea
from datetime import datetime

from models.note import Note
from db.notes import update_note_content

class WritingScreen(Screen):
    CSS_PATH = "writing.tcss"

    BINDINGS = [
        ("ctrl+s", "save_note", "Save"),
        ("ctrl+c", "quit_no_save", "Quit"), # temporário, depois tirar
        # ("escape", "open_menu", ) --> abrir um menu com informações/metadados
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
                text="",
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
        self.note.content = body

        self.notify("Note saved!")

        # Futuramente salvar os metadados no SQLite e depois excluir essa bosta
        # self.notify("Save is not implemented yet", severity="warning")

    def action_open_menu(self) -> None:
        # menuzinho pra poder ver/alterar os metadados, salvar e sair
        pass

    def action_quit_no_save(self) -> None:
        self.app.pop_screen()
