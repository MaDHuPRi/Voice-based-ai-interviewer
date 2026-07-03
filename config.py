import os

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


def _get_secret(key: str, default=None):
    """Reads from Streamlit secrets first (for Streamlit Cloud), falls back to
    environment variables (for local dev)."""
    if _HAS_STREAMLIT:
        try:
            return st.secrets[key]
        except Exception:
            pass
    return os.environ.get(key, default)


# ── Groq (free tier) — replaces local Ollama ────────────────────────────────
GROQ_API_KEY = _get_secret("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Fast + free Groq model. See https://console.groq.com/docs/models for others.
DEFAULT_MODEL = "llama-3.3-70b-versatile"
