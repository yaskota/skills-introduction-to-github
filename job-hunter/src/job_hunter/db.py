"""SQLite storage for discovered jobs, application status and email replies.
Keeps runs idempotent (no duplicate matches/applications across days) and
gives the report generator something to summarize."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    dedupe_key TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    url TEXT,
    score REAL,
    matched_skills TEXT,
    status TEXT NOT NULL DEFAULT 'new',  -- new | applied | ignored
    first_seen TEXT NOT NULL,
    applied_at TEXT
);

CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_dedupe_key TEXT,
    from_address TEXT,
    subject TEXT,
    received_at TEXT,
    gmail_message_id TEXT UNIQUE,
    detected_at TEXT NOT NULL
);
"""


@contextmanager
def connect(db_path: str = "job_hunter.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_job(conn, dedupe_key, source, title, company, location, url, score, matched_skills):
    existing = conn.execute(
        "SELECT dedupe_key FROM jobs WHERE dedupe_key = ?", (dedupe_key,)
    ).fetchone()
    if existing:
        return False  # already known, not a new match today

    conn.execute(
        """INSERT INTO jobs
           (dedupe_key, source, title, company, location, url, score,
            matched_skills, status, first_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)""",
        (dedupe_key, source, title, company, location, url, score,
         ",".join(matched_skills), now()),
    )
    return True


def mark_applied(conn, dedupe_key: str):
    conn.execute(
        "UPDATE jobs SET status = 'applied', applied_at = ? WHERE dedupe_key = ?",
        (now(), dedupe_key),
    )


def record_reply(conn, job_dedupe_key, from_address, subject, received_at, gmail_message_id):
    try:
        conn.execute(
            """INSERT INTO replies
               (job_dedupe_key, from_address, subject, received_at,
                gmail_message_id, detected_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (job_dedupe_key, from_address, subject, received_at, gmail_message_id, now()),
        )
        return True
    except sqlite3.IntegrityError:
        return False  # already recorded this email


def counts_since(conn, since_iso: str) -> dict:
    new_matches = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE first_seen >= ?", (since_iso,)
    ).fetchone()[0]
    applied = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE applied_at >= ?", (since_iso,)
    ).fetchone()[0]
    replies = conn.execute(
        "SELECT COUNT(*) FROM replies WHERE detected_at >= ?", (since_iso,)
    ).fetchone()[0]
    total_applied = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'applied'"
    ).fetchone()[0]
    return {
        "new_matches": new_matches,
        "applied_today": applied,
        "replies_today": replies,
        "total_applied": total_applied,
    }
