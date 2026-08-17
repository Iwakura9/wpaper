from rich.markup import escape

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static

from db.search import SNIPPET_END, SNIPPET_START, Hit, search, sync_index
from db.tasks import format_deadline
from models.note import Note
from models.task import Task


def _render_hit(hit: Hit) -> str:
    item = hit.item
    if isinstance(item, Note):
        header = f"📝 {escape(item.title)}"
        if item.tags:
            header += f"   [dim]{escape(', '.join(item.tags))}[/dim]"
    else:
        header = f"✓ {escape(item.title)}   [dim]!{item.importance}"
        deadline = format_deadline(item.deadline)
        if deadline:
            header += f" {deadline}"
        header += "[/dim]"

    lines = [header]
    if hit.snippet:
        snippet = escape(hit.snippet).replace(SNIPPET_START, "[reverse]").replace(SNIPPET_END, "[/reverse]")
        lines.append(f"  {snippet}")
    return "\n".join(lines)


class SearchModal(ModalScreen):
    """Search notes and tasks by title, body and tags. Dismisses with the picked Note/Task, or None."""

    CSS_PATH = "search_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
        Binding("down,ctrl+n", "cursor_down", show=False),
        Binding("up,ctrl+p", "cursor_up", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.hits: list[Hit] = []

    def compose(self) -> ComposeResult:
        yield Vertical(
            Input(placeholder="Search…  is:note  tag:x  status:y", id="search_query"),
            ListView(id="search_results"),
            id="search_modal",
        )

    def on_mount(self) -> None:
        sync_index()
        self.refresh_results("")
        self.query_one("#search_query", Input).focus()

    def refresh_results(self, query: str) -> None:
        self.hits = search(query)
        results = self.query_one("#search_results", ListView)
        results.clear()
        if not self.hits:
            results.append(ListItem(Static("No results", classes="search_empty")))
            return
        results.extend(ListItem(Static(_render_hit(hit))) for hit in self.hits)
        results.index = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        self.refresh_results(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.select_current()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.select_current()

    def select_current(self) -> None:
        if not self.hits:
            return
        index = self.query_one("#search_results", ListView).index
        if index is None or index >= len(self.hits):
            return
        self.dismiss(self.hits[index].item)

    def action_cursor_down(self) -> None:
        self.query_one("#search_results", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#search_results", ListView).action_cursor_up()

    def action_cancel(self) -> None:
        self.dismiss(None)
