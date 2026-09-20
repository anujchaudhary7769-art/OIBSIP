"""
db.py
-----
SQLite persistence layer for the advanced BMI calculator.

Keeps all database code in one place so advanced_bmi_gui.py only ever calls
these functions and never touches SQL directly. Every function catches
sqlite3.Error and re-raises it as a DBError with a friendly message, so the
GUI can show a message box instead of crashing on a locked/corrupt/missing
database file.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bmi_records.db")


class DBError(Exception):
    """Raised for any database read/write failure, with a user-friendly message."""


def _connect() -> sqlite3.Connection:
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as exc:
        raise DBError(f"Could not open the database file: {exc}") from exc


def init_db() -> None:
    """Create the records table if it doesn't already exist."""
    try:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    username  TEXT NOT NULL,
                    weight    REAL NOT NULL,
                    height    REAL NOT NULL,
                    bmi       REAL NOT NULL,
                    category  TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
    except sqlite3.Error as exc:
        raise DBError(f"Could not initialize the database: {exc}") from exc


def save_record(username: str, weight: float, height: float, bmi: float, category: str) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO records (username, weight, height, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, weight, height, bmi, category, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
    except sqlite3.Error as exc:
        raise DBError(f"Could not save the record: {exc}") from exc


def get_usernames() -> list[str]:
    """Distinct usernames that have at least one saved record, alphabetical."""
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT DISTINCT username FROM records ORDER BY username").fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error as exc:
        raise DBError(f"Could not read usernames: {exc}") from exc


def get_history(username: str) -> list[tuple[str, float]]:
    """Return [(recorded_at, bmi), ...] for `username`, oldest first."""
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT recorded_at, bmi FROM records WHERE username = ? ORDER BY recorded_at",
                (username,),
            ).fetchall()
        return rows
    except sqlite3.Error as exc:
        raise DBError(f"Could not read history for {username}: {exc}") from exc
