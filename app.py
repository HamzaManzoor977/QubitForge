from db import init_db, load_history, save_history, clear_history
import os
import json
import uuid
import tempfile
import re
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# =============================
# ENV & CORE IMPORTS
# =============================
load_dotenv()

from research import deep_research
from agent import translate_text

# =============================
# AUDIO TRANSCRIPTION (GROQ)
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

# =============================
# ADVANCED MARKDOWN FIXER
# =============================
def fix_markdown_formatting(text):
    if not text:
        return ""

    text = re.sub(r':\s*(\d+\.|-)', r':\n\n\1', text)
    text = re.sub(r'(\.|\?|\!)\s+(\d+\.|-)', r'\1\n\n\2', text)

    lines = text.split('\n')
    fixed = []

    for i, line in enumerate(lines):
        fixed.append(line)
        if i < len(lines) - 1:
            if line.strip() and re.match(r'^(\d+\.|-|\*)', lines[i + 1].strip()):
                fixed.append("")

    return "\n".join(fixed)

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="QubitForge Deep Research Agent",
    layout="centered"
)

init_db()

# =============================
# SESSION STATE INIT (CRITICAL)
# =============================
if "research_output" not in st.session_state:
    st.session_state.research_output = None

if "spoken_topic" not in st.session_state:
    st.session_state.spoken_topic = ""

if "loaded_from_history" not in st.session_state:
    st.session_state.loaded_from_history = False

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📜 Research Memory")

    theme_dark = st.toggle("🌗 Dark Mode", value=True)

    if theme_dark:
        bg, text, box, border = "#0e1117", "#ffffff", "rgba(255,255,255,0.05)", "#1e90ff"
    else:
        bg, text, box, border = "#ffffff", "#000000", "#f0f2f6", "#ff4b4b"

    st.markdown(
        f"""
        <style>
        .stApp {{ background-color:{bg}; color:{text}; }}
        section[data-testid="stSidebar"] {{ background-color:{box}; }}
        section[data-testid="stSidebar"] * {{ color:{text} !important; }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.divider()

        # ... inside sidebar ...
    history = load_history()

    if not history:
        st.info("No past research found.")
    else:
        for item in history:
            # Mode styling
            if item["mode"] == "quick":
                icon, color = "⚡", "#1e90ff"
            elif item["mode"] == "deep":
                icon, color = "🧠", "#ff8c00"
            else:
                icon, color = "📘", "#2ecc71"

            # FIX: Use 'created_at' instead of 'timestamp'
            # And format the ISO date string nicely
            try:
                dt = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                nice_time = dt.strftime("%b %d, %I:%M %p")
            except:
                nice_time = "Unknown Time"
            
            # Use the formatted time for the key to ensure uniqueness
            key = f"history_{nice_time}_{item['topic']}"

            c1, c2 = st.columns([5, 1])

            with c1:
                if st.button(f"{icon} {item['topic']}", key=key, use_container_width=True):
                    st.session_state.research_output = item["result"]
                    st.session_state.spoken_topic = item["topic"]
                    st.session_state.loaded_from_history = True
                    st.rerun()

            with c2:
                st.markdown(
                    f"""
                    <div style="background:{color};color:white;padding:4px;
                    border-radius:6px;font-size:10px;text-align:center;font-weight:bold;">
                    {item['mode'].upper()}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Display the nice time
            st.caption(f"🕒 {nice_time}")
            st.divider()

    if st.button("🗑️ Clear History"):
        clear_history()
        st.rerun()

# =============================
# MAIN UI
# =============================
st.title("QubitForge Deep Research Agent")

mode = st.radio(
    "Select research mode",
    ["quick", "standard", "deep"],
    horizontal=True
)

# =============================
# BRANDING BYLINE
# =============================
byline_color = "#1e90ff" if mode == "quick" else "#ff8c00" if mode == "deep" else "#2ecc71"

st.markdown(
    f"""
    <div style="text-align:center;margin-bottom:20px;">
        <h3 style="color:{byline_color};font-weight:600;">
            Forge Your Next Big Move
        </h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# =============================
# FILE UPLOAD
# =============================
uploaded_file = st.file_uploader("Upload Source Material (PDF or TXT)", type=["pdf", "txt"])
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

# =============================
# AUDIO + TEXT INPUT
# =============================
audio = st.audio_input("🎙️ Record your topic")

if audio:
    spoken = transcribe_audio_groq(audio)
    if spoken:
        st.session_state.spoken_topic = spoken
        st.success(f"Heard: {spoken}")

topic = st.text_input(
    "Enter your research topic",
    value=st.session_state.spoken_topic,
    placeholder="e.g. Introduction to Artificial Intelligence"
)

# =============================
# RUN RESEARCH
# =============================
if st.button("Run Deep Research", use_container_width=True):
    if not topic and not extracted_text:
        st.warning("Please enter a topic or upload a file.")
    else:
        with st.spinner("Researching..."):
            result = deep_research(f"{topic}\n\n{extracted_text}", mode)
            st.session_state.research_output = result
            save_history(topic or "File Analysis", result, mode)
            st.session_state.loaded_from_history = False

# =============================
# OUTPUT SECTION (FIXED)
# =============================
if st.session_state.research_output is not None:
    st.divider()

    language = st.selectbox(
        "Translate output",
        ["English", "Urdu", "Arabic", "French", "German", "Spanish"]
    )

    output = (
        translate_text(st.session_state.research_output, language)
        if language != "English"
        else st.session_state.research_output
    )

    main_text, citations = output, ""

    if "REFERENCES" in output:
        main_text, citations = output.split("REFERENCES", 1)
    elif "SOURCES" in output:
        main_text, citations = output.split("SOURCES", 1)

    st.markdown(
        f"""
        <div style="background:{box};color:{text};
        padding:25px;border-left:5px solid {border};
        border-radius:12px;"></div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(fix_markdown_formatting(main_text).replace("•", "- "))

    if citations.strip():
        st.divider()
        st.subheader("📚 Citations")
        st.markdown(citations.strip())

    # Reset flag
    st.session_state.loaded_from_history = False
