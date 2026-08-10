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
    status: TaskStatus
    importance: int = 3
    description: str = ""
    deadline: int | None = None
    tags: list[str] | None = None

@dataclass
class Task:
    id: int
    title: str
    status: TaskStatus
    importance: int
    created_at: int
    updated_at: int
    description: str = ""
    deadline: int | None = None
    tags: list[str] | None = None
