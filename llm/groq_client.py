import requests
from config import GROQ_API_KEY, GROQ_API_URL


def call_groq(model_name: str, prompt_text: str, timeout: int = 60):
    """
    Calls the Groq chat completions API. Mirrors the (ok, text) return
    signature of the old call_ollama_http() so the rest of the app doesn't
    need to change.
    """
    if not GROQ_API_KEY:
        return False, (
            "Missing GROQ_API_KEY. Add it under your app's Settings → Secrets "
            "on Streamlit Cloud (or as an env var locally)."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.7,
    }

    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        return False, f"Request to Groq failed: {e}"

    if r.status_code != 200:
        return False, f"Groq API error ({r.status_code}): {r.text}"

    try:
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return True, text
    except (KeyError, IndexError, ValueError) as e:
        return False, f"Unexpected Groq response format: {e}"
