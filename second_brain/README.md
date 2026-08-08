# 🧠 Second Brain — AI Personal Knowledge & Productivity Assistant

A LangChain + Streamlit "second brain": one chat assistant that combines document search (RAG), web/Wikipedia research, notes, tasks, email drafting, and a daily briefing generator, backed by short-term/persistent/long-term memory.

This project is structured as **real, importable Python files** (not just notebook cells) so the exact same code runs in Colab while you build it and on the web once you deploy it — nothing to rewrite at deployment time.

---

## Project Structure

```
second_brain/
├── app.py                    # Streamlit entry point — run this
├── requirements.txt
├── .env.example               # copy to .env and fill in
├── core/
│   ├── config.py               # reads secrets from .env OR st.secrets
│   ├── llm.py                  # shared LLM instance
│   ├── memory.py                # Module 11 — short/persistent/long-term memory
│   ├── models.py                # Module 12 — Pydantic structured output
│   ├── coordinator.py           # Module 10 — routes requests to the right agent
│   ├── python_tool.py           # Module 13 — stats & charts
│   ├── weather_tool.py          # optional stretch
│   └── reminder_tool.py         # optional stretch
├── agents/
│   ├── knowledge_agent.py       # Module 2/4 — RAG over uploaded docs
│   ├── research_agent.py        # Module 3 — web + Wikipedia
│   ├── notes_agent.py           # Module 5
│   ├── task_agent.py            # Module 6
│   ├── email_agent.py           # Module 4 — draft + send (SMTP)
│   ├── briefing_agent.py        # Module 7/9 — daily briefing, parallel gather
│   └── drive_agent.py           # optional stretch — Google Drive
├── sample_docs/                 # put 2-3 demo PDFs here before submission
└── data/                        # SQLite DB + Chroma vector store (auto-created, gitignored)
```

---

## Part 1 — Build & Test in Google Colab

Colab is great for building and testing each piece fast. Do this first.

### Step 1: Upload the project to Colab

```python
# In a Colab cell — upload the whole project as a zip, then unzip it
from google.colab import files
uploaded = files.upload()   # choose second_brain.zip
```
```python
!unzip -q second_brain.zip -d /content/
%cd /content/second_brain
```

### Step 2: Install dependencies

```python
!pip install -q -r requirements.txt
```

### Step 3: Set your API key for this session

```python
import os
from getpass import getpass
os.environ["OPENAI_API_KEY"] = getpass("OpenAI API key: ")
```

### Step 4: Test each agent standalone before touching Streamlit

```python
import sys; sys.path.append("/content/second_brain")

from agents.research_agent import research
print(research("Latest AI industry trends"))
```
```python
from agents.notes_agent import create_note, search_notes
print(create_note("Test note", "This is a test", "demo"))
print(search_notes("test"))
```
```python
from agents.task_agent import add_task, list_pending_tasks
print(add_task("Prepare workshop slides", "2026-08-10"))
print(list_pending_tasks())
```
```python
# Knowledge base — upload a sample PDF first
from google.colab import files
uploaded = files.upload()
from agents.knowledge_agent import build_knowledge_base, search_knowledge_base
print(build_knowledge_base(list(uploaded.keys())))
print(search_knowledge_base("What is this document about?"))
```
```python
from core.coordinator import coordinator
print(coordinator("Latest AI news"))
print(coordinator("Show my pending tasks"))
```
```python
from agents.briefing_agent import generate_daily_briefing
briefing = generate_daily_briefing()
print(briefing.model_dump_json(indent=2))
```

Fix bugs here, one function at a time — it's much faster to debug a single `print()` than the full Streamlit app.

### Step 5: Preview the full Streamlit app inside Colab

Colab can't render Streamlit inline, so tunnel it out temporarily just to eyeball it:

```python
!npm install -g localtunnel
!streamlit run app.py &>/content/logs.txt &
import time; time.sleep(5)
!npx localtunnel --port 8501
```
Open the printed URL. If it asks for a tunnel password:
```python
!wget -q -O - https://loca.lt/mytunnelpassword
```

This is a **preview only** — it disappears when your Colab session ends. For a permanent, always-on web app, go to Part 2.

---

## Part 2 — Deploy for Real (Streamlit Community Cloud, free)

Once everything works in Colab, deploy properly. This is the standard, free way to get a public URL for a Streamlit app.

### Step 1: Push the project to GitHub

From your local machine (or Colab, or GitHub's web upload UI) — make sure `.env`, `data/`, and any secret files are **not** included (the `.gitignore` already excludes them):

```bash
cd second_brain
git init
git add .
git commit -m "Initial commit: Second Brain capstone project"
git branch -M main
git remote add origin https://github.com/<your-username>/second-brain.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Community Cloud

1. Go to **share.streamlit.io** and sign in with GitHub
2. Click **"New app"**
3. Pick your repo, branch `main`, and set the main file path to `app.py`
4. Click **"Advanced settings"** → **Secrets** and paste:
   ```toml
   OPENAI_API_KEY = "sk-..."
   GMAIL_ADDRESS = "you@gmail.com"
   GMAIL_APP_PASSWORD = "xxxx-xxxx-xxxx-xxxx"
   OPENWEATHER_API_KEY = ""
   ```
   (`core/config.py` already knows to read these from `st.secrets` automatically — no code changes needed.)
5. Click **Deploy**

In a couple of minutes you'll have a public URL like `https://second-brain-<yourname>.streamlit.app` — this is what you submit/demo.

### Step 3: Redeploying after changes

Any `git push` to `main` auto-redeploys the live app within a minute or two. No manual redeploy step.

---

## Optional Stretch Goals (already included in the code)

| Stretch feature | File | What you need to activate it |
|---|---|---|
| Weather Tool | `core/weather_tool.py` | Free API key from openweathermap.org, add as `OPENWEATHER_API_KEY` secret |
| Calendar Reminder Tool | `core/reminder_tool.py` | Works out of the box, no external API — just import and call `add_reminder()` / `list_reminders()` |
| Google Drive Toolkit | `agents/drive_agent.py` | Needs a Google Cloud OAuth project (see below) |

### Setting up Google Drive / full Gmail API (only if you want these)

1. Go to console.cloud.google.com → create a project
2. Enable the **Gmail API** and/or **Google Drive API**
3. Configure the OAuth consent screen (External, add yourself as a test user)
4. Create OAuth Client ID credentials → Application type: Desktop app → download as `client_secret.json`
5. Place `client_secret.json` in your project root (it's gitignored — don't commit it)
6. The first call to `drive_agent.upload_report()` will open a local auth flow — follow the prompt once, and a token is cached in `data/drive_token.pickle` for future calls

Note: this OAuth flow needs a local browser popup, so it works when running locally but **not** on Streamlit Community Cloud (no browser access on the server). If you want Drive/full Gmail working in the deployed web app, you'd need to pre-generate the token locally and upload it as a secret — for a course capstone, it's usually fine to demo this part locally/in Colab and keep the deployed web app on the SMTP email path.

---

## Testing Checklist Before Submission

Run each of these against your deployed app and confirm the routing/output is sensible:

- [ ] "Find my project notes" → routes to Notes
- [ ] "Latest AI News" → routes to Research
- [ ] "Draft an email to my mentor about the project" → routes to Email
- [ ] Upload a PDF, ask a question about it → routes to Knowledge
- [ ] "Remember that I prefer concise reports" → check it's saved (Preferences panel)
- [ ] Generate Daily Briefing → all 7 structured fields populate
- [ ] Task stats tab shows a chart after adding/completing a few tasks

## Deliverables Checklist

- [ ] Streamlit application deployed and reachable via public URL
- [ ] Complete source code on GitHub
- [ ] This README (setup + architecture + deployment)
- [ ] `requirements.txt`
- [ ] Sample knowledge base documents in `sample_docs/`
- [ ] Short user guide / demo video (optional but recommended)
