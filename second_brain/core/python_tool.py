"""Module 13 — Python Tool: task stats, simple calculations, chart generation."""
import sqlite3
import matplotlib.pyplot as plt
from core.config import DB_PATH


def task_completion_stats():
    """Returns (summary_text, path_to_chart_png)."""
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
    conn.close()
    pending = total - completed
    pct = (completed / total * 100) if total else 0

    chart_path = "data/task_stats.png"
    plt.figure(figsize=(4, 4))
    if total:
        plt.pie([completed, pending], labels=["Completed", "Pending"], autopct="%1.0f%%")
    else:
        plt.text(0.5, 0.5, "No tasks yet", ha="center")
    plt.title("Task Completion")
    plt.savefig(chart_path)
    plt.close()

    summary = f"{completed}/{total} tasks completed ({pct:.1f}%)" if total else "No tasks yet."
    return summary, chart_path


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """Compound Annual Growth Rate — handy for the finance-flavored demo prompts."""
    if start_value <= 0 or years <= 0:
        return 0.0
    return ((end_value / start_value) ** (1 / years) - 1) * 100
