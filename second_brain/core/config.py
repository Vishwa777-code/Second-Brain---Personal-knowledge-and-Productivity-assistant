"""
Central place to read API keys / secrets.
Works locally (.env), in Colab (os.environ set manually), and on Streamlit
Community Cloud (st.secrets), without changing any other file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/".env")

def get_secret(key: str, default: str = "") -> str:
    # 1. Streamlit Cloud secrets (only available once the app is actually running under `streamlit run`)
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # 2. Environment variable (.env locally, or manually set in Colab)
    return os.environ.get(key, default)

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
GMAIL_ADDRESS = get_secret("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = get_secret("GMAIL_APP_PASSWORD")
OPENWEATHER_API_KEY = get_secret("OPENWEATHER_API_KEY")


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "second_brain.db")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
