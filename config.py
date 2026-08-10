import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("WPAPER_DATA_DIR", Path.home() / ".local/share/wpaper"))
NOTES_DIR = DATA_DIR / "notes"
DB_PATH = DATA_DIR / "wpaper.sqlite"


def resolve_editor() -> str:
    return os.environ.get("WPAPER_EDITOR") or os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nvim"
