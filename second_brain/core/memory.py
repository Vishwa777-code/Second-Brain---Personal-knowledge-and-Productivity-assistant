"""
Module 11 — Memory
Short-term  -> handled by Streamlit session_state in app.py
Persistent  -> conversations table (SQLite)
Long-term   -> user_profile key/value table (SQLite)
"""
import sqlite3
import os
from datetime import datetime
from core.config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_memory_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT, role TEXT, content TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS user_profile
                     (key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit()
    conn.close()


def save_message(role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO conversations (timestamp, role, content) VALUES (?,?,?)",
                 (datetime.now().isoformat(), role, content))
    conn.commit()
    conn.close()


def load_history(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return list(reversed(rows))


def remember(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO user_profile (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


def recall(key: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT value FROM user_profile WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None


def recall_all() -> dict:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT key, value FROM user_profile").fetchall()
    conn.close()
    return dict(rows)


init_memory_db()
