from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer

from ui.widgets.stats_panel import StatsPanel
from ui.widgets.task_list import TaskList
from ui.widgets.note_board import NoteBoard


class DashboardScreen(Screen):
    CSS_PATH = "dashboard.tcss"

    BINDINGS = [
        ("v", "toggle_note_view", "Toggle notes view"),
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                StatsPanel(id="stats"),
                TaskList(id="tasks"),
                id="top_row",
            ),
            NoteBoard(id="notes"),
            id="dashboard",
        )
        yield Footer(compact=True)

    def action_toggle_note_view(self) -> None:
        self.query_one(NoteBoard).toggle_view()

    def action_back(self) -> None:
        self.app.pop_screen()
