# wpaper TODO

Single source of pending work. Update this file, not the CLAUDE.md "Roadmap status" section,
when something here gets done or something new turns up.

## Bugs

- `db/connection.py:25` — `get_connection()` never closes the connection it opens; `with con`
  only commits/rolls back, it doesn't call `close()`. Leaks a handle per call.
- `db/notes.py` (`update_note_content`, `delete_note`) — both assume the row still exists
  (`row["file_path"]` on a `None` row raises `TypeError`) if the note was deleted between the
  read and the write. Narrow race, but the same shared-connection pattern as everything else in
  `db/`, so worth a `if row is None: return` guard once touched again.
- `db/search.py:64` — `sync_index()` runs on the UI thread. Marked `# ponytail:` already;
  measured ~85ms at 2000 notes, 15 notes today. Move to `@work` if it starts being felt.
- `db/search.py:77` — the note re-index stamp has 1-second resolution, so two status-only edits
  inside the same second can share a stamp and the second edit's search hit goes stale until the
  next touch. Marked `# ponytail:` already; self-corrects on the next edit or mtime change.

## Small adjustments

- DB stores `"done"` for what the design doc calls "Complete" (`models/note.py`'s `NoteStatus`).
  The kanban column header reads "Done" — fine as is, but flagging the naming mismatch in case it
  ever needs to match the spec's wording exactly.
- `DashboardScreen.show_all_tasks` (the `a` toggle added to reveal complete/abandoned tasks) is
  session-only, not persisted to `config.toml`. Add it there (mirroring `notes_view`) if resetting
  on every launch turns out to be annoying.
- `/` (global search) has no binding on `WritingScreen` — deliberate (see `wpaper.py`'s comment on
  `open_hit`), but revisit if searching mid-write turns out to be wanted.
- No in-app editor for `alt_editor`/`force_alt_editor` — `config.toml` is hand-edited only.
- `HomeScreen` shows shortcuts and a logo but no glance at recent notes/tasks; everything requires
  going to the dashboard first.

## Big adjustments (each deserves its own session)

1. **Real-time markdown preview** — `local/planer_ideia.md` lists this under "o que tem que ter"
   (must-have) and it was never built. Likely shape: split pane in `WritingScreen`, `TextArea` on
   the left and Textual's built-in `Markdown` widget on the right, toggled on a key — no new
   dependency, `textual==8.2.7` already ships `Markdown`. Decided against for now; `F3`/external
   nvim covers serious markdown editing.
2. ~~**Configurable data directory**~~ — done: `WPAPER_DATA_DIR` env var overrides
   `~/Documents/wpaper` (`db/connection.py:_data_dir()`, expanduser'd, read once at import time).
   No XDG base-dir fallback chain — one env var was the actual ask.
3. **Cross-device sync** — the original spec's "syncthing" ask. Now that (2) is done, this is
   "point `WPAPER_DATA_DIR` at a folder syncthing watches," not new code in this repo — nothing
   left to build unless something concrete comes up (e.g. conflict handling if two devices write
   at once, which syncthing itself doesn't resolve for a live sqlite file).
4. **A real tag dropdown** — `local/CONTEXT.md` asks for a dropdown of existing tags; what shipped
   is inline ghost text (`ui/screens/modals/tag_suggester.py`, `TagSuggester`). Upgrade path: an
   `OptionList` overlaid under the `Input`, or the `textual-autocomplete` package.
5. **Editing the note↔task link from the task side** — a task can have many linked notes, but only
   the note side writes `linked_task_id`; `TaskModal` shows linked notes read-only on purpose
   (skipped deliberately — see CLAUDE.md's "Not yet built"). Opening this up means a
   `SelectionList` in `TaskModal` plus a second write path for the same column.
6. **A writing screen for tasks** — the spec says "a mesma coisa para os dois tipos de página"
   (same thing for both page types); tasks still edit their description in `TaskModal`'s small
   `TextArea`. Decided to keep the modal for now.
7. **A real schema migration system** — `db/schema.py` has exactly two guarded `ALTER TABLE`
   calls (`notes.linked_task_id`, `tasks.completed_at`), marked `# ponytail: ad-hoc migration,
   real migration system when a destructive change lands`. Fine while every change only adds
   tables/columns; the first non-additive change needs a real one.
