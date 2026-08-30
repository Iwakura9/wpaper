import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / "Documents" / "wpaper"
DB_PATH = DATA_DIR / "wpaper.sqlite"


def now_timestamp() -> int:
    # função pra retornar data e horário em segundos
    return int(datetime.now().timestamp())


def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    normalized = []
    for tag in tags:
        clean = tag.strip().lower()
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # pra poder acessar as colunas por nome
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:  # commits on success, rolls back on exception
            yield connection
    finally:
        connection.close()
