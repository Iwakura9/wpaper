from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class NoteStatus(Enum):
    WRITING = "writing"
    DONE = "done"
    HIATUS = "hiatus"
    ABANDONED = "abandoned"

@dataclass
class NewNoteData:
    title: str
    status: NoteStatus
    created_at: str
    updated_at: datetime
    content: str = ""
    tags: list[str] | None = None
    # related_task_id: int | None =None
