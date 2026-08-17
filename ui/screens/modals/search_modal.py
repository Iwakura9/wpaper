from rich.table import Table
from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static

from db.search import SNIPPET_END, SNIPPET_START, Hit, search, sync_index
from db.tasks import format_deadline
from models.note import Note, NoteStatus
from models.task import Task, TaskStatus
from ui.screens.dashboard import format_status

# "blue" (a base 16-color ANSI name) gets remapped to a purple accent by Textual's theme;
# dodger_blue2 is a fixed 256-palette color so it always renders as an actual blue
NOTE_STATUS_COLOR = {
    NoteStatus.WRITING: "dodger_blue2",
    NoteStatus.DONE: "pale_green3",
    NoteStatus.HIATUS: "dark_orange",
    NoteStatus.ABANDONED: "dark_red",
}
TASK_STATUS_COLOR = {
    TaskStatus.PENDING: "dark_orange",
    TaskStatus.IN_PROGRESS: "dodger_blue2",
    TaskStatus.COMPLETE: "pale_green3",
    TaskStatus.ABANDONED: "dark_red",
}

REST_WIDTH = 20  # fits "!5  ·  31-12-2026"
STATUS_WIDTH = 13  # fits "In progress" / "abandoned"


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


def _title_cell(item: Note | Task) -> Text:
    # "bold" goes on a span over just the title, not the Text object's base style,
    # so it doesn't bleed into the tags span appended after it
    text = Text(overflow="ellipsis", no_wrap=True)
    text.append(item.title, style="bold")
    if item.tags:
        text.append("  " + ", ".join(item.tags), style="medium_purple")
    return text


def _rest_cell(item: Note | Task) -> Text:
    if isinstance(item, Note):
        return Text("")
    rest = Text(f"!{item.importance}", style="dim")
    deadline = format_deadline(item.deadline)
    if deadline:
        rest.append(f"  ·  {deadline}", style="dim")
    return rest


def _status_cell(item: Note | Task) -> Text:
    if isinstance(item, Note):
        return Text(item.status.value, style=NOTE_STATUS_COLOR[item.status])
    return Text(format_status(item.status), style=TASK_STATUS_COLOR[item.status])


def _render_hit(hit: Hit) -> Table:
    # fixed-width right columns, not content-sized: each row is its own independent
    # Table.grid(), so a content-sized column lands at a different x per row (what made
    # the status column look staggered); a fixed width lines every row up identically
    grid = Table.grid(expand=True, padding=(0, 0, 0, 1))
    grid.add_column(ratio=1, overflow="ellipsis", no_wrap=True)
    grid.add_column(width=REST_WIDTH, justify="right", no_wrap=True, overflow="crop")
    grid.add_column(width=STATUS_WIDTH, justify="right", no_wrap=True, overflow="crop")
    grid.add_row(_title_cell(hit.item), _rest_cell(hit.item), _status_cell(hit.item))
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
            Input(placeholder="Search notes and tasks…", compact=True, id="search_query"),
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
