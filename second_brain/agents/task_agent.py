"""Module 6 — Task Management Agent"""
import sqlite3
from datetime import datetime
from core.config import DB_PATH


def init_tasks_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      description TEXT, status TEXT, due_date TEXT, created_at TEXT)""")
    conn.commit()
    conn.close()


def add_task(description: str, due_date: str = "") -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO tasks (description, status, due_date, created_at) VALUES (?,?,?,?)",
                 (description, "pending", due_date, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return f"Task added: {description}"


def complete_task(description: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE tasks SET status='completed' WHERE description=?", (description,))
    conn.commit()
    conn.close()
    return f"Task marked complete: {description}"


def delete_task(description: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks WHERE description=?", (description,))
    conn.commit()
    conn.close()
    return f"Task deleted: {description}"


def list_pending_tasks() -> str:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT description, due_date FROM tasks WHERE status='pending'").fetchall()
    conn.close()
    if not rows:
        return "No pending tasks."
    return "\n".join(f"- {d} (due {due or 'no date'})" for d, due in rows)


def list_all_tasks():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, description, status, due_date FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def search_tasks(keyword: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT description, status FROM tasks WHERE description LIKE ?",
                        (f"%{keyword}%",)).fetchall()
    conn.close()
    return "\n".join(f"- {d} [{s}]" for d, s in rows) or "No matching tasks."


init_tasks_db()
