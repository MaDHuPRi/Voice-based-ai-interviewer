import tempfile
import streamlit as st
from faster_whisper import WhisperModel


@st.cache_resource(show_spinner=False)
def _get_model():
    # Cached so the model loads once per server instance, not once per rerun.
    return WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Transcribes audio recorded in the user's browser (via st.audio_input).
    Replaces the old sounddevice mic-recording flow, which only worked when
    the app ran on your own machine — a Streamlit Cloud server has no
    microphone of its own to record from.
    """
    model = _get_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    segments, _ = model.transcribe(tmp_path)
    return " ".join(seg.text for seg in segments).strip()
