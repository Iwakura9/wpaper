from datetime import datetime

from models.task import NewTaskData, Task, TaskStatus
from db.connection import get_connection, normalize_tags, now_timestamp

DEADLINE_FORMAT = "%d-%m-%Y"

def parse_deadline(text: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    return int(datetime.strptime(text, DEADLINE_FORMAT).timestamp())

def format_deadline(deadline: int | None) -> str:
    if deadline is None:
        return ""
    return datetime.fromtimestamp(deadline).strftime(DEADLINE_FORMAT)

def format_status(status: TaskStatus) -> str:
    return status.value.replace("_", " ").capitalize()

def _replace_tags(con, task_id: int, tags: list[str]) -> None:
    con.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
    for tag in tags:
        con.execute(
            "INSERT OR IGNORE INTO task_tags (task_id, tag) VALUES (?, ?)",
            (task_id, tag),
        )

def create_task(data: NewTaskData) -> Task:
    now = now_timestamp()
    completed_at = now if data.status is TaskStatus.COMPLETE else None

    with get_connection() as con:
        cursor = con.execute("""
            INSERT INTO tasks (
                title,
                importance,
                status,
                description,
                deadline,
                created_at,
                completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.title,
                data.importance,
                data.status.value,
                data.description,
                data.deadline,
                now,
                completed_at,
            ),
        )

        task_id = cursor.lastrowid

        if task_id is None:
            raise RuntimeError("Failed to create task")

        tags = normalize_tags(data.tags)
        _replace_tags(con, task_id, tags)

        return Task(
            id=task_id,
            title=data.title,
            importance=data.importance,
            status=data.status,
            description=data.description,
            deadline=data.deadline,
            created_at=now,
            completed_at=completed_at,
            tags=tags,
        )


def update_task(task_id: int, data: NewTaskData) -> None:
    with get_connection() as con:
        con.execute(
            """
            UPDATE tasks
            SET title = ?, importance = ?, status = ?, description = ?, deadline = ?,
                completed_at = CASE WHEN ? = 'complete' THEN COALESCE(completed_at, ?) ELSE NULL END
            WHERE id = ?
            """,
            (
                data.title,
                data.importance,
                data.status.value,
                data.description,
                data.deadline,
                data.status.value,
                now_timestamp(),
                task_id,
            ),
        )

        _replace_tags(con, task_id, normalize_tags(data.tags))


def delete_task(task_id: int) -> None:
    with get_connection() as con:
        con.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

def list_task_tags() -> list[str]:
    with get_connection() as con:
        rows = con.execute("SELECT DISTINCT tag FROM task_tags ORDER BY tag").fetchall()
    return [row["tag"] for row in rows]

def list_tasks() -> list[Task]:
    with get_connection() as con:
        rows = con.execute("""
            SELECT
                id,
                title,
                importance,
                status,
                description,
                deadline,
                created_at,
                completed_at
            FROM tasks
            ORDER BY
                status IN ('complete', 'abandoned'),
                importance ASC,
                deadline IS NULL,
                deadline ASC,
                id DESC
        """).fetchall()

        task_ids = [row["id"] for row in rows]
        tags_by_task: dict[int, list[str]] = {}
        if task_ids:
            placeholders = ",".join("?" * len(task_ids))
            tag_rows = con.execute(
                f"SELECT task_id, tag FROM task_tags WHERE task_id IN ({placeholders}) ORDER BY tag",
                task_ids,
            ).fetchall()
            for tag_row in tag_rows:
                tags_by_task.setdefault(tag_row["task_id"], []).append(tag_row["tag"])

    return [
        Task(
            id=row["id"],
            title=row["title"],
            importance=row["importance"],
            status=TaskStatus(row["status"]),
            description=row["description"],
            deadline=row["deadline"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            tags=tags_by_task.get(row["id"], []),
        )
        for row in rows
    ]
