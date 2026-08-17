from rich.table import Table
from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static

from db.search import SNIPPET_END, SNIPPET_START, Hit, search, sync_index
from db.tasks import format_deadline
from models.note import Note
from models.task import Task
from ui.screens.dashboard import format_status


def _snippet_text(snippet: str) -> Text:
    # splits on the sentinel bytes db.search wraps a match in, rather than turning them
    # into markup, so a snippet containing "[" or "]" can never be misread as a tag
    text = Text(overflow="ellipsis", no_wrap=True, style="dim")
    segments = snippet.split(SNIPPET_START)
    text.append(segments[0])
    for segment in segments[1:]:
        marked, _, rest = segment.partition(SNIPPET_END)
        text.append(marked, style="reverse not dim")
        text.append(rest)
    return text


def _meta_text(item: Note | Task) -> Text:
    if isinstance(item, Note):
        meta = Text(item.status.value, style="dim")
        if item.tags:
            meta.append("  ·  " + ", ".join(item.tags), style="dim")
        return meta

    meta = Text(f"{format_status(item.status)}  ·  !{item.importance}", style="dim")
    deadline = format_deadline(item.deadline)
    if deadline:
        meta.append(f"  ·  {deadline}", style="dim")
    return meta


def _render_hit(hit: Hit) -> Table:
    # a grid, not a markup string: keeps the title/meta columns aligned regardless of
    # title length, and truncates a long title with an ellipsis instead of wrapping it
    grid = Table.grid(expand=True, padding=(0, 0, 0, 1))
    grid.add_column(ratio=1, overflow="ellipsis", no_wrap=True)
    grid.add_column(justify="right", no_wrap=True)
    grid.add_row(Text(hit.item.title, style="bold", overflow="ellipsis", no_wrap=True), _meta_text(hit.item))
    if hit.snippet:
        grid.add_row(_snippet_text(hit.snippet))
    return grid


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
        container = Vertical(
            Input(placeholder="Search notes and tasks…", id="search_query"),
            ListView(id="search_results"),
            id="search_modal",
        )
        container.border_title = "Search"
        container.border_subtitle = "is:note/task   tag:x   status:y"
        yield container

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
