"""
Module 10 — Coordinator Agent (Conditional Routing)
Module 8 — Sequential Workflow
"""

from core.llm import llm, get_text_content
from core.memory import save_message
from agents.knowledge_agent import search_knowledge_base
from agents.research_agent import research
from agents.notes_agent import search_notes, create_note
from agents.task_agent import list_pending_tasks, add_task
from agents.email_agent import draft_email, send_email
from agents.briefing_agent import generate_daily_briefing

CATEGORIES = [
    "notes",
    "tasks",
    "research",
    "email",
    "knowledge",
    "briefing",
    "general",
]

def classify_request(user_input: str) -> str:
    prompt = f"""Classify this request into exactly one category:
notes, tasks, research, email, knowledge, briefing, general

Request: "{user_input}"

Reply with only the category word, nothing else."""

    result = llm.invoke(prompt)
    content = get_text_content(result)
    category = content.strip().lower()

    return category if category in CATEGORIES else "general"

def coordinator(user_input: str) -> tuple[str, str]:
    """Returns (response_text, category_used)."""
    category = classify_request(user_input)
    save_message("user", user_input)

    if category == "notes":
        if any(w in user_input.lower() for w in ["save", "add", "create"]):
            response = create_note(title=user_input[:50], content=user_input)
        else:
            response = search_notes(user_input)

    elif category == "tasks":
        if any(w in user_input.lower() for w in ["add", "create", "prepare"]):
            response = add_task(user_input)
        else:
            response = list_pending_tasks()

    elif category == "research":
        response = research(user_input)

    elif category == "email":
        lower_input = user_input.lower()
        if any(w in lower_input for w in ["inbox", "summarize", "read", "check"]):
            from agents.email_agent import summarize_inbox
            response = summarize_inbox()
        elif any(w in lower_input for w in ["search", "find"]):
            from agents.email_agent import search_emails
            response = search_emails(user_input)
        else:
            response = draft_email(user_input)


    elif category == "knowledge":
        response = search_knowledge_base(user_input)

    elif category == "briefing":
        briefing = generate_daily_briefing()
        response = briefing.model_dump_json(indent=2)

    else:
        result = llm.invoke(user_input)
        response = get_text_content(result)

    response = str(response)
    save_message("assistant", response)

    return response, category
