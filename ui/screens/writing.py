from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.app import ComposeResult
from textual.widgets import Footer, Static, TextArea

from ui.screens.modals.new_note_modal import NewNoteData

class WritingScreen(Screen):
    CSS_PATH = "writing.tcss"

    BINDINGS = [
        ("ctrl+s", "save_note", "Save"),
        ("ctrl+c", "quit_no_save", "Quit"), # temporário, depois tirar
        # ("escape", "open_menu", ) --> abrir um menu com informações/metadados
    ]

    def __init__(self, note: NewNoteData):
        super().__init__()
        self.note = note

    def compose(self) -> ComposeResult:
        yield Vertical(
            Vertical(
                Static(self.note.title, id="note_title"),
                Static(self.note.created_at, id="note_date"), # tem que ver isso aqui
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
        body = self.query_one("#note_body", TextArea).text

        # Futuramente salvar os metadados no SQLite e depois excluir essa bosta
        self.notify("Save is not implemented yet", severity="warning")

    def action_open_menu(self) -> None:
        # menuzinho pra poder ver/alterar os metadados, salvar e sair
        pass

    def action_quit_no_save(self) -> None:
        self.app.pop_screen()
