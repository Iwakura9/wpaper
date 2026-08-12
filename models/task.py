from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ABANDONED = "abandoned"

@dataclass
class NewTaskData:
    title: str
    importance: int  # 1..5, 1 is the most important
    status: TaskStatus
    description: str = ""
    deadline: int | None = None
    tags: list[str] | None = None

@dataclass
class Task:
    id: int
    title: str
    importance: int
    status: TaskStatus
    created_at: int
    description: str = ""
    deadline: int | None = None
    tags: list[str] | None = None
    completed_at: int | None = None
