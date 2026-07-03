# InterviewAI — Mock Interview App

AI-generated mock interviews from your resume + a job description, with
spoken questions, voice answers, and AI feedback scoring.

## Stack (all free tier)
- **Streamlit** — UI + hosting (Streamlit Community Cloud)
- **Groq** — LLM for question generation and answer evaluation
- **faster-whisper** — speech-to-text (runs on the server, CPU)
- **Browser Web Speech API** — text-to-speech (runs in the user's browser)
- **PyPDF2 / python-docx** — resume & job description parsing

## Deploy to Streamlit Community Cloud

1. **Push this folder to a public GitHub repo.**

2. **Get a free Groq API key:**
   - Go to https://console.groq.com/keys
   - Sign in, click "Create API Key," copy it

3. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - "New app" → point it at your repo, branch, and `app.py`

4. **Add your secret:**
   - In your app's dashboard: **Settings → Secrets**
   - Paste:
     ```
     GROQ_API_KEY = "your_key_here"
     ```
   - Save — the app will restart automatically

That's it — no servers, no ongoing cost.

## Run locally

```bash
pip install -r requirements.txt
export GROQ_API_KEY="your_key_here"   # or create .streamlit/secrets.toml from the example
streamlit run app.py
```

## Known limitations (things to know, not bugs)

- **Sessions are not persistent long-term.** `sessions/*.json` is written to
  the app's local disk, which Streamlit Cloud wipes on redeploy/restart.
  Fine for demos; if you want history to survive restarts, swap
  `utils/storage.py` to write to a free Postgres DB (e.g. Supabase) instead.
- **First transcription per session is slow.** `faster-whisper`'s "base"
  model loads fresh the first time the app spins up (Streamlit Cloud apps
  sleep after inactivity). It's cached after that via `st.cache_resource`.
- **TTS voice/quality depends on the visitor's browser**, since it uses the
  Web Speech API client-side rather than a server-side voice engine.
