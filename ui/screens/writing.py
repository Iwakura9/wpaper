from textual.screen import Screen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Static, TextArea

from ui.screens.modals.new_note_modal import NewNoteData

class WritingScreen(Screen):
    CSS_PATH = "writing.tcss"

    BINDINGS = [
        ("ctrl+s", "save_note", "Save")
        # ("escape", "open_menu", ) --> abrir um menu com informações/metadados
    ]

    