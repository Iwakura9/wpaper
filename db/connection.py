import sqlite3
from pathlib import Path

DATA_DIR = Path.home() / "Documents" / "wpaper"
DB_PATH = DATA_DIR / "wpaper.sqlite"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # pra poder acessar as colunas por nome
    connection.execute("PRAGMA foreign_keys = ON")

    return connection
