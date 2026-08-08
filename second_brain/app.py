import os
import streamlit as st

from core.memory import save_message, load_history, remember, recall
from core.coordinator import coordinator
from core.python_tool import task_completion_stats
from agents.knowledge_agent import build_knowledge_base
from agents.notes_agent import create_note, list_notes, delete_note
from agents.task_agent import add_task, complete_task, list_all_tasks
from agents.briefing_agent import generate_daily_briefing
from agents.email_agent import (
    generate_email_draft,
    save_email_draft,
    list_email_drafts,
    list_sent_emails,
    send_email,
    send_email_by_id,
    delete_email,
    fetch_inbox,
    summarize_inbox
)

st.set_page_config(page_title="Second Brain", page_icon="🧠", layout="wide")
st.title("🧠 Second Brain — Personal Knowledge & Productivity Assistant")

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_category" not in st.session_state:
    st.session_state.last_category = None
if "draft_recipient" not in st.session_state:
    st.session_state.draft_recipient = ""
if "draft_subject" not in st.session_state:
    st.session_state.draft_subject = ""
if "draft_body" not in st.session_state:
    st.session_state.draft_body = ""

# ---------- Sidebar ----------
with st.sidebar:
    st.header("📚 Knowledge Base")
    uploaded_files = st.file_uploader(
        "Upload documents (PDF/TXT)", accept_multiple_files=True, type=["pdf", "txt"]
    )
    if st.button("Build Knowledge Base", use_container_width=True):
        if uploaded_files:
            os.makedirs("data/uploads", exist_ok=True)
            paths = []
            for f in uploaded_files:
                path = os.path.join("data/uploads", f.name)
                with open(path, "wb") as out:
                    out.write(f.getbuffer())
                paths.append(path)
            with st.spinner("Indexing documents..."):
                result = build_knowledge_base(paths)
            st.success(result)
        else:
            st.warning("Upload at least one file first.")

    st.divider()
    st.header("📝 Notes")
    with st.expander("Add a note"):
        note_title = st.text_input("Title", key="note_title")
        note_content = st.text_area("Content", key="note_content")
        if st.button("Save Note"):
            st.success(create_note(note_title, note_content))
    with st.expander("View notes"):
        for nid, title, content, tags, created in list_notes():
            st.markdown(f"**{title}**  \n{content}")
            if st.button(f"Delete '{title}'", key=f"del_note_{nid}"):
                delete_note(title)
                st.rerun()

    st.divider()
    st.header("✅ Tasks")
    with st.expander("Add a task"):
        task_desc = st.text_input("Task description", key="task_desc")
        task_due = st.text_input("Due date (optional)", key="task_due")
        if st.button("Add Task"):
            st.success(add_task(task_desc, task_due))
    with st.expander("View tasks"):
        for tid, desc, status, due in list_all_tasks():
            col1, col2 = st.columns([4, 1])
            col1.write(f"{'✅' if status == 'completed' else '⬜'} {desc} ({due or 'no date'})")
            if status == "pending" and col2.button("Done", key=f"done_{tid}"):
                complete_task(desc)
                st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.header("👤 Preferences")
    pref_style = st.selectbox("Preferred report style", ["concise", "detailed"],
                              index=0 if recall("preferred_report_style") != "detailed" else 1)
    if st.button("Save Preference"):
        remember("preferred_report_style", pref_style)
        st.success("Saved to long-term memory.")

# ---------- Main: Navigation Tabs ----------
tab_chat, tab_email, tab_briefing, tab_stats = st.tabs(
    ["💬 Chat", "📧 Email Agent", "📋 Daily Briefing", "📊 Stats"]
)

# ---------- Tab 1: Chat ----------
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask your Second Brain..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, category = coordinator(prompt)
            st.write(response)
            st.session_state.last_category = category

        st.session_state.messages.append({"role": "assistant", "content": response})

    if st.session_state.last_category:
        with st.expander("🔧 Tool Execution Summary"):
            st.write(f"Last request was routed to: **{st.session_state.last_category}** agent")

# ---------- Tab 2: Email Agent ----------
with tab_email:
    st.subheader("📧 Email Assistant")

    sub_tab_compose, sub_tab_inbox, sub_tab_history = st.tabs(
        ["✉️ Compose & AI Draft", "📥 Inbox Digest", "📂 Drafts & History"]
    )

    with sub_tab_compose:
        st.markdown("#### Generate Email Draft with AI")
        email_prompt = st.text_area(
            "Describe the email you want to write:",
            placeholder="e.g. Write a polite email to John asking for feedback on the project milestone by Thursday.",
            key="email_prompt_input"
        )
        if st.button("✨ Generate AI Draft"):
            if email_prompt.strip():
                with st.spinner("Drafting email..."):
                    draft_obj = generate_email_draft(email_prompt)
                    st.session_state.draft_recipient = draft_obj.recipient
                    st.session_state.draft_subject = draft_obj.subject
                    st.session_state.draft_body = draft_obj.body
                st.success(f"Generated draft with '{draft_obj.tone}' tone!")
            else:
                st.warning("Please enter an email instruction first.")

        st.divider()
        st.markdown("#### Review & Edit Draft")
        recipient = st.text_input("Recipient Email", value=st.session_state.draft_recipient)
        subject = st.text_input("Subject", value=st.session_state.draft_subject)
        body = st.text_area("Body", value=st.session_state.draft_body, height=200)

        col_save, col_send = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save as Draft", use_container_width=True):
                if subject and body:
                    draft_id = save_email_draft(recipient, subject, body)
                    st.success(f"Draft saved to SQLite DB (Draft #{draft_id}).")
                else:
                    st.warning("Please provide a subject and body to save a draft.")

        with col_send:
            if st.button("🚀 Send Email Now", use_container_width=True):
                if recipient and subject and body:
                    with st.spinner("Sending email..."):
                        res = send_email(recipient, subject, body)
                    st.info(res)
                else:
                    st.warning("Please provide Recipient, Subject, and Body before sending.")

    with sub_tab_inbox:
        st.markdown("#### Inbox Summary & Messages")
        if st.button("🤖 Generate AI Inbox Digest"):
            with st.spinner("Analyzing inbox emails..."):
                digest = summarize_inbox()
            st.markdown(digest)

        st.divider()
        st.markdown("#### Recent Inbox Items")
        inbox_items = fetch_inbox(limit=5)
        for idx, item in enumerate(inbox_items):
            with st.expander(f"📩 {item['subject']} — from {item['sender']} ({item['date']})"):
                st.write(f"**From:** {item['sender']}")
                st.write(f"**Date:** {item['date']}")
                st.write(f"**Content Snippet:**\n{item['snippet']}")
                if st.button(f"Reply / Draft Response", key=f"reply_btn_{idx}"):
                    reply_instruction = f"Reply to {item['sender']} regarding '{item['subject']}': {item['snippet']}"
                    draft_obj = generate_email_draft(reply_instruction)
                    st.session_state.draft_recipient = item['sender']
                    st.session_state.draft_subject = f"Re: {item['subject']}"
                    st.session_state.draft_body = draft_obj.body
                    st.success("Draft created! Switch to 'Compose & AI Draft' tab to review.")

    with sub_tab_history:
        st.markdown("#### Saved Drafts")
        drafts = list_email_drafts()
        if not drafts:
            st.info("No pending drafts.")
        for did, recip, subj, bdy, created in drafts:
            with st.expander(f"📝 #{did}: {subj} (To: {recip or 'Not specified'}) — {created[:10]}"):
                st.write(f"**To:** {recip or 'N/A'}")
                st.write(f"**Subject:** {subj}")
                st.text_area("Body", bdy, key=f"draft_body_{did}", height=120, disabled=True)
                col_d_send, col_d_del = st.columns([1, 1])
                with col_d_send:
                    target_to = st.text_input("Send to email:", value=recip, key=f"send_to_input_{did}")
                    if st.button(f"Send Draft #{did}", key=f"send_draft_btn_{did}"):
                        res = send_email_by_id(did, to=target_to)
                        st.info(res)
                        st.rerun()
                with col_d_del:
                    if st.button(f"Delete Draft #{did}", key=f"del_draft_btn_{did}"):
                        delete_email(did)
                        st.success("Draft deleted.")
                        st.rerun()

        st.divider()
        st.markdown("#### Sent Emails History")
        sent_items = list_sent_emails()
        if not sent_items:
            st.info("No sent email record yet.")
        for sid, recip, subj, bdy, sent_at in sent_items:
            with st.expander(f"✅ #{sid}: {subj} (To: {recip}) — {sent_at[:16] if sent_at else ''}"):
                st.write(f"**To:** {recip}")
                st.write(f"**Subject:** {subj}")
                st.write(f"**Sent At:** {sent_at}")
                st.text_area("Body", bdy, key=f"sent_body_{sid}", height=100, disabled=True)

# ---------- Tab 3: Daily Briefing ----------
with tab_briefing:
    st.subheader("Today's Briefing")
    if st.button("Generate Briefing"):
        with st.spinner("Gathering tasks, notes, and news..."):
            briefing = generate_daily_briefing()
        st.markdown(f"**Summary:** {briefing.daily_summary}")

        with st.expander("Pending Tasks"):
            for t in briefing.pending_tasks:
                st.write(f"- {t}")
        with st.expander("Knowledge Base Highlights"):
            for k in briefing.knowledge_base_highlights:
                st.write(f"- {k}")
        with st.expander("Latest Research"):
            st.write(briefing.latest_research)
        with st.expander("Recommendations"):
            for r in briefing.recommendations:
                st.write(f"- {r}")
        with st.expander("Next Actions"):
            for a in briefing.next_actions:
                st.write(f"- {a}")

        st.download_button(
            "Download Briefing (TXT)",
            briefing.model_dump_json(indent=2),
            file_name="daily_briefing.txt",
        )

        with st.expander("📧 Email this briefing"):
            to_addr = st.text_input("Send to")
            if st.button("Send Briefing Email"):
                st.info(send_email(to_addr, "Daily Briefing", briefing.model_dump_json(indent=2)))

# ---------- Tab 4: Stats ----------
with tab_stats:
    st.subheader("Task Completion")
    summary, chart_path = task_completion_stats()
    st.write(summary)
    if os.path.exists(chart_path):
        st.image(chart_path)
