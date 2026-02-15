from db import init_db, load_history, save_history, clear_history
import os
import uuid
import tempfile
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# =============================
# LOAD ENV
# =============================
current_path = Path(__file__).resolve().parent
env_path = current_path / ".env"
load_dotenv(env_path)

if not os.getenv("GROQ_API_KEY"):
    st.error("CRITICAL ERROR: GROQ_API_KEY not found in .env file!")
    st.stop()

from research import deep_research
from agent import translate_text

# =============================
# AUDIO TRANSCRIPTION
# =============================
def transcribe_audio_groq(audio_data):
    from groq import Groq
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        audio_bytes = audio_data.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        with open(temp_path, "rb") as f:
            text = client.audio.transcriptions.create(
                file=(temp_path, f.read()),
                model="whisper-large-v3",
                response_format="text"
            )

        os.remove(temp_path)
        return text

    except Exception as e:
        st.error(f"Transcription Error: {e}")
        return None

# =============================
# UTILS
# =============================
def clean_text(text):
    if not text:
        return ""
    return text.encode("utf-8", errors="ignore").decode("utf-8")

def fix_markdown_formatting(text):
    if not text:
        return ""
    text = re.sub(r':\s*(\d+\.|-)', r':\n\n\1', text)
    text = re.sub(r'(\.|\?|\!)\s+(\d+\.|-)', r'\1\n\n\2', text)
    return text

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="QubitForge Deep Research Agent", layout="centered")
init_db()

# =============================
# SESSION STATE
# =============================
st.session_state.setdefault("research_output", None)
st.session_state.setdefault("spoken_topic", "")
st.session_state.setdefault("loaded_from_history", False)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📜 Research Memory")

    # Default light mode
    theme_dark = st.toggle("🌗 Dark Mode", value=False)

    if theme_dark:
        bg = "#0b0f19"
        text = "#e2e8f0"
        box = "rgba(30, 41, 59, 0.7)"
        border = "#38bdf8"
        input_bg = "#1e293b"
    else:
        bg = "#ffffff"
        text = "#000000"
        box = "#f0f2f6"
        border = "#ff4b4b"
        input_bg = "#ffffff"

    # CSS
    st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; }}
    input, textarea {{
        background-color:{input_bg}!important;
        color:{text}!important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.divider()

    # ================= HISTORY =================
    history = load_history()

    if not history:
        st.info("No past research found.")
    else:
        for idx, item in enumerate(history):

            if item["mode"] == "quick":
                icon, color = "⚡", "#1e90ff"
            elif item["mode"] == "deep":
                icon, color = "🧠", "#ff8c00"
            else:
                icon, color = "📘", "#2ecc71"

            c1, c2 = st.columns([5,1])

            with c1:
                if st.button(f"{icon} {item['topic']}", key=f"history_{idx}", use_container_width=True):
                    st.session_state.research_output = item["result"]
                    st.session_state.spoken_topic = item["topic"]

            with c2:
                st.markdown(f"""
                <div style="background:{color};color:white;padding:4px;
                border-radius:6px;font-size:10px;text-align:center;font-weight:bold;">
                {item['mode'].upper()}
                </div>
                """, unsafe_allow_html=True)

            st.caption(f"🕒 {item.get('timestamp','')}")
            st.divider()

    if st.button("🗑️ Clear History"):
        clear_history()
        st.rerun()


# =============================
# MAIN UI
# =============================
st.title("QubitForge Deep Research Agent")

mode = st.radio("Select research mode", ["quick", "standard", "deep"], horizontal=True)

# ===== TRUE REACTIVE BYLINE =====
color_map = {
    "quick": "#1e90ff",
    "standard": "#2ecc71",
    "deep": "#ff8c00"
}

st.container().markdown(f"""
<div style="text-align:center;margin-bottom:20px;">
<h3 style="color:{color_map[mode]};font-weight:700;letter-spacing:1px;">
Forge Your Next Big Move
</h3>
</div>
""", unsafe_allow_html=True)

st.divider()

# =============================
# FILE UPLOAD
# =============================
uploaded_file = st.file_uploader("Upload Source Material", type=["pdf","txt"])
extracted_text = ""

if uploaded_file:
    try:
        if uploaded_file.type == "text/plain":
            extracted_text = clean_text(uploaded_file.read().decode("utf-8"))
        else:
            from pypdf import PdfReader
            reader = PdfReader(uploaded_file)
            extracted_text = "\n".join(clean_text(p.extract_text()) for p in reader.pages if p.extract_text())
        st.success("File processed successfully.")
    except Exception as e:
        st.error(e)

st.divider()

audio = st.audio_input("🎙️ Record your topic")

if audio:
    spoken = transcribe_audio_groq(audio)
    if spoken:
        st.session_state.spoken_topic = spoken

topic = st.text_input("Enter your research topic", value=st.session_state.spoken_topic)

# =============================
# RUN
# =============================
if st.button("Run Deep Research", use_container_width=True):
    if not topic and not extracted_text:
        st.warning("Enter topic or upload file.")
    else:
        with st.spinner("Researching..."):
            result = deep_research(f"{topic}\n\n{extracted_text}", mode)
            st.session_state.research_output = result
            save_history(topic or "File Analysis", result, mode)

# =============================
# OUTPUT
# =============================
if st.session_state.research_output:
    st.divider()

    language = st.selectbox("Translate output", ["English","Urdu","Arabic","French","German","Spanish"])

    output = translate_text(st.session_state.research_output, language) if language!="English" else st.session_state.research_output

    st.markdown(fix_markdown_formatting(output))
