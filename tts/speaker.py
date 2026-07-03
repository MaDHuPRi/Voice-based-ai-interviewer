import json
import streamlit.components.v1 as components


def speak_text(text: str):
    """
    Speaks text using the browser's built-in Web Speech API (SpeechSynthesis).
    Runs client-side, so it works on Streamlit Cloud with no server audio
    dependency and no extra cost. Replaces the old macOS `say` subprocess call.
    """
    safe_text = json.dumps(text or "")
    components.html(
        f"""
        <script>
        (function() {{
            try {{
                const utterance = new SpeechSynthesisUtterance({safe_text});
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utterance);
            }} catch (e) {{
                console.warn("Speech synthesis not supported in this browser:", e);
            }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
