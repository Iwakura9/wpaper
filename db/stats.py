from datetime import datetime, timedelta

from db.connection import get_connection


def week_start_timestamp() -> int:
    now = datetime.now()
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int(monday.timestamp())


def dashboard_stats() -> dict:
    with get_connection() as con:
        completed_this_week = con.execute(
            "SELECT COUNT(*) FROM tasks WHERE completed_at >= ?",
            (week_start_timestamp(),),
        ).fetchone()[0]

        open_tasks = con.execute(
            "SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'in_progress')"
        ).fetchone()[0]

        total_notes = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]

        tasks_by_status = {
            row["status"]: row["count"]
            for row in con.execute(
                "SELECT status, COUNT(*) AS count FROM tasks GROUP BY status"
            )
        }

    return {
        "completed_this_week": completed_this_week,
        "open_tasks": open_tasks,
        "total_notes": total_notes,
        "tasks_by_status": tasks_by_status,
    }
