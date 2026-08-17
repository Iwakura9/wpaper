import tomllib

import db.connection

# ponytail: fixed-template writer, real TOML writer when the config grows nesting
TEMPLATE = """\
# wpaper config

# Textual theme name (ctrl+p -> "theme" to browse). Saved automatically.
theme = {theme!r}

# Note board layout on the dashboard: "grid" or "kanban". Saved automatically.
notes_view = {notes_view!r}

# Alternative editor command, e.g. "nvim", "hx", "code -w".
# Empty falls back to nvim -> vim -> $EDITOR.
alt_editor = {alt_editor!r}

# true  = notes always open in alt_editor
# false = notes open in wpaper's editor; F3 still opens alt_editor
force_alt_editor = {force_alt_editor}
"""

DEFAULTS = {
    "theme": "textual-dark",
    "notes_view": "grid",
    "alt_editor": "",
    "force_alt_editor": False,
}


def config_path():
    return db.connection.DATA_DIR / "config.toml"


def load() -> dict:
    path = config_path()
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        data = {}

    config = dict(DEFAULTS)
    for key, default in DEFAULTS.items():
        value = data.get(key)
        if isinstance(value, type(default)):
            config[key] = value
    return config


def save(**changes) -> None:
    config = load() | changes
    config["force_alt_editor"] = "true" if config["force_alt_editor"] else "false"
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.format(**config), encoding="utf-8")


def demo() -> None:
    import tempfile
    from pathlib import Path

    old_data_dir = db.connection.DATA_DIR
    db.connection.DATA_DIR = Path(tempfile.mkdtemp())
    try:
        assert load() == DEFAULTS

        save(theme="gruvbox")
        assert load()["theme"] == "gruvbox"
        assert load()["notes_view"] == "grid"

        save(notes_view="kanban", alt_editor="hx", force_alt_editor=True)
        config = load()
        assert config["theme"] == "gruvbox"
        assert config["notes_view"] == "kanban"
        assert config["alt_editor"] == "hx"
        assert config["force_alt_editor"] is True

        config_path().write_text("theme = 42\nunknown_key = 1\nnotes_view = ", encoding="utf-8")
        assert load() == DEFAULTS

        config_path().unlink()
        assert load() == DEFAULTS

        print("config.py: ok")
    finally:
        db.connection.DATA_DIR = old_data_dir


if __name__ == "__main__":
    demo()
