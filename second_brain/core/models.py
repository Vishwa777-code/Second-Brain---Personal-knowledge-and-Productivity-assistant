"""Module 12 — Structured Outputs"""
from pydantic import BaseModel, Field
from typing import List


class DailyBriefing(BaseModel):
    daily_summary: str = Field(description="One-paragraph overview of the day")
    important_emails: List[str]
    pending_tasks: List[str]
    knowledge_base_highlights: List[str]
    latest_research: str
    recommendations: List[str]
    next_actions: List[str]


class EmailDraft(BaseModel):
    recipient: str = Field(default="", description="Recipient email address or name if mentioned")
    subject: str = Field(description="Clear and concise email subject line")
    body: str = Field(description="Full professional body text of the email")
    tone: str = Field(default="professional", description="Overall tone of the email (e.g. professional, friendly, concise, persuasive)")
    key_points: List[str] = Field(default_factory=list, description="Key summary points addressed in the email")

