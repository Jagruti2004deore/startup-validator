import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime

from app.config import DB_PATH


@contextmanager
def get_conn():
    """Open the database, and always save and close it afterwards."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def init_db() -> None:
    """Create the tables if they do not exist yet. Safe to run many times."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            idea_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            verdict TEXT,
            evidence_score INTEGER,
            report_md TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
            run_id TEXT NOT NULL,
            source_no INTEGER NOT NULL,
            url TEXT,
            title TEXT,
            content TEXT,
            PRIMARY KEY (run_id, source_no)
        );
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            text TEXT NOT NULL,
            category TEXT,
            source_nos TEXT,
            status TEXT NOT NULL,
            drop_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS run_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            time TEXT NOT NULL,
            node TEXT,
            message TEXT
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            pinecone_id TEXT,
            created_at TEXT NOT NULL
        );
        """)


# ---------- runs ----------
def create_run(idea_text: str) -> str:
    run_id = uuid.uuid4().hex[:8]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, idea_text, status, created_at) VALUES (?, ?, 'running', ?)",
            (run_id, idea_text, _now()),
        )
    return run_id


def update_run(run_id: str, **fields) -> None:
    allowed = {"status", "verdict", "evidence_score", "report_md"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with get_conn() as conn:
        conn.execute(f"UPDATE runs SET {set_clause} WHERE id = ?", (*fields.values(), run_id))


def get_run(run_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return dict(row) if row else None


def list_runs(limit: int = 20) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, idea_text, status, verdict, evidence_score, created_at "
            "FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- live events (power the live steps in the UI) ----------
def add_event(run_id: str, node: str, message: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO run_events (run_id, time, node, message) VALUES (?, ?, ?, ?)",
            (run_id, _now(), node, message),
        )


def get_events(run_id: str, after_id: int = 0) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM run_events WHERE run_id = ? AND id > ? ORDER BY id",
            (run_id, after_id),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- sources ----------
def save_sources(run_id: str, sources: list) -> None:
    """Replace this run's sources. Source number = position in the list + 1."""
    with get_conn() as conn:
        conn.execute("DELETE FROM sources WHERE run_id = ?", (run_id,))
        for i, s in enumerate(sources, start=1):
            conn.execute(
                "INSERT INTO sources (run_id, source_no, url, title, content) VALUES (?, ?, ?, ?, ?)",
                (run_id, i, s.get("url"), s.get("title"), s.get("content")),
            )


def get_sources(run_id: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sources WHERE run_id = ? ORDER BY source_no", (run_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- claims ----------
def save_claims(run_id: str, verified: list, dropped: list) -> None:
    """Replace this run's claims. Dropped claims keep the reason they failed."""
    with get_conn() as conn:
        conn.execute("DELETE FROM claims WHERE run_id = ?", (run_id,))
        for status, items in (("verified", verified), ("dropped", dropped)):
            for c in items:
                conn.execute(
                    "INSERT INTO claims (run_id, text, category, source_nos, status, drop_reason) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (run_id, c["text"], c.get("category"),
                     json.dumps(c.get("source_ids", [])), status, c.get("reason")),
                )


def get_claims(run_id: str) -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM claims WHERE run_id = ?", (run_id,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["source_nos"] = json.loads(d["source_nos"] or "[]")
        result.append(d)
    return result


# ---------- founder notes ----------
def add_note(text: str, pinecone_id: str = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO notes (text, pinecone_id, created_at) VALUES (?, ?, ?)",
            (text, pinecone_id, _now()),
        )
        return cur.lastrowid


def set_note_pinecone_id(note_id: int, pinecone_id: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE notes SET pinecone_id = ? WHERE id = ?", (pinecone_id, note_id))


def list_notes() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]