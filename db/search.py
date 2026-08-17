from dataclasses import dataclass

from db.connection import get_connection
from db.notes import get_notes_dir, list_notes, read_note_content
from db.tasks import list_tasks
from models.note import Note
from models.task import Task

SNIPPET_START = "\x02"
SNIPPET_END = "\x03"

FILTER_PREFIXES = ("is", "tag", "status")


@dataclass
class Hit:
    item: Note | Task
    snippet: str
    rank: float


def _fts_term(text: str) -> str:
    # quoted prefix match: neutralizes fts5 syntax chars (NEAR, -, *, ...) as literal text
    return '"' + text.replace('"', '""') + '"*'


def _parse(query: str) -> tuple[list[str], dict[str, str]]:
    terms: list[str] = []
    filters: dict[str, str] = {}
    for token in query.split():
        prefix, sep, value = token.partition(":")
        if sep and value and prefix.lower() in FILTER_PREFIXES:
            filters[prefix.lower()] = value.lower()
        else:
            terms.append(token)
    return terms, filters


def _match_expr(terms: list[str], filters: dict[str, str]) -> str | None:
    clauses = []
    if terms:
        free_text = " AND ".join(_fts_term(term) for term in terms)
        clauses.append(f"{{title body tags}} : ({free_text})")
    if "tag" in filters:
        clauses.append(f"tags : {_fts_term(filters['tag'])}")
    if "status" in filters:
        clauses.append(f"status : {_fts_term(filters['status'])}")
    return " AND ".join(clauses) if clauses else None


def sync_index() -> None:
    with get_connection() as con:
        # tasks: small, no on-disk body, just rebuild the whole thing
        con.execute("DELETE FROM task_index")
        con.execute("""
            INSERT INTO task_index (rowid, title, body, tags, status)
            SELECT t.id, t.title, t.description, COALESCE(GROUP_CONCAT(tt.tag, ' '), ''), t.status
            FROM tasks t
            LEFT JOIN task_tags tt ON tt.task_id = t.id
            GROUP BY t.id
        """)

        # notes: body lives in a .md file, so reindex only what changed since last sync
        # ponytail: sync runs on the UI thread; move to @work if it starts costing enough
        # notes to be felt (measured ~85ms rebuild at 2000 notes, 15 notes today)
        existing_stamps = {
            row["rowid"]: row["stamp"] for row in con.execute("SELECT rowid, stamp FROM note_index")
        }
        notes_dir = get_notes_dir()
        seen_ids = []
        for note in list_notes():
            seen_ids.append(note.id)
            try:
                mtime_ns = (notes_dir / note.file_path).stat().st_mtime_ns
            except OSError:
                mtime_ns = 0
            # ponytail: updated_at has 1s resolution, so two status-only edits in the same
            # second could share a stamp; the next edit (or mtime change) self-corrects it
            stamp = f"{note.file_path}|{note.updated_at}|{mtime_ns}"
            if existing_stamps.get(note.id) == stamp:
                continue
            con.execute("DELETE FROM note_index WHERE rowid = ?", (note.id,))
            con.execute(
                "INSERT INTO note_index (rowid, title, body, tags, status, stamp) VALUES (?, ?, ?, ?, ?, ?)",
                (note.id, note.title, read_note_content(note), " ".join(note.tags or []), note.status.value, stamp),
            )

        if seen_ids:
            placeholders = ",".join("?" * len(seen_ids))
            con.execute(f"DELETE FROM note_index WHERE rowid NOT IN ({placeholders})", seen_ids)
        else:
            con.execute("DELETE FROM note_index")


def _query_index(table: str, expr: str, limit: int) -> list[tuple[int, float, str]]:
    with get_connection() as con:
        rows = con.execute(
            f"SELECT rowid, bm25({table}) AS rank, snippet({table}, -1, ?, ?, '…', 12) AS snip "
            f"FROM {table} WHERE {table} MATCH ? ORDER BY rank LIMIT ?",
            (SNIPPET_START, SNIPPET_END, expr, limit),
        ).fetchall()
    return [(row["rowid"], row["rank"], row["snip"]) for row in rows]


def search(query: str, limit: int = 50) -> list[Hit]:
    terms, filters = _parse(query)
    expr = _match_expr(terms, filters)
    want = filters.get("is")

    if expr is None:
        hits: list[Hit] = []
        if want != "task":
            hits += [Hit(item=note, snippet="", rank=0.0) for note in list_notes()[:limit]]
        if want != "note":
            hits += [Hit(item=task, snippet="", rank=0.0) for task in list_tasks()[:limit]]
        return hits[:limit]

    hits = []
    if want != "task":
        notes_by_id = {note.id: note for note in list_notes()}
        for rowid, rank, snip in _query_index("note_index", expr, limit):
            note = notes_by_id.get(rowid)
            if note is not None:
                hits.append(Hit(item=note, snippet=snip, rank=rank))
    if want != "note":
        tasks_by_id = {task.id: task for task in list_tasks()}
        for rowid, rank, snip in _query_index("task_index", expr, limit):
            task = tasks_by_id.get(rowid)
            if task is not None:
                hits.append(Hit(item=task, snippet=snip, rank=rank))

    hits.sort(key=lambda hit: hit.rank)
    return hits[:limit]
