from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

import config
from db.notes import delete_note, list_notes
from db.stats import dashboard_stats
from db.tasks import create_task, delete_task, format_deadline, format_status, list_tasks, update_task
from models.note import Note, NoteStatus
from models.task import NewTaskData, Task, TaskStatus
from ui.screens.modals.confirm_modal import ConfirmModal
from ui.external_editor import open_note_in_editor
from ui.screens.modals.new_note_modal import NewNoteModal
from ui.screens.modals.search_modal import SearchModal
from ui.screens.modals.task_modal import TaskModal


def days_left(deadline: int | None) -> str:
    if deadline is None:
        return ""
    delta = datetime.fromtimestamp(deadline).date() - datetime.now().date()
    return str(delta.days)


class NoteCard(Static):
    can_focus = True

    BINDINGS = [
        ("enter", "open", "Open"),
        ("d", "delete", "Delete note"),
        ("e", "edit_external", "Edit in editor"),
    ]

    class Opened(Message):
        def __init__(self, note: Note) -> None:
            self.note = note
            super().__init__()

    class DeleteRequested(Message):
        def __init__(self, note: Note) -> None:
            self.note = note
            super().__init__()

    class EditExternalRequested(Message):
        def __init__(self, note: Note) -> None:
            self.note = note
            super().__init__()

    def __init__(self, note: Note):
        updated = datetime.fromtimestamp(note.updated_at).strftime("%d %b, %Y")
        lines = [note.title, f"{note.status.value} · {updated}"]
        super().__init__("\n".join(lines), classes=f"note_card status-{note.status.value}")
        self.note = note

    def action_open(self) -> None:
        self.post_message(self.Opened(self.note))

    def action_delete(self) -> None:
        self.post_message(self.DeleteRequested(self.note))

    def action_edit_external(self) -> None:
        self.post_message(self.EditExternalRequested(self.note))


class DashboardScreen(Screen):
    CSS_PATH = "dashboard.tcss"

    BINDINGS = [
        ("escape", "back", "Back"),
        ("v", "toggle_notes_view", "Toggle view"),
        ("n", "new_note", "New note"),
        ("t", "new_task", "New task"),
        ("d", "delete_task", "Delete task"),
        ("/", "global_search", "Search"),
        # The DataTable consumes the arrows itself, so these only ever fire on a focused
        # NoteCard, which is a Static and lets them through to the screen.
        Binding("up", "focus_card(0, -1)", show=False),
        Binding("down", "focus_card(0, 1)", show=False),
        Binding("left", "focus_card(-1, 0)", show=False),
        Binding("right", "focus_card(1, 0)", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.notes_view = config.load()["notes_view"]
        self.tasks_by_row: dict[str, Task] = {}

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Static(id="stats"),
                DataTable(id="tasks", cursor_type="row"),
                id="top_row",
            ),
            Vertical(id="note_board"),
            id="dashboard",
        )
        yield Footer(compact=True)

    def on_mount(self) -> None:
        self.query_one("#tasks", DataTable).add_columns(
            "Imp", "Title", "Status", "Days left", "Deadline"
        )

    async def on_screen_resume(self) -> None:
        await self.reload()

    async def reload(self) -> None:
        stats = dashboard_stats()
        by_status = stats["tasks_by_status"]
        self.query_one("#stats", Static).update(
            f"Completed this week: {stats['completed_this_week']}\n"
            f"Open tasks: {stats['open_tasks']}\n"
            f"Total notes: {stats['total_notes']}\n"
            "\n"
            f"Pending: {by_status.get('pending', 0)}\n"
            f"In progress: {by_status.get('in_progress', 0)}\n"
            f"Complete: {by_status.get('complete', 0)}\n"
            f"Abandoned: {by_status.get('abandoned', 0)}"
        )

        table = self.query_one("#tasks", DataTable)
        table.clear()
        self.tasks_by_row = {}
        open_tasks = [
            task
            for task in list_tasks()
            if task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        ]
        open_tasks.sort(key=lambda task: (task.deadline is None, task.deadline or 0, task.importance))
        for task in open_tasks:
            row_key = str(task.id)
            table.add_row(
                str(task.importance),
                task.title,
                format_status(task.status),
                days_left(task.deadline),
                format_deadline(task.deadline),
                key=row_key,
            )
            self.tasks_by_row[row_key] = task

        await self.rebuild_note_board()

    async def rebuild_note_board(self) -> None:
        board = self.query_one("#note_board", Vertical)
        await board.remove_children()
        board.set_classes("grid_view" if self.notes_view == "grid" else "kanban_view")

        notes = list_notes()

        def card(note: Note) -> NoteCard:
            return NoteCard(note)

        if self.notes_view == "grid":
            await board.mount_all(card(note) for note in notes)
        else:
            for status in NoteStatus:
                column_notes = [note for note in notes if note.status is status]
                column = Vertical(
                    Static(status.value.title(), classes="column_header"),
                    Vertical(*[card(note) for note in column_notes], classes="column_body"),
                    classes="column",
                )
                await board.mount(column)

    def note_card_cells(self) -> dict[tuple[int, int], NoteCard]:
        """Maps every note card to its (column, row) on the board."""
        board = self.query_one("#note_board", Vertical)
        if self.notes_view == "grid":
            # Cards are children of the grid in row-major order; the column count is the
            # tcss grid-size, read back so there is no constant to keep in sync.
            columns = board.styles.grid_size_columns or 4
            return {
                (index % columns, index // columns): card
                for index, card in enumerate(board.query(NoteCard))
            }
        return {
            (column_index, row): card
            for column_index, column in enumerate(board.query(".column"))
            for row, card in enumerate(column.query(NoteCard))
        }

    def action_focus_card(self, dcol: int, drow: int) -> None:
        card = self.focused
        if not isinstance(card, NoteCard):
            return

        cells = self.note_card_cells()
        origin = next((pos for pos, other in cells.items() if other is card), None)
        if origin is None:
            return
        col, row = origin

        if drow:
            target = cells.get((col, row + drow))
        else:
            # Columns are ragged, so a sideways move lands on the nearest card there.
            column = [pos for pos in cells if pos[0] == col + dcol]
            target = cells[min(column, key=lambda pos: abs(pos[1] - row))] if column else None

        if target is not None:
            target.focus()

    def on_note_card_opened(self, message: NoteCard.Opened) -> None:
        self.app.open_note(message.note)

    def on_note_card_delete_requested(self, message: NoteCard.DeleteRequested) -> None:
        note = message.note
        self.app.push_screen(
            ConfirmModal(f'Delete "{note.title}"?'),
            lambda confirmed: self.on_note_delete_confirmed(note.id, confirmed),
        )

    def on_note_delete_confirmed(self, note_id: int, confirmed: bool | None) -> None:
        if not confirmed:
            return
        delete_note(note_id)
        self.call_next(self.reload)

    def on_note_card_edit_external_requested(self, message: NoteCard.EditExternalRequested) -> None:
        if open_note_in_editor(self.app, message.note):
            self.call_next(self.reload)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        task = self.tasks_by_row.get(event.row_key.value)
        if task is None:
            return
        self.app.push_screen(TaskModal(task), lambda data: self.on_task_edited(task.id, data))

    def on_task_edited(self, task_id: int, data: NewTaskData | None) -> None:
        if data is None:
            return
        update_task(task_id, data)
        self.call_next(self.reload)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_global_search(self) -> None:
        self.app.push_screen(SearchModal(), self.app.open_hit)

    def action_toggle_notes_view(self) -> None:
        self.notes_view = "kanban" if self.notes_view == "grid" else "grid"
        config.save(notes_view=self.notes_view)
        self.call_next(self.rebuild_note_board)

    def action_new_note(self) -> None:
        self.app.push_screen(NewNoteModal(), self.open_writing_screen)

    def open_writing_screen(self, note: Note | None) -> None:
        if note is None:
            return
        self.app.open_note(note)

    def action_new_task(self) -> None:
        self.app.push_screen(TaskModal(), self.on_task_created)

    def on_task_created(self, data: NewTaskData | None) -> None:
        if data is None:
            return
        create_task(data)
        self.notify("Task created!")
        self.call_next(self.reload)

    # NoteCard owns its own "d" binding (deletes that note) and shadows this one while
    # focused; everywhere else "d" falls through to here and deletes the table's cursor row.
    def action_delete_task(self) -> None:
        table = self.query_one("#tasks", DataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        task = self.tasks_by_row.get(row_key.value)
        if task is None:
            return
        self.app.push_screen(
            ConfirmModal(f'Delete "{task.title}"?'),
            lambda confirmed: self.on_delete_confirmed(task.id, confirmed),
        )

    def on_delete_confirmed(self, task_id: int, confirmed: bool | None) -> None:
        if not confirmed:
            return
        delete_task(task_id)
        self.call_next(self.reload)
