"""Module 5 — Notes Agent"""
import sqlite3
from datetime import datetime
from core.config import DB_PATH


def init_notes_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT, content TEXT, tags TEXT, created_at TEXT)""")
    conn.commit()
    conn.close()


def create_note(title: str, content: str, tags: str = "") -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO notes (title, content, tags, created_at) VALUES (?,?,?,?)",
                 (title, content, tags, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return f"Note '{title}' saved."


def list_notes():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, title, content, tags, created_at FROM notes ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def search_notes(keyword: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT title, content FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?",
        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
    ).fetchall()
    conn.close()
    return "\n".join(f"- {t}: {c}" for t, c in rows) or "No matching notes found."


def update_note(title: str, new_content: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE notes SET content=? WHERE title=?", (new_content, title))
    conn.commit()
    conn.close()
    return f"Note '{title}' updated."


def delete_note(title: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM notes WHERE title=?", (title,))
    conn.commit()
    conn.close()
    return f"Note '{title}' deleted."


init_notes_db()
