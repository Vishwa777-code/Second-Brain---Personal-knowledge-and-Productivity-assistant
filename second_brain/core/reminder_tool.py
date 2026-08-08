"""Optional stretch — basic Calendar Reminder Tool (no external calendar API needed)."""
import sqlite3
from core.config import DB_PATH


def init_reminders_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS reminders
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      text TEXT, remind_at TEXT)""")
    conn.commit()
    conn.close()


def add_reminder(text: str, remind_at: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO reminders (text, remind_at) VALUES (?,?)", (text, remind_at))
    conn.commit()
    conn.close()
    return f"Reminder set: {text} at {remind_at}"


def list_reminders():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT text, remind_at FROM reminders ORDER BY remind_at").fetchall()
    conn.close()
    return rows


init_reminders_db()
