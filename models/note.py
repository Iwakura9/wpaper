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
    tags: list[str] | None =None
    # related_task_id: int | None =None

@dataclass
class Note:
    id: int
    title: str
    status: NoteStatus
    created_at: int
    updated_at: int
    content: str = ""
    tags: list[str] | None =None

# fluxo:
# modalscreen aparece pedindo NewNoteData: Titulo, Status e tags; futuramente task associada
# modalscreen -> create_note (notes.db)
# create_note recebe NewNoteData, adiciona ID e datas
# salva no BD e retorna Note com todas as informações
