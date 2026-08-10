import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("WPAPER_DATA_DIR", Path.home() / ".local/share/wpaper"))
NOTES_DIR = DATA_DIR / "notes"
DB_PATH = DATA_DIR / "wpaper.sqlite"
