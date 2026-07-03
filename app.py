import streamlit as st
import re
import time

from config import DEFAULT_MODEL
from loaders.file_loader import load_file_text
from llm.prompt_builder import build_prompt
from llm.groq_client import call_groq
from tts.speaker import speak_text
from stt.whisper_stt import transcribe_audio_bytes
from utils.storage import create_new_session, add_answer, finalize_session

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InterviewAI — Mock Interviewer",
    page_icon="🎙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Barlow:wght@300;400;500&display=swap');

/* ── Reset ── */
html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
}
.stApp {
    background: #080810 !important;
    color: #E0E0F0;
}
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080810; }
::-webkit-scrollbar-thumb { background: #00F5C4; border-radius: 2px; }

/* ── Main content text ── */
.main p, .main li,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: #B0B0C8 !important; }
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 { color: #E0E0F0 !important; }

/* ── Hero header ── */
.hero {
    padding: 3rem 0 1rem;
    position: relative;
}
.hero-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #00F5C4;
    margin-bottom: 0.5rem;
}
.hero-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 5rem;
    font-weight: 800;
    line-height: 0.92;
    color: #F0F0FF;
    text-transform: uppercase;
    letter-spacing: -0.02em;
}
.hero-title .accent { color: #00F5C4; }
.hero-title .accent2 { color: #FFB800; }
.hero-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #404060;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.75rem;
}

/* ── Phase indicator ── */
.phase-bar {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 1.5rem 0 2rem;
    border-bottom: 1px solid #12121E;
    padding-bottom: 1.25rem;
}
.phase-step {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #282840;
    padding: 0.35rem 1rem;
    border: 1px solid #12121E;
    border-radius: 999px;
    margin-right: 0.4rem;
}
.phase-step.active {
    color: #00F5C4;
    border-color: #00F5C440;
    background: #00F5C410;
}
.phase-step.done {
    color: #404060;
    border-color: #1E1E30;
    text-decoration: line-through;
}

/* ── Cards ── */
.card {
    background: #0C0C18;
    border: 1px solid #1A1A2E;
    border-radius: 16px;
    padding: 1.75rem 2rem;
    margin-bottom: 1rem;
}
.card-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #404060;
    margin-bottom: 0.75rem;
}
.card h3 { color: #E0E0F0 !important; }
.card p, .card li { color: #8080A0 !important; }

/* ── Question display ── */
.question-card {
    background: linear-gradient(135deg, #0C0C1A, #0A0A16);
    border: 1px solid #1E1E38;
    border-left: 3px solid #00F5C4;
    border-radius: 16px;
    padding: 2rem 2.25rem;
    margin-bottom: 1.25rem;
}
.question-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #00F5C4;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.question-text {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: #F0F0FF;
    line-height: 1.2;
}

/* ── Instruction card ── */
.instruction-card {
    background: #0A0A14;
    border: 1px solid #1A1A30;
    border-radius: 16px;
    padding: 2rem 2.25rem;
    margin-bottom: 1.5rem;
}
.instruction-step {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #12121E;
}
.step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #00F5C4;
    min-width: 24px;
    margin-top: 0.1rem;
}
.step-text {
    font-size: 0.95rem;
    color: #8080A0;
    line-height: 1.5;
}

/* ── Score cards ── */
.score-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.score-card {
    background: #0C0C18;
    border: 1px solid #1A1A2E;
    border-radius: 12px;
    padding: 1.25rem 1rem;
    text-align: center;
}
.score-val {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    color: #00F5C4;
    line-height: 1;
}
.score-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: #404060;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.3rem;
}

/* ── Progress bar ── */
.progress-wrap {
    background: #12121E;
    border-radius: 999px;
    height: 4px;
    margin-bottom: 2rem;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #00F5C4, #FFB800);
    transition: width 0.5s ease;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: transparent;
    color: #00F5C4;
    border: 1px solid #00F5C440;
    border-radius: 8px;
    padding: 0.7rem 2rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
}
div[data-testid="stButton"] > button:hover {
    background: #00F5C415;
    border-color: #00F5C4;
    transform: translateY(-1px);
}

/* ── Primary button override ── */
div[data-testid="stButton"][class*="primary"] > button,
.primary-btn div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #00F5C4, #00C49A) !important;
    color: #080810 !important;
    border: none !important;
    font-weight: 700 !important;
}

/* ── Text inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #0C0C18 !important;
    border: 1px solid #1A1A2E !important;
    border-radius: 10px !important;
    color: #E0E0F0 !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #00F5C440 !important;
    box-shadow: 0 0 0 1px #00F5C420 !important;
}
.stTextArea label, .stTextInput label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #404060 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #0C0C18 !important;
    border: 1px dashed #1A1A2E !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    color: #404060 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

/* ── Sliders ── */
.stSlider label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    color: #404060 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #00F5C4 !important;
}

/* ── Selectbox ── */
.stSelectbox label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    color: #404060 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
div[data-baseweb="select"] > div {
    background: #0C0C18 !important;
    border: 1px solid #1A1A2E !important;
    border-radius: 10px !important;
    color: #E0E0F0 !important;
}

/* ── Checkbox ── */
.stCheckbox label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    color: #606080 !important;
    letter-spacing: 0.08em !important;
}

/* ── Divider ── */
hr { border-color: #12121E !important; }

/* ── Expander ── */
.stExpander {
    background: #0C0C18 !important;
    border: 1px solid #1A1A2E !important;
    border-radius: 10px !important;
}
.stExpander summary { color: #8080A0 !important; }

/* ── Alert/info ── */
.stAlert {
    background: #0C0C18 !important;
    border: 1px solid #1A1A2E !important;
    border-radius: 10px !important;
    color: #8080A0 !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #0C0C18;
    border: 1px solid #1A1A2E;
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.65rem !important;
    color: #404060 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    color: #00F5C4 !important;
}

/* ── Success/Error ── */
.stSuccess { background: #001A12 !important; border-color: #00F5C440 !important; color: #00F5C4 !important; }
.stError { background: #1A0008 !important; border-color: #FF003660 !important; color: #FF4060 !important; }
.stInfo { background: #0A0A18 !important; border-color: #00F5C420 !important; color: #8080A0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "phase": "setup",
    "questions": [],
    "current_q_index": 0,
    "spoken": False,
    "instructions_spoken": False,
    "interview_started": False,
    "session": None,
    "selected_role": "Mock Interview",
    "record_attempt": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.interview_started and st.session_state.session is None:
    st.session_state.session = create_new_session(role=st.session_state.selected_role)

# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_all_questions(text):
    return re.findall(r"\n\d+\.\s+(.*)", text)

INSTRUCTION_TEXT = (
    "Before we begin, here is how the mock interview will work. "
    "I will ask you one question at a time. "
    "After each question, click the start recording button and speak your answer. "
    "Once you finish, press Next Question to continue. "
    "When you are ready, we will begin with the first question."
)

PHASES = ["Setup", "Review", "Instructions", "Interview", "Feedback"]
PHASE_MAP = {"setup": 0, "review": 1, "instructions": 2, "interview": 3, "feedback": 4}

# ── Phase indicator ───────────────────────────────────────────────────────────
current_phase_idx = PHASE_MAP.get(st.session_state.phase, 0)
phase_html = '<div class="phase-bar">'
for i, p in enumerate(PHASES):
    if i < current_phase_idx:
        cls = "done"
    elif i == current_phase_idx:
        cls = "active"
    else:
        cls = ""
    phase_html += f'<div class="phase-step {cls}">{p}</div>'
phase_html += '</div>'

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-eyebrow">// AI-Powered Mock Interview System</div>
    <div class="hero-title">Interview<br><span class="accent">AI</span></div>
    <div class="hero-sub">Ollama · Whisper STT · Real-time Feedback</div>
</div>
{phase_html}
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: SETUP
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "setup":

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown('<div class="card"><div class="card-label">// Job Description</div>', unsafe_allow_html=True)
        with st.form("generation_form"):
            jd_text_area = st.text_area("Paste job description here", height=180, label_visibility="collapsed",
                                         placeholder="Paste the full job description here…")
            jd_file = st.file_uploader("Or upload JD (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
            resume_file = st.file_uploader("Upload your resume (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
            submitted = st.form_submit_button("⚡ Generate Interview Questions")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card"><div class="card-label">// Interview Settings</div>', unsafe_allow_html=True)
        # These live outside the form intentionally for live feedback
        n_technical  = st.slider("Technical questions", 1, 10, 5)
        n_behavioral = st.slider("Behavioral questions", 0, 5, 2)
        difficulty   = st.selectbox("Difficulty level", ["mixed", "easy", "medium", "hard"])
        include_answers = st.checkbox("Include answer outlines")
        st.markdown(f"""
        <div style='margin-top:1.25rem; padding:1rem; background:#080810; border-radius:10px; border:1px solid #12121E;'>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.62rem; color:#404060; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:0.5rem;'>Interview Summary</div>
            <div style='font-family:"Barlow Condensed",sans-serif; font-size:1.4rem; color:#F0F0FF; font-weight:600;'>{n_technical + n_behavioral} Questions</div>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.68rem; color:#606080; margin-top:0.25rem;'>{n_technical} technical · {n_behavioral} behavioral · {difficulty}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Handle form submission ──
    if submitted:
        jd_text = jd_text_area.strip() or load_file_text(jd_file)
        resume_text = load_file_text(resume_file)

        if not jd_text:
            st.error("⚠️  Please provide a job description.")
            st.stop()
        if not resume_text:
            st.error("⚠️  Please upload your resume.")
            st.stop()

        prompt = build_prompt(jd_text, resume_text, n_technical, n_behavioral, difficulty, include_answers)

        with st.spinner("Generating your personalised interview…"):
            ok, output = call_groq(DEFAULT_MODEL, prompt)

        if not ok:
            st.error(output)
            st.stop()

        all_questions = extract_all_questions(output)
        st.session_state.questions   = all_questions[:n_technical + n_behavioral]
        st.session_state.llm_output  = output
        st.session_state.phase       = "review"
        st.session_state.current_q_index = 0
        st.session_state.spoken      = False
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: REVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "review":

    st.markdown('<div class="card"><div class="card-label">// Generated Interview Plan</div>', unsafe_allow_html=True)
    st.markdown(st.session_state.get("llm_output", ""))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown(f"""
        <div style='text-align:center; margin-bottom:1rem;'>
            <div style='font-family:"Barlow Condensed",sans-serif; font-size:2rem; font-weight:700; color:#F0F0FF;'>Ready to begin?</div>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.7rem; color:#404060; margin-top:0.25rem;'>{len(st.session_state.questions)} questions queued</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎙  Start Mock Interview →"):
            st.session_state.session = create_new_session(role=st.session_state.selected_role)
            st.session_state.current_q_index = 0
            st.session_state.interview_started = True
            st.session_state.phase = "instructions"
            st.session_state.spoken = False
            st.session_state.instructions_spoken = False
            st.rerun()

    col_x, col_y, col_z = st.columns([1, 2, 1])
    with col_y:
        if st.button("← Regenerate Questions"):
            st.session_state.phase = "setup"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: INSTRUCTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "instructions":

    col_a, col_b, col_c = st.columns([1, 3, 1])
    with col_b:
        st.markdown("""
        <div style='text-align:center; margin-bottom:2rem;'>
            <div style='font-size:3rem; margin-bottom:0.5rem;'>🎙</div>
            <div style='font-family:"Barlow Condensed",sans-serif; font-size:2.5rem; font-weight:800; color:#F0F0FF; text-transform:uppercase;'>How It Works</div>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.7rem; color:#404060; letter-spacing:0.1em; text-transform:uppercase;'>Read carefully before starting</div>
        </div>
        """, unsafe_allow_html=True)

        steps = [
            ("01", "One question at a time", "The interviewer will ask you one question at a time, just like a real interview."),
            ("02", "Click to record", "Press the Start Recording button — you have up to 60 seconds to answer each question."),
            ("03", "AI transcription", "Your answer is transcribed automatically using Whisper speech recognition."),
            ("04", "Continue", "Press Next Question to move forward. You cannot go back."),
            ("05", "Feedback at the end", "After all questions, you'll receive detailed AI feedback with scores and suggestions."),
        ]

        st.markdown('<div class="instruction-card">', unsafe_allow_html=True)
        for num, title, desc in steps:
            st.markdown(f"""
            <div class="instruction-step">
                <div class="step-num">{num}</div>
                <div>
                    <div style='font-family:"Barlow Condensed",sans-serif; font-size:1.1rem; font-weight:600; color:#E0E0F0; margin-bottom:0.2rem;'>{title}</div>
                    <div class="step-text">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if not st.session_state.instructions_spoken:
            speak_text(INSTRUCTION_TEXT)
            st.session_state.instructions_spoken = True

        if st.button("✦  Begin Interview →"):
            st.session_state.phase = "interview"
            st.session_state.spoken = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: INTERVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "interview":

    questions = st.session_state.questions
    q_idx = st.session_state.current_q_index
    total = len(questions)

    if q_idx < total:
        question = questions[q_idx]

        # Progress
        pct = int((q_idx / total) * 100)
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; margin-bottom:0.4rem;'>
            <span style='font-family:"IBM Plex Mono",monospace; font-size:0.65rem; color:#404060; text-transform:uppercase; letter-spacing:0.1em;'>Question {q_idx+1} of {total}</span>
            <span style='font-family:"IBM Plex Mono",monospace; font-size:0.65rem; color:#00F5C4;'>{pct}% complete</span>
        </div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%;"></div>
        </div>
        """, unsafe_allow_html=True)

        col_q, col_status = st.columns([3, 1])
        with col_q:
            st.markdown(f"""
            <div class="question-card">
                <div class="question-num">// Question {q_idx + 1}</div>
                <div class="question-text">{question}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_status:
            st.markdown(f"""
            <div style='background:#0C0C18; border:1px solid #1A1A2E; border-radius:12px; padding:1.25rem; text-align:center; height:100%;'>
                <div style='font-family:"Barlow Condensed",sans-serif; font-size:3rem; font-weight:800; color:#FFB800; line-height:1;'>{q_idx+1}</div>
                <div style='font-family:"IBM Plex Mono",monospace; font-size:0.6rem; color:#404060; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.25rem;'>of {total}</div>
                <div style='margin-top:1rem; font-family:"IBM Plex Mono",monospace; font-size:0.62rem; color:#00F5C4;'>{'▓' * (q_idx+1)}{'░' * (total-q_idx-1)}</div>
            </div>
            """, unsafe_allow_html=True)

        # Speak question once
        if not st.session_state.spoken:
            speak_text(question)
            st.session_state.spoken = True

        # ── Answer section ──
        st.markdown('<div class="card"><div class="card-label">// Your Answer</div>', unsafe_allow_html=True)

        if "last_answer" not in st.session_state:
            st.markdown(
                "<div style='font-family:\"IBM Plex Mono\",monospace; font-size:0.68rem; "
                "color:#404060; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.75rem;'>"
                "Record your answer (up to 60 seconds)</div>",
                unsafe_allow_html=True,
            )
            audio_value = st.audio_input(
                "Record your answer",
                label_visibility="collapsed",
                key=f"audio_q{q_idx}_{st.session_state.record_attempt}",
            )
            if audio_value is not None:
                start_time = time.time()
                with st.spinner("Transcribing your answer…"):
                    transcript = transcribe_audio_bytes(audio_value.getvalue())
                duration_sec = round(time.time() - start_time, 2)
                st.session_state.last_answer = transcript
                st.session_state.last_duration = duration_sec
                st.rerun()
        else:
            st.markdown(f"""
            <div style='background:#080810; border:1px solid #00F5C420; border-radius:10px; padding:1rem 1.25rem; margin-bottom:1rem;'>
                <div style='font-family:"IBM Plex Mono",monospace; font-size:0.62rem; color:#00F5C4; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;'>✓ Transcribed</div>
                <div style='font-size:0.95rem; color:#C0C0D8; line-height:1.6;'>{st.session_state.last_answer}</div>
            </div>
            """, unsafe_allow_html=True)

            col_next, col_re, _ = st.columns([2, 1, 3])
            with col_next:
                if st.button("Next Question →"):
                    add_answer(
                        session=st.session_state.session,
                        question=question,
                        answer_text=st.session_state.last_answer,
                        duration_sec=st.session_state.last_duration,
                        transcript_conf=1.0
                    )
                    st.session_state.current_q_index += 1
                    st.session_state.spoken = False
                    st.session_state.record_attempt += 1
                    st.session_state.pop("last_answer", None)
                    st.session_state.pop("last_duration", None)
                    st.rerun()
            with col_re:
                if st.button("Re-record"):
                    st.session_state.record_attempt += 1
                    st.session_state.pop("last_answer", None)
                    st.session_state.pop("last_duration", None)
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # All questions done
        path = finalize_session(st.session_state.session)
        st.markdown("""
        <div style='text-align:center; padding:3rem 0;'>
            <div style='font-size:4rem; margin-bottom:1rem;'>🎉</div>
            <div style='font-family:"Barlow Condensed",sans-serif; font-size:3rem; font-weight:800; color:#F0F0FF; text-transform:uppercase;'>Interview Complete!</div>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.72rem; color:#404060; letter-spacing:0.1em; margin-top:0.5rem;'>Processing your feedback…</div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.phase = "feedback"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: FEEDBACK
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "feedback":

    session  = st.session_state.session
    feedback = session.get("aggregated_feedback", {})

    st.markdown("""
    <div style='margin-bottom:1.5rem;'>
        <div style='font-family:"IBM Plex Mono",monospace; font-size:0.7rem; color:#00F5C4; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.25rem;'>// Interview Complete</div>
        <div style='font-family:"Barlow Condensed",sans-serif; font-size:3.5rem; font-weight:800; color:#F0F0FF; text-transform:uppercase; line-height:1;'>Your Feedback</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Score cards ──
    c1, c2, c3, c4 = st.columns(4)
    scores = [
        (c1, "Clarity", feedback.get("avg_clarity", 0), "#00F5C4"),
        (c2, "Confidence", feedback.get("avg_confidence", 0), "#FFB800"),
        (c3, "Technical Depth", feedback.get("avg_technical_depth", 0), "#FF6B35"),
        (c4, "Overall", feedback.get("overall_score", 0), "#FF3366"),
    ]
    for col, label, val, color in scores:
        col.markdown(f"""
        <div style='background:#0C0C18; border:1px solid #1A1A2E; border-radius:12px; padding:1.5rem 1rem; text-align:center;'>
            <div style='font-family:"Barlow Condensed",sans-serif; font-size:3.5rem; font-weight:800; color:{color}; line-height:1;'>{val}</div>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.6rem; color:#404060; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.4rem;'>{label}</div>
            <div style='font-family:"IBM Plex Mono",monospace; font-size:0.58rem; color:#282840; margin-top:0.1rem;'>/ 10</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary ──
    st.markdown('<div class="card"><div class="card-label">// AI Summary</div>', unsafe_allow_html=True)
    st.write(feedback.get("summary", "No summary available."))
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Strengths & Improvements ──
    col_s, col_i = st.columns(2)
    with col_s:
        st.markdown('<div class="card"><div class="card-label" style="color:#00F5C4;">// Strengths</div>', unsafe_allow_html=True)
        for s in feedback.get("strengths", []):
            st.markdown(f"""
            <div style='display:flex; gap:0.75rem; margin-bottom:0.6rem; align-items:flex-start;'>
                <span style='color:#00F5C4; font-family:"IBM Plex Mono",monospace; font-size:0.8rem; margin-top:0.1rem;'>✓</span>
                <span style='font-size:0.9rem; color:#8080A0; line-height:1.5;'>{s}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_i:
        st.markdown('<div class="card"><div class="card-label" style="color:#FFB800;">// Areas to Improve</div>', unsafe_allow_html=True)
        for item in feedback.get("improvements", []):
            st.markdown(f"""
            <div style='display:flex; gap:0.75rem; margin-bottom:0.6rem; align-items:flex-start;'>
                <span style='color:#FFB800; font-family:"IBM Plex Mono",monospace; font-size:0.8rem; margin-top:0.1rem;'>→</span>
                <span style='font-size:0.9rem; color:#8080A0; line-height:1.5;'>{item}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Per-question feedback ──
    st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.7rem; color:#404060; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:1rem;">// Question-by-Question Breakdown</div>', unsafe_allow_html=True)

    for idx, q in enumerate(session.get("questions", []), start=1):
        with st.expander(f"Q{idx} — {q['question'][:80]}{'…' if len(q['question']) > 80 else ''}"):
            st.markdown(f"**Question:** {q['question']}")
            st.markdown(f"**Your Answer:** {q.get('answer_text', '—')}")
            eval_data = q.get("evaluation", {})
            if eval_data:
                m1, m2, m3 = st.columns(3)
                m1.metric("Clarity", eval_data.get("clarity", 0))
                m2.metric("Confidence", eval_data.get("confidence", 0))
                m3.metric("Technical Depth", eval_data.get("technical_depth", 0))
                if eval_data.get("strength"):
                    st.markdown(f'<div style="color:#00F5C4; font-size:0.88rem; margin-top:0.5rem;">✓ {eval_data["strength"]}</div>', unsafe_allow_html=True)
                if eval_data.get("improvement"):
                    st.markdown(f'<div style="color:#FFB800; font-size:0.88rem; margin-top:0.25rem;">→ {eval_data["improvement"]}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Action buttons ──
    col_new, col_export, _ = st.columns([1, 1, 2])
    with col_new:
        if st.button("🔁  Start New Interview"):
            st.session_state.clear()
            st.rerun()
    with col_export:
        if st.button("📄  View Saved Report"):
            st.info(f"Report saved. Check your output folder.")