import sqlite3
from pathlib import Path

DB_PATH = Path("data/library.db")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                gender TEXT NOT NULL,
                total_pages INTEGER NOT NULL,
                voice TEXT NOT NULL,
                last_page INTEGER DEFAULT 0,
                last_position REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_book(book_id: str, title: str, author: str, gender: str, total_pages: int, voice: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO books (book_id, title, author, gender, total_pages, voice, last_page, last_position, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0.0, CURRENT_TIMESTAMP)
            """,
            (book_id, title, author, gender, total_pages, voice),
        )


def list_books() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM books ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def get_book(book_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)).fetchone()
        return dict(row) if row else None


def update_progress(book_id: str, last_page: int, last_position: float = 0.0, voice: str | None = None) -> None:
    with get_conn() as conn:
        if voice:
            conn.execute(
                """
                UPDATE books
                SET last_page = ?, last_position = ?, voice = ?, updated_at = CURRENT_TIMESTAMP
                WHERE book_id = ?
                """,
                (last_page, last_position, voice, book_id),
            )
        else:
            conn.execute(
                """
                UPDATE books
                SET last_page = ?, last_position = ?, updated_at = CURRENT_TIMESTAMP
                WHERE book_id = ?
                """,
                (last_page, last_position, book_id),
            )


def delete_book(book_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
