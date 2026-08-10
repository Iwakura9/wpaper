from datetime import datetime

from models.task import NewTaskData, Task, TaskStatus
from db.connection import get_connection


def now_timestamp() -> int:
    return int(datetime.now().timestamp())


def create_task(data: NewTaskData) -> Task:
    now = now_timestamp()

    with get_connection() as con:
        cursor = con.execute("""
            INSERT INTO tasks (
                title,
                description,
                status,
                importance,
                deadline,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.title,
                data.description,
                data.status.value,
                data.importance,
                data.deadline,
                now,
                now,
            ),
        )

        task_id = cursor.lastrowid

        if task_id is None:
            raise RuntimeError("Failed to create task")

    return Task(
        id=task_id,
        title=data.title,
        status=data.status,
        importance=data.importance,
        description=data.description,
        deadline=data.deadline,
        created_at=now,
        updated_at=now,
        tags=data.tags,
    )


def update_task(task_id: int, **fields) -> None:
    if not fields:
        return

    fields["updated_at"] = now_timestamp()
    columns = ", ".join(f"{column} = ?" for column in fields)

    with get_connection() as con:
        con.execute(
            f"UPDATE tasks SET {columns} WHERE id = ?",
            (*fields.values(), task_id),
        )


def list_tasks() -> list[Task]:
    with get_connection() as con:
        rows = con.execute("""
            SELECT
                id,
                title,
                description,
                status,
                importance,
                deadline,
                created_at,
                updated_at
            FROM tasks
            ORDER BY deadline IS NULL, deadline ASC, importance ASC
        """).fetchall()

    return [
        Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
            importance=row["importance"],
            deadline=row["deadline"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=None,
        )
        for row in rows
    ]
