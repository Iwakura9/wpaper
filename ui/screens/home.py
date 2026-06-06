from pathlib import Path
from random import choice

from textual.app import ComposeResult
from textual.widgets import Static
from textual.screen import Screen
from textual.containers import Vertical

def load_random_logo() -> str:
    logos_path = Path("ui/logos.txt")
    content = logos_path.read_text(encoding="utf-8")

    logos = [
        block.strip()
        for block in content.split('"\n\n"')
        if block.strip().strip('"')
    ]

    return choice(logos).strip().strip('"')

class HomeScreen(Screen):
    BINDINGS = [
        ("n", "new_note"),
        ("t", "new_task"),
        ("d", "view_dashboard"),
        ("q", "quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(load_random_logo(), id="logo"),
            Static("n - New note", classes="shortcut"),
            Static("t - New task", classes="shortcut"),
            Static("d - Dashboard", classes="shortcut"),
            Static("q - Quit", classes="shortcut"),
            id="home",
        )

    def action_new_note(self) -> None:
        self.app.push_screen("note_editor")

    def action_new_task(self) -> None:
        self.app.push_screen("task_editor")

    def action_view_dashboard(self) -> None:
        self.app.push_screen("dashboard")

    def action_quit(self) -> None:
        self.app.exit()
