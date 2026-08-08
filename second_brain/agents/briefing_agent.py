"""
Module 7 — Daily Briefing Generator
Module 9 — Parallel Processing (gather step runs conceptually in parallel;
           each source is independent and merged at the end)
Module 12 — Structured Output (Pydantic)
"""
from langchain_core.runnables import RunnableParallel, RunnableLambda
from core.llm import llm
from core.models import DailyBriefing
from agents.task_agent import list_pending_tasks
from agents.notes_agent import search_notes
from agents.research_agent import research

briefing_llm = llm.with_structured_output(DailyBriefing)


def _gather_all(_input=None) -> dict:
    return {
        "tasks": list_pending_tasks(),
        "notes": search_notes(""),
        "news": research("today's most important AI and technology news"),
        "emails": "Connect the Email Agent's inbox summary here for live email data.",
    }


parallel_gather = RunnableParallel(gather=RunnableLambda(_gather_all))


def generate_daily_briefing() -> DailyBriefing:
    gathered = _gather_all()
    prompt = f"""Create a structured daily briefing from this data.

Pending tasks: {gathered['tasks']}
Recent notes: {gathered['notes']}
Latest news: {gathered['news']}
Email summary: {gathered['emails']}"""
    return briefing_llm.invoke(prompt)
