import os
import shlex
import shutil
import subprocess

from textual.app import App, SuspendNotSupported

import config
from db.notes import read_note_content, update_note_content
from db.notes import get_notes_dir
from models.note import Note


def editor_command() -> list[str] | None:
    alt_editor = config.load()["alt_editor"]
    parts = shlex.split(alt_editor)
    if parts and shutil.which(parts[0]):
        return parts

    for name in ("nvim", "vim"):
        if shutil.which(name):
            return [name]

    parts = shlex.split(os.environ.get("EDITOR", ""))
    if parts and shutil.which(parts[0]):
        return parts

    return None


def open_note_in_editor(app: App, note: Note) -> bool:
    command = editor_command()
    if command is None:
        app.notify("No editor found (tried nvim, vim, $EDITOR)", severity="error")
        return False

    path = get_notes_dir() / note.file_path
    try:
        with app.suspend():
            subprocess.call(command + [str(path)])
    except SuspendNotSupported:
        app.notify("Terminal does not support suspending for an external editor", severity="error")
        return False

    update_note_content(note.id, read_note_content(note))
    return True
