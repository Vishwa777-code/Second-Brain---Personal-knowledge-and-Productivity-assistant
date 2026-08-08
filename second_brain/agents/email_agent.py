"""
Module 4 — Email Agent (Enhanced)

Supports:
- Structured AI Email Drafting (recipient, subject, body, tone, key points)
- SQLite Database Persistence for Drafts & Sent Emails History
- SMTP Sending (Gmail App Password) with status logging
- IMAP Inbox Reading (with realistic mock fallback for demo mode)
- AI Inbox Summarization & Email Search
"""
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from core.config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, DB_PATH
from core.llm import llm, get_text_content
from core.models import EmailDraft


def init_email_db():
    """Initialize SQLite database for emails history and drafts."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT,
            subject TEXT,
            body TEXT,
            status TEXT, -- 'draft', 'sent', 'failed'
            created_at TEXT,
            sent_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_email_db()


def generate_email_draft(instruction: str) -> EmailDraft:
    """Generate a structured EmailDraft object from a natural language prompt."""
    try:
        draft_llm = llm.with_structured_output(EmailDraft)
        prompt = f"""Generate a complete structured email draft based on this instruction:
"{instruction}"

Provide a recipient (if inferable or leave blank), a clear subject line, body text, overall tone, and key points."""
        res = draft_llm.invoke(prompt)
        if res and hasattr(res, "subject") and res.subject:
            return res
    except Exception:
        pass

    # Fallback plain LLM invocation if structured output fails
    prompt = f"""Write a professional email based on this instruction: "{instruction}"
Format your response as:
Subject: <subject line>
Recipient: <email address if mentioned, else leave blank>
Tone: <tone>
Body:
<email body>"""
    raw = get_text_content(llm.invoke(prompt))
    lines = raw.split("\n")
    subject = "Draft Email"
    recipient = ""
    tone = "professional"
    body_lines = []
    is_body = False

    for line in lines:
        if line.startswith("Subject:"):
            subject = line.replace("Subject:", "").strip()
        elif line.startswith("Recipient:"):
            recipient = line.replace("Recipient:", "").strip()
        elif line.startswith("Tone:"):
            tone = line.replace("Tone:", "").strip()
        elif line.startswith("Body:"):
            is_body = True
        elif is_body:
            body_lines.append(line)

    body = "\n".join(body_lines).strip() or raw
    return EmailDraft(
        recipient=recipient,
        subject=subject,
        body=body,
        tone=tone,
        key_points=[instruction[:60]]
    )


def draft_email(instruction: str) -> str:
    """Natural language entry point for coordinator returning string summary and saving draft."""
    draft = generate_email_draft(instruction)
    email_id = save_email_draft(draft.recipient, draft.subject, draft.body)
    recip_str = f" to {draft.recipient}" if draft.recipient else ""
    return f"📝 Email Draft Created (ID: {email_id}){recip_str}\nSubject: {draft.subject}\n\n{draft.body}"


def save_email_draft(recipient: str, subject: str, body: str) -> int:
    """Save an email draft to SQLite DB and return draft ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emails (recipient, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (recipient, subject, body, "draft", datetime.now().isoformat())
    )
    email_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return email_id


def list_email_drafts() -> List[Tuple[int, str, str, str, str]]:
    """Return list of drafts: [(id, recipient, subject, body, created_at), ...]"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, recipient, subject, body, created_at FROM emails WHERE status='draft' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows


def list_sent_emails() -> List[Tuple[int, str, str, str, str]]:
    """Return list of sent emails: [(id, recipient, subject, body, sent_at), ...]"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, recipient, subject, body, sent_at FROM emails WHERE status='sent' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows


def delete_email(email_id: int) -> str:
    """Delete an email entry from SQLite DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM emails WHERE id=?", (email_id,))
    conn.commit()
    conn.close()
    return f"Email #{email_id} deleted."


def is_valid_gmail_config() -> bool:
    """Check if real Gmail credentials (not placeholder) are configured in .env."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False
    if "you@gmail.com" in GMAIL_ADDRESS.lower() or "xxxx" in GMAIL_APP_PASSWORD.lower():
        return False
    return True


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail SMTP if credentials exist; otherwise save as draft/simulated."""
    if not to:
        return "Recipient email address is required to send."

    now_iso = datetime.now().isoformat()
    if not is_valid_gmail_config():
        # Save to DB as draft for offline demo mode
        email_id = save_email_draft(to, subject, body)
        return (
            f"ℹ️ Demo Mode: Real Gmail credentials not configured in .env. Draft saved to database (ID #{email_id}).\n\n"
            f"To send live emails:\n"
            f"1. Enable 2-Step Verification at https://myaccount.google.com/security\n"
            f"2. Create a 16-character App Password at https://myaccount.google.com/apppasswords\n"
            f"3. Update .env with GMAIL_ADDRESS and GMAIL_APP_PASSWORD."
        )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to

    conn = sqlite3.connect(DB_PATH)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to, msg.as_string())

        conn.execute(
            "INSERT INTO emails (recipient, subject, body, status, created_at, sent_at) VALUES (?, ?, ?, ?, ?, ?)",
            (to, subject, body, "sent", now_iso, now_iso)
        )
        conn.commit()
        conn.close()
        return f"✅ Email successfully sent to {to} via SMTP!"
    except smtplib.SMTPAuthenticationError:
        conn.execute(
            "INSERT INTO emails (recipient, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (to, subject, body, "failed", now_iso)
        )
        conn.commit()
        conn.close()
        return (
            "🔑 Gmail Authentication Error (535 Bad Credentials):\n\n"
            "• Gmail requires a 16-character 'App Password' (not your standard Gmail password).\n"
            "• Make sure 2-Step Verification is enabled on your Google Account.\n"
            "• Generate an App Password at: https://myaccount.google.com/apppasswords\n"
            "• Update .env with your real Gmail address and 16-character App Password."
        )
    except Exception as e:
        conn.execute(
            "INSERT INTO emails (recipient, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (to, subject, body, "failed", now_iso)
        )
        conn.commit()
        conn.close()
        return f"❌ Failed to send email via SMTP: {e}"


def send_email_by_id(email_id: int, to: str = "") -> str:
    """Send an existing draft by its DB ID."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT recipient, subject, body FROM emails WHERE id=?", (email_id,)).fetchone()
    conn.close()
    if not row:
        return f"Email #{email_id} not found."
    recip = to or row[0]
    if not recip:
        return "Please specify a recipient email address."

    result = send_email(recip, row[1], row[2])
    if "successfully sent" in result:
        # Update draft status to sent
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE emails SET status='sent', sent_at=? WHERE id=?", (datetime.now().isoformat(), email_id))
        conn.commit()
        conn.close()
    return result


def fetch_inbox(limit: int = 5) -> List[Dict[str, str]]:
    """
    Fetch recent inbox messages using IMAP if valid credentials exist.
    Falls back to structured mock inbox data for demo mode.
    """
    if is_valid_gmail_config():
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            recent_ids = email_ids[-limit:]
            inbox_list = []

            for e_id in reversed(recent_ids):
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg.get("Subject", "(No Subject)")
                        sender = msg.get("From", "(Unknown Sender)")
                        date = msg.get("Date", "")
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                        inbox_list.append({
                            "sender": sender,
                            "subject": subject,
                            "date": date,
                            "snippet": body[:200].strip()
                        })
            mail.logout()
            if inbox_list:
                return inbox_list
        except Exception:
            pass

    # Mock inbox data for instant offline demo
    return [
        {
            "sender": "sarah.chen@techcorp.io",
            "subject": "Project Milestone Review & Q3 Roadmap",
            "date": "Today, 09:15 AM",
            "snippet": "Hi team, please find attached the draft for the Q3 project milestone. Let me know your thoughts on the timeline by EOD."
        },
        {
            "sender": "support@cloudservice.com",
            "subject": "Scheduled System Maintenance Notification",
            "date": "Yesterday, 04:30 PM",
            "snippet": "Our database cluster will undergo routine maintenance this Saturday between 02:00 UTC and 04:00 UTC."
        },
        {
            "sender": "david.mentor@university.edu",
            "subject": "Feedback on Second Brain Architecture Plan",
            "date": "Yesterday, 02:10 PM",
            "snippet": "Great progress on the LangChain multi-agent coordinator design! Make sure your structured output schema is strictly typed."
        }
    ]


def summarize_inbox() -> str:
    """Generate an AI summary of recent inbox items."""
    inbox = fetch_inbox(limit=5)
    formatted = "\n\n".join(
        f"From: {item['sender']}\nSubject: {item['subject']}\nDate: {item['date']}\nPreview: {item['snippet']}"
        for item in inbox
    )
    prompt = f"""Summarize these recent inbox emails into a concise executive digest. Highlight urgent items, key actions required, and brief status updates:

Emails:
{formatted}"""
    return get_text_content(llm.invoke(prompt))


def search_emails(query: str) -> str:
    """Search drafts and sent emails in SQLite DB."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, recipient, subject, status, created_at FROM emails WHERE recipient LIKE ? OR subject LIKE ? OR body LIKE ?",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()
    conn.close()

    if not rows:
        return f"No stored emails matching '{query}'."

    return "\n".join(
        f"• #{r[0]} [{r[3].upper()}] To: {r[1] or 'N/A'} | Subject: {r[2]} ({r[4][:10]})"
        for r in rows
    )
