from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.widget import Widget

from db.stats import dashboard_stats


class StatsPanel(Widget):
    def compose(self) -> ComposeResult:
        stats = dashboard_stats()
        by_status = stats["tasks_by_status"]

        yield Vertical(
            Static("Stats", id="stats_title"),
            Static(f"Notes: {stats['notes_total']}"),
            Static(f"Tasks completed this week: {stats['tasks_completed_this_week']}"),
            Static(f"Tasks open: {stats['tasks_open']}"),
            Static(f"  pending: {by_status.get('pending', 0)}"),
            Static(f"  in progress: {by_status.get('in_progress', 0)}"),
            Static(f"  complete: {by_status.get('complete', 0)}"),
            Static(f"  abandoned: {by_status.get('abandoned', 0)}"),
            id="stats_panel",
        )
