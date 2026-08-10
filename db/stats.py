from datetime import datetime, timedelta

from db.connection import get_connection


def week_start_timestamp() -> int:
    now = datetime.now()
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(monday.timestamp())


def dashboard_stats() -> dict:
    with get_connection() as con:
        notes_total = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]

        tasks_completed_this_week = con.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'complete' AND updated_at >= ?",
            (week_start_timestamp(),),
        ).fetchone()[0]

        tasks_open = con.execute(
            "SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'in_progress')"
        ).fetchone()[0]

        status_rows = con.execute(
            "SELECT status, COUNT(*) AS count FROM tasks GROUP BY status"
        ).fetchall()

    return {
        "notes_total": notes_total,
        "tasks_completed_this_week": tasks_completed_this_week,
        "tasks_open": tasks_open,
        "tasks_by_status": {row["status"]: row["count"] for row in status_rows},
    }
