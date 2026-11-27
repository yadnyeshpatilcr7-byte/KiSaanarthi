import streamlit as st
import json
import io
import html
import base64
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote
import requests
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
from sentence_transformers import SentenceTransformer, util


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="KiSaanarthi | Agricultural Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# CONSTANTS
# ==================================================

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
CEDA_LOOKUP_BASE = "https://agmarknet.ceda.ashoka.edu.in/api"
CEDA_PRICES_URL = "https://api.ceda.ashoka.edu.in/v1/agmarknet/prices"
DATA_FILE = BASE_DIR / "data" / "knowledge_base.json"

# Optional: drop a cropped banner image here to replace the built-in
# illustration, e.g. assets/banner.png (the farmer + oxen + fields part).
BANNER_IMAGE = BASE_DIR / "assets" / "banner.png"

LANGUAGES = ["English", "Hindi", "Marathi"]
SPEECH_CODES = {"English": "en-IN", "Hindi": "hi-IN", "Marathi": "mr-IN"}
TTS_CODES = {"English": "en", "Hindi": "hi", "Marathi": "mr"}

# label shown in sidebar -> url slug
PAGES = {
    "🏠  Home": "home",
    "🌱  Agricultural Assistant": "assistant",
    "⛅  Weather Information": "weather",
    "📊  Mandi Prices": "mandi",
    "📋  Government Schemes": "schemes",
    "🌿  Crop Guidance": "crops",
    "ℹ️  About KiSaanarthi": "about",
}
SLUG_TO_LABEL = {v: k for k, v in PAGES.items()}

# top navigation bar: (text, slug)
TOP_NAV = [
    ("🏠 Home", "home"),
    ("🌱 Agricultural Assistance", "assistant"),
    ("⛅ Weather", "weather"),
    ("📊 Mandi Prices", "mandi"),
    ("📋 Government Schemes", "schemes"),
]


# ==================================================
# HELPERS
# ==================================================

def clean_html(markup: str) -> str:
    """Strip indentation / blank lines so Markdown never treats HTML as code."""
    return "\n".join(l.strip() for l in markup.splitlines() if l.strip())


def render_html(markup: str, target=st):
    target.markdown(clean_html(markup), unsafe_allow_html=True)


def svg_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def file_uri(path: Path) -> str:
    ext = path.suffix.lower().strip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64," + base64.b64encode(path.read_bytes()).decode()


# ==================================================
# ILLUSTRATIONS (inline SVG, no external files needed)
# ==================================================

BANNER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 220" preserveAspectRatio="xMaxYMax slice">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#EAF4FF"/><stop offset="1" stop-color="#FFFBEA"/>
    </linearGradient>
    <linearGradient id="h1" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B7DB7A"/><stop offset="1" stop-color="#8CC152"/>
    </linearGradient>
    <linearGradient id="h2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#8CCB4A"/><stop offset="1" stop-color="#5FA52E"/>
    </linearGradient>
    <radialGradient id="sun"><stop offset="0" stop-color="#FFE066"/><stop offset="1" stop-color="#FFC107"/></radialGradient>
  </defs>
  <rect width="760" height="220" fill="url(#sky)"/>
  <g stroke="#FFC933" stroke-width="3" stroke-linecap="round">
    <line x1="640" y1="18" x2="640" y2="30"/><line x1="640" y1="82" x2="640" y2="94"/>
    <line x1="604" y1="56" x2="616" y2="56"/><line x1="664" y1="56" x2="676" y2="56"/>
    <line x1="614" y1="30" x2="622" y2="38"/><line x1="658" y1="74" x2="666" y2="82"/>
    <line x1="666" y1="30" x2="658" y2="38"/><line x1="622" y1="74" x2="614" y2="82"/>
  </g>
  <circle cx="640" cy="56" r="21" fill="url(#sun)"/>
  <path d="M0 150 Q120 105 260 140 T520 128 T760 140 L760 220 L0 220Z" fill="#CDE6A8" opacity=".8"/>
  <path d="M0 165 Q160 125 320 158 T620 150 T760 160 L760 220 L0 220Z" fill="url(#h1)"/>
  <path d="M0 190 Q200 160 400 185 T760 182 L760 220 L0 220Z" fill="url(#h2)"/>
  <!-- trees -->
  <g fill="#4E9A2F"><circle cx="560" cy="132" r="22"/><circle cx="582" cy="140" r="17"/><circle cx="540" cy="142" r="16"/></g>
  <rect x="558" y="140" width="5" height="22" fill="#7A5230"/>
  <!-- hut -->
  <rect x="660" y="128" width="46" height="28" fill="#F3E2C0"/>
  <polygon points="654,130 683,106 712,130" fill="#B5703A"/>
  <rect x="676" y="138" width="11" height="18" fill="#8A5A2B"/>
  <!-- wheat -->
  <g stroke="#6BA43A" stroke-width="3" stroke-linecap="round">
    <line x1="470" y1="215" x2="470" y2="170"/><line x1="490" y1="215" x2="490" y2="160"/>
    <line x1="728" y1="215" x2="728" y2="165"/><line x1="745" y1="215" x2="745" y2="172"/>
  </g>
  <g fill="#E7B923">
    <ellipse cx="470" cy="165" rx="5" ry="12"/><ellipse cx="490" cy="155" rx="5" ry="12"/>
    <ellipse cx="728" cy="160" rx="5" ry="12"/><ellipse cx="745" cy="167" rx="5" ry="12"/>
  </g>
</svg>
"""

SIDEBAR_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 150" preserveAspectRatio="none">
  <defs>
    <linearGradient id="a" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#C9E6A0"/><stop offset="1" stop-color="#8CC152"/>
    </linearGradient>
    <linearGradient id="b" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#8FCB52"/><stop offset="1" stop-color="#5FA52E"/>
    </linearGradient>
  </defs>
  <path d="M0 85 Q80 45 170 78 T300 62 L300 150 L0 150Z" fill="#DDEFC3" opacity=".9"/>
  <path d="M0 105 Q90 70 180 100 T300 90 L300 150 L0 150Z" fill="url(#a)"/>
  <path d="M0 128 Q110 108 220 126 T300 120 L300 150 L0 150Z" fill="url(#b)"/>
  <g fill="#6BAE3A"><circle cx="40" cy="92" r="11"/><circle cx="58" cy="97" r="9"/><circle cx="238" cy="80" r="10"/><circle cx="256" cy="86" r="8"/></g>
  <g fill="#7A5230"><rect x="38" y="98" width="3" height="10"/><rect x="236" y="86" width="3" height="10"/></g>
</svg>
"""

banner_uri = file_uri(BANNER_IMAGE) if BANNER_IMAGE.exists() else svg_uri(BANNER_SVG)
sidebar_uri = svg_uri(SIDEBAR_SVG)


# ==================================================
# CUSTOM CSS
# ==================================================

CSS = """
<style>
/* ---------- base ---------- */
.stApp {
    background: linear-gradient(180deg, #F4F8FC 0%, #EEF4FA 100%);
    color: #172B4D;
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton { display: none !important; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }
h1, h2, h3, h4 { color: #123E68; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    border-right: none;
    box-shadow: 4px 0 24px rgba(16,74,128,0.08);
}
section[data-testid="stSidebar"] > div:first-child {
    background:
        url("__SIDEBAR_BG__") bottom center / 100% 170px no-repeat,
        linear-gradient(180deg, #F3F9FF 0%, #E8F2FC 60%, #EAF5E0 100%);
}
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 1rem; }

.sb-brand { text-align: center; padding: 6px 0 4px 0; }
.sb-logo { font-size: 58px; line-height: 1.1; }
.sb-name { font-size: 30px; font-weight: 800; color: #124477; margin: 2px 0 0 0; }
.sb-tag { font-size: 14px; color: #3B556F; margin: 2px 0 0 0; }
.sb-line { height: 1px; background: linear-gradient(90deg, transparent, #BCD0E4, transparent); margin: 18px 0; }

/* nav radio styled as menu */
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 6px; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    padding: 11px 14px; border-radius: 10px; cursor: pointer;
    transition: background .15s; width: 100%;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
    color: #123E68; font-weight: 600; font-size: 15px; margin: 0;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(20,93,160,0.10); }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(90deg, #0F4C8A, #1A6CC0);
    box-shadow: 0 4px 12px rgba(20,93,160,0.35);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #FFFFFF; }

.sb-section { font-size: 17px; font-weight: 800; color: #123E68; margin: 0 0 10px 4px; }
.lang-chip {
    display: block; width: fit-content; min-width: 170px;
    background: rgba(255,255,255,0.75); border: 1px solid #D5E4F5;
    border-radius: 999px; padding: 7px 16px; margin-bottom: 8px;
    color: #123E68; font-weight: 600; font-size: 14px;
}
.sb-foot { color: #5A7088; font-size: 12px; margin-top: 14px; padding-bottom: 150px; }

/* ---------- header banner ---------- */
.brand-header {
    position: relative; overflow: hidden; min-height: 190px;
    background: linear-gradient(90deg, #FFFFFF 0%, #FFFFFF 38%, #F2F8EC 100%);
    border: 1px solid #DCE5F1; border-radius: 16px;
    padding: 26px 32px; margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(16,74,128,0.07);
}
.brand-art {
    position: absolute; top: 0; right: 0; bottom: 0; width: 62%;
    background: url("__BANNER__") right bottom / cover no-repeat;
    -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 40%);
            mask-image: linear-gradient(to right, transparent 0%, #000 40%);
}
.brand-chars {
    position: absolute; right: 7%; bottom: 8px; font-size: 76px; line-height: 1;
    letter-spacing: 6px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.18));
}
.brand-text { position: relative; z-index: 2; }
.brand-title { font-size: 50px; font-weight: 800; color: #124477; margin: 0; line-height: 1.1; }
.brand-subtitle { font-size: 18px; color: #1D3B5C; margin-top: 8px; font-weight: 500; }
.brand-hindi { font-size: 17px; color: #1D3B5C; margin-top: 6px; }

/* ---------- top nav ---------- */
.nav-bar {
    background: linear-gradient(90deg, #0E4378, #1560A8);
    border-radius: 12px; padding: 13px 18px; margin-bottom: 22px;
    display: flex; justify-content: space-around; align-items: center;
    box-shadow: 0 6px 16px rgba(14,67,120,0.28);
}
.nav-bar a {
    color: #FFFFFF !important; text-decoration: none !important;
    font-weight: 600; font-size: 15.5px; padding: 4px 10px; border-radius: 8px;
}
.nav-bar a:hover { background: rgba(255,255,255,0.16); }
.nav-bar a.active { background: rgba(255,255,255,0.22); }
.nav-sep { color: rgba(255,255,255,0.45); }

/* ---------- welcome card ---------- */
.welcome-card {
    position: relative; overflow: hidden; text-align: center;
    background: linear-gradient(135deg, #FFFFFF 0%, #F4FAEC 55%, #E5F3D3 100%);
    border: 1px solid #DCE9D2; border-radius: 16px;
    padding: 30px 24px 26px 24px; margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(16,74,128,0.06);
}
.welcome-card::before { content: "🌱"; position: absolute; left: 22px; bottom: 8px; font-size: 52px; opacity: .9; }
.welcome-card::after  { content: "🌾"; position: absolute; right: 24px; bottom: 8px; font-size: 52px; opacity: .9; }
.welcome-title { color: #123E68; font-size: 36px; font-weight: 800; }
.welcome-sub { color: #1D3B5C; font-size: 18px; font-weight: 500; margin-top: 6px; }
.welcome-desc { color: #2B4561; font-size: 16px; margin-top: 14px; }

.section-title { font-size: 28px; font-weight: 800; color: #123E68; margin: 6px 0 14px 2px; }

/* ---------- service cards ---------- */
.svc-card {
    display: flex; align-items: center; gap: 18px;
    background: #FFFFFF; border: 1px solid #E1EAF4; border-radius: 14px;
    padding: 18px 20px; margin-bottom: 18px; min-height: 108px;
    box-shadow: 0 4px 14px rgba(16,74,128,0.07);
    transition: transform .15s, box-shadow .15s;
}
.svc-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(16,74,128,0.13); }
.svc-icon {
    flex: 0 0 64px; height: 64px; border-radius: 16px; font-size: 34px;
    display: flex; align-items: center; justify-content: center;
}
.svc-title { font-size: 19px; font-weight: 800; color: #123E68; margin: 0 0 4px 0; }
.svc-desc { font-size: 14px; color: #4A607A; margin: 0; line-height: 1.45; }

/* ---------- assistant page ---------- */
.input-panel {
    background: #FFFFFF; border: 1px solid #DCE5F1; border-radius: 14px;
    padding: 18px 20px; margin-bottom: 10px;
    box-shadow: 0 3px 10px rgba(16,74,128,0.05);
}
.input-panel h3 { margin: 0 0 6px 0; color: #124477; }
.input-panel p { margin: 0; color: #53677F; }

.answer-card {
    background: #FFFFFF; border-left: 6px solid #1765B1; border-radius: 12px;
    padding: 22px; margin-top: 20px; box-shadow: 0 4px 14px rgba(16,74,128,0.08);
}
.answer-card h3 { color: #124477; margin-top: 0; }
.answer-card p { color: #172B4D; font-size: 16px; line-height: 1.65; margin-bottom: 0; }

/* ---------- widgets ---------- */
.stButton > button {
    background: linear-gradient(90deg, #0F4C8A, #1A6CC0); color: #FFFFFF;
    border: none; border-radius: 10px; font-weight: 600; min-height: 44px;
    transition: .2s; box-shadow: 0 3px 8px rgba(20,93,160,0.25);
}
.stButton > button:hover { filter: brightness(1.1); color: #FFFFFF; border: none; }
.stButton > button p { color: #FFFFFF; }
.stTextArea textarea {
    background-color: #FFFFFF; color: #172B4D;
    border: 1px solid #C8D6E5; border-radius: 10px;
}
.stSelectbox div[data-baseweb="select"] > div { background-color: #FFFFFF; border-radius: 10px; }

/* ---------- footer ---------- */
.footer {
    text-align: center; color: #63758B; font-size: 13px;
    border-top: 1px solid #DCE5F1; padding-top: 20px; margin-top: 35px;
}
</style>
"""

st.markdown(
    CSS.replace("__SIDEBAR_BG__", sidebar_uri).replace("__BANNER__", banner_uri),
    unsafe_allow_html=True,
)


# ==================================================
# LOAD KNOWLEDGE BASE
# ==================================================

@st.cache_resource
def load_knowledge_base():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


try:
    knowledge_base = load_knowledge_base()
except FileNotFoundError:
    st.error(f"Knowledge base not found at: {DATA_FILE}")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"knowledge_base.json is not valid JSON: {e}")
    st.stop()


# ==================================================
# LOAD MULTILINGUAL MODEL
# ==================================================

@st.cache_resource(show_spinner="Loading language model...")
def load_model():
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


model = load_model()


# ==================================================
# SEMANTIC SEARCH
# ==================================================

@st.cache_resource(show_spinner=False)
def get_index(language):
    items = [i for i in knowledge_base if i.get("language") == language]
    if not items:
        return [], None
    embeddings = model.encode([i["question"] for i in items], convert_to_tensor=True)
    return items, embeddings


def find_answer(question, language, threshold=0.60):
    items, embeddings = get_index(language)
    if not items:
        return None

    query_embedding = model.encode(question, convert_to_tensor=True)
    similarities = util.cos_sim(query_embedding, embeddings)[0]

    best_index = similarities.argmax().item()
    best_score = similarities[best_index].item()

    return items[best_index] if best_score >= threshold else None


# ==================================================
# SPEECH TO TEXT / TEXT TO SPEECH
# ==================================================

def convert_speech_to_text(audio_bytes, language):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language=SPEECH_CODES[language])
    except sr.UnknownValueError:
        return None
    except Exception:
        return "SERVICE_ERROR"


@st.cache_data(show_spinner=False)
def convert_text_to_speech(text, language):
    buffer = io.BytesIO()
    gTTS(text=text, lang=TTS_CODES[language]).write_to_fp(buffer)
    return buffer.getvalue()


# ==================================================
# NAVIGATION STATE
# ==================================================

if "page" not in st.session_state:
    slug = st.query_params.get("page", "home")
    st.session_state["page"] = SLUG_TO_LABEL.get(slug, "🏠  Home")


def sync_url():
    st.query_params["page"] = PAGES[st.session_state["page"]]


def go_to_assistant():
    st.session_state["page"] = "🌱  Agricultural Assistant"
    st.query_params["page"] = "assistant"


def use_sample(text):
    st.session_state["question_input"] = text
    st.session_state["last_answer"] = None


current_slug = PAGES[st.session_state["page"]]


# ==================================================
# SIDEBAR
# ==================================================

render_html("""
<div class="sb-brand">
  <div class="sb-logo">🌾</div>
  <div class="sb-name">KiSaanarthi</div>
  <div class="sb-tag">Agricultural Support Portal</div>
</div>
<div class="sb-line"></div>
""", target=st.sidebar)

page = st.sidebar.radio(
    "Navigation",
    list(PAGES.keys()),
    key="page",
    on_change=sync_url,
    label_visibility="collapsed",
)

render_html("""
<div class="sb-line"></div>
<div class="sb-section">Language Support</div>
<span class="lang-chip">🌐&nbsp; English</span>
<span class="lang-chip">🧡&nbsp; Hindi / हिंदी</span>
<span class="lang-chip">💜&nbsp; Marathi / मराठी</span>
<div class="sb-foot">KiSaanarthi | Academic Project Prototype</div>
""", target=st.sidebar)


# ==================================================
# HEADER BANNER + TOP NAV
# ==================================================

render_html("""
<div class="brand-header">
  <div class="brand-art"></div>
  <div class="brand-chars">🧑‍🌾🐂🐂</div>
  <div class="brand-text">
    <div class="brand-title">🌾 KiSaanarthi</div>
    <div class="brand-subtitle">Your Voice-First Multilingual Agricultural Assistant</div>
    <div class="brand-hindi">किसान की सहायता • किसान की भाषा में</div>
  </div>
</div>
""")

nav_items = []
for text, slug in TOP_NAV:
    cls = "active" if slug == current_slug else ""
    nav_items.append(f'<a class="{cls}" href="?page={quote(slug)}" target="_self">{text}</a>')
render_html(
    '<div class="nav-bar">'
    + '<span class="nav-sep">|</span>'.join(nav_items)
    + "</div>"
)


# ==================================================
# HOME PAGE
# ==================================================

if page == "🏠  Home":

    render_html("""
    <div class="welcome-card">
      <div class="welcome-title">Welcome to KiSaanarthi</div>
      <div class="welcome-sub">Your Voice-First Multilingual Agricultural Assistant</div>
      <div class="welcome-desc">Get agricultural information using your voice or text in your preferred language.</div>
    </div>
    <div class="section-title">Our Services</div>
    """)

    cards = [
        ("🌱", "#E3F5DA", "Crop Guidance", "Get information about crop cultivation and farming practices."),
        ("🌦️", "#DDF0FC", "Weather Information", "Explore weather-related agricultural information."),
        ("📊", "#ECE6FA", "Mandi Prices", "Access agricultural market price information."),
        ("📋", "#FFE9D2", "Government Schemes", "Explore information about agricultural support schemes."),
        ("🎙️", "#DCE8FD", "Voice Assistance", "Ask agricultural questions using your preferred language."),
        ("🔤", "#D9F3E4", "Multilingual Support", "Interact in English, Hindi and Marathi."),
    ]

    for start in (0, 3):
        cols = st.columns(3, gap="medium")
        for col, (icon, tint, title, desc) in zip(cols, cards[start:start + 3]):
            with col:
                render_html(f"""
                <div class="svc-card">
                  <div class="svc-icon" style="background:{tint};">{icon}</div>
                  <div>
                    <div class="svc-title">{title}</div>
                    <p class="svc-desc">{desc}</p>
                  </div>
                </div>
                """)

    st.write("")
    st.button("🌱 Open Agricultural Assistant", on_click=go_to_assistant)


# ==================================================
# AGRICULTURAL ASSISTANT
# ==================================================

elif page == "🌱  Agricultural Assistant":

    render_html("""
    <div class="welcome-card">
      <div class="welcome-title">🌾 Agricultural Assistant</div>
      <div class="welcome-sub">Ask your farming questions in English, Hindi or Marathi.</div>
    </div>
    """)

    language = st.selectbox("🌐 Select Your Preferred Language", LANGUAGES)

    st.write("")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_html("""
        <div class="input-panel">
          <h3>🎙️ Ask Using Your Voice</h3>
          <p>Record your farming question. Our system will convert your speech into text.</p>
        </div>
        """)

        audio = mic_recorder(
            start_prompt="🎙️ Start Recording",
            stop_prompt="⏹️ Stop Recording",
            key="recorder",
            format="wav",
        )

        if audio:
            st.audio(audio["bytes"], format="audio/wav")

            if st.button("Convert Voice to Text", key="convert_voice"):
                with st.spinner("Recognizing your speech..."):
                    recognized = convert_speech_to_text(audio["bytes"], language)

                if recognized == "SERVICE_ERROR":
                    st.error("Speech recognition service unavailable. Check your internet connection.")
                elif recognized:
                    st.session_state["question_input"] = recognized
                    st.session_state["last_answer"] = None
                    st.success("Speech converted successfully! See the text box.")
                else:
                    st.error("Could not understand your audio. Please try again.")

    with col2:
        render_html("""
        <div class="input-panel">
          <h3>⌨️ Type Your Question</h3>
          <p>Enter your agricultural question below.</p>
        </div>
        """)

        question = st.text_area(
            "Your Question",
            placeholder="Example: How often should I irrigate wheat?",
            height=130,
            key="question_input",
        )

    st.write("")

    if st.button("🔍 Get Agricultural Answer", use_container_width=True):
        if question.strip():
            with st.spinner("Searching the agricultural knowledge base..."):
                result = find_answer(question, language)

            if result:
                st.session_state["last_answer"] = {"item": result, "language": language}
                st.success("Relevant information found!")
            else:
                st.session_state["last_answer"] = None
                st.warning(
                    "Sorry, we could not find a sufficiently relevant answer. "
                    "Please consult an agricultural expert or KVK."
                )
        else:
            st.error("Please enter or record your question first.")

    saved = st.session_state.get("last_answer")

    if saved:
        result = saved["item"]
        answer_language = saved["language"]
        answer_html = html.escape(result["answer"]).replace("\n", "<br>")

        render_html(f"""
        <div class="answer-card">
          <h3>🌱 Agricultural Advice</h3>
          <p>{answer_html}</p>
        </div>
        """)

        st.caption(
            f"Category: {result.get('category', 'General')} | "
            f"Source: {result.get('source', 'Prototype Knowledge Base')}"
        )

        st.divider()
        st.subheader("🔊 Listen to the Answer")

        try:
            with st.spinner("Generating voice response..."):
                speech_audio = convert_text_to_speech(result["answer"], answer_language)
            st.audio(speech_audio, format="audio/mp3")
        except Exception:
            st.error("Unable to generate audio. Please check your internet connection.")

    st.divider()
    st.subheader("💡 Example Questions")
    st.write("Try these questions to explore the assistant.")

    samples = [
        "How often should I water wheat crops?",
        "Why should farmers check weather forecasts?",
        "How can I improve crop irrigation?",
    ]

    for i, sample in enumerate(samples):
        st.button("🌾 " + sample, key=f"sample_{i}", on_click=use_sample, args=(sample,))


# ==================================================
# OTHER PAGES
# ==================================================

elif page == "⛅  Weather Information":
    st.title("⛅ Live Weather Information")
    st.write(
        "Check current weather conditions and the 7-day forecast for your location. "
        "Weather data is provided by Open-Meteo."
    )

    @st.cache_data(ttl=1800, show_spinner=False)
    def get_weather(city_name):
        """Get city coordinates and a 7-day forecast from Open-Meteo."""
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_name, "count": 1, "language": "en", "format": "json"},
            timeout=15,
        )
        geo_response.raise_for_status()
        locations = geo_response.json().get("results", [])
        if not locations:
            return None

        place = locations[0]
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,wind_speed_10m,weather_code"
                ),
                "daily": (
                    "temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,weather_code"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=15,
        )
        weather_response.raise_for_status()
        return {
            "place": place,
            "weather": weather_response.json(),
        }

    def weather_description(code):
        """Convert a WMO weather code into a readable description."""
        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with heavy hail",
        }
        return descriptions.get(code, "Weather conditions unavailable")

    with st.form("weather_search_form"):
        city = st.text_input(
            "Enter city or town",
            value="Pune",
            placeholder="For example: Pune, Nashik, Nagpur",
        )
        weather_submitted = st.form_submit_button(
            "🌤️ Get Weather",
            use_container_width=True,
        )

    if weather_submitted:
        if not city.strip():
            st.warning("Please enter a city or town.")
        else:
            try:
                with st.spinner(f"Fetching weather for {city.strip()}..."):
                    weather_result = get_weather(city.strip())
                if weather_result is None:
                    st.session_state["weather_result"] = None
                    st.warning("Location not found. Please check the spelling and try again.")
                else:
                    st.session_state["weather_result"] = weather_result
            except requests.RequestException as error:
                st.error(
                    "Unable to retrieve weather data. Please check your internet "
                    f"connection and try again. Details: {error}"
                )
            except (KeyError, ValueError):
                st.error("The weather service returned an unexpected response. Please try again.")

    result = st.session_state.get("weather_result")
    if result:
        place = result["place"]
        data = result["weather"]
        current = data.get("current", {})
        daily = data.get("daily", {})

        place_parts = [place.get("name", city)]
        if place.get("admin1"):
            place_parts.append(place["admin1"])
        if place.get("country"):
            place_parts.append(place["country"])

        st.subheader("📍 " + ", ".join(place_parts))
        st.caption(
            f"Last updated: {current.get('time', 'Not available')} "
            f"({data.get('timezone', 'local time')})"
        )

        st.markdown("### Current Conditions")
        metric_cols = st.columns(4)
        metric_cols[0].metric(
            "Temperature",
            f"{current.get('temperature_2m', '—')} °C",
        )
        metric_cols[1].metric(
            "Feels Like",
            f"{current.get('apparent_temperature', '—')} °C",
        )
        metric_cols[2].metric(
            "Humidity",
            f"{current.get('relative_humidity_2m', '—')}%",
        )
        metric_cols[3].metric(
            "Wind Speed",
            f"{current.get('wind_speed_10m', '—')} km/h",
        )

        current_code = current.get("weather_code")
        if current_code is not None:
            st.info("Current conditions: " + weather_description(current_code))

        st.markdown("### 7-Day Forecast")
        forecast_rows = []
        dates = daily.get("time", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        rain = daily.get("precipitation_probability_max", [])
        codes = daily.get("weather_code", [])

        for index, date in enumerate(dates):
            code = codes[index] if index < len(codes) else None
            forecast_rows.append({
                "Date": date,
                "Condition": weather_description(code) if code is not None else "—",
                "Max (°C)": highs[index] if index < len(highs) else "—",
                "Min (°C)": lows[index] if index < len(lows) else "—",
                "Rain Chance (%)": rain[index] if index < len(rain) else "—",
            })

        if forecast_rows:
            st.dataframe(forecast_rows, use_container_width=True, hide_index=True)

        st.caption(
            "Weather data: Open-Meteo. Forecast information is general and should be "
            "considered alongside local field conditions before making farming decisions."
        )
    else:
        st.info("Enter a location and select **Get Weather** to view live conditions and forecast.")

elif page == "📊  Mandi Prices":
    st.title("📊 Agricultural Mandi Prices")
    st.write(
        "Explore reported agricultural market prices by state, district, commodity and date range. "
        "Prices are shown in ₹ per quintal where reported by the source."
    )

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_ceda_lookup(endpoint, params=None):
        response = requests.get(
            f"{CEDA_LOOKUP_BASE}/{endpoint}",
            params=params or {},
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", payload if isinstance(payload, list) else [])

    def first_value(item, possible_keys, fallback=""):
        for key in possible_keys:
            value = item.get(key)
            if value not in (None, ""):
                return value
        return fallback

    @st.cache_data(ttl=900, show_spinner=False)
    def get_ceda_prices(commodity_id, state_id, district_id, from_date, to_date):
        api_key = os.getenv("CEDA_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "CEDA_API_KEY was not found. Add CEDA_API_KEY=your_key to the .env file "
                "in the same folder as app.py, then restart Streamlit."
            )

        payload = {
            "commodity_id": int(commodity_id),
            "state_id": int(state_id),
            "district_id": [int(district_id)],
            "from_date": from_date,
            "to_date": to_date,
        }
        response = requests.post(
            CEDA_PRICES_URL,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            timeout=60,
        )

        if response.status_code == 401:
            raise RuntimeError(
                "CEDA rejected the API key. Check that the regenerated key is saved "
                "correctly in .env and restart the app."
            )
        response.raise_for_status()
        result = response.json()
        output = result.get("output", {})
        if output.get("type") == "failure":
            raise RuntimeError(output.get("message", "CEDA could not return price data."))
        return output.get("data", result.get("data", []))

    try:
        with st.spinner("Loading states and commodities from CEDA..."):
            states = get_ceda_lookup("states")
            commodities = get_ceda_lookup("commodities")

        if not states or not commodities:
            st.warning("CEDA did not return the state or commodity list. Please try again later.")
        else:
            state_options = {
                str(first_value(item, ["state_name", "census_state_name", "name", "state"])): item
                for item in states
            }
            commodity_options = {
                str(first_value(item, ["commodity_disp_name", "commodity_name", "name", "commodity"])): item
                for item in commodities
            }
            state_names = sorted(state_options.keys())
            commodity_names = sorted(commodity_options.keys())

            default_state = next(
                (name for name, item in state_options.items()
                 if int(first_value(item, ["census_state_id", "state_id"], -1)) == 27),
                state_names[0],
            )
            default_commodity = next(
                (name for name in commodity_names if name.lower() == "wheat"),
                commodity_names[0],
            )

            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                selected_state = st.selectbox(
                    "Select State", state_names,
                    index=state_names.index(default_state),
                    key="mandi_state",
                )
            with filter_col2:
                selected_commodity = st.selectbox(
                    "Select Commodity", commodity_names,
                    index=commodity_names.index(default_commodity),
                    key="mandi_commodity",
                )

            state_record = state_options[selected_state]
            state_id = first_value(state_record, ["census_state_id", "state_id", "id"])
            commodity_record = commodity_options[selected_commodity]
            commodity_id = first_value(commodity_record, ["commodity_id", "id"])

            with st.spinner(f"Loading districts in {selected_state}..."):
                districts = get_ceda_lookup("districts", {"state_id": int(state_id)})

            if not districts:
                st.warning("No districts were returned for this state.")
            else:
                district_options = {
                    str(first_value(item, [
                        "district_name", "census_district_name", "name", "district"
                    ])): item
                    for item in districts
                }
                district_names = sorted(district_options.keys())
                default_district = next(
                    (name for name, item in district_options.items()
                     if int(first_value(item, ["census_district_id", "district_id"], -1)) == 521),
                    district_names[0],
                )

                district_col, date_col1, date_col2 = st.columns([1.2, 1, 1])
                with district_col:
                    selected_district = st.selectbox(
                        "Select District", district_names,
                        index=district_names.index(default_district),
                        key=f"mandi_district_{state_id}",
                    )
                with date_col1:
                    from_date = st.date_input(
                        "From Date", value=date.today() - timedelta(days=7),
                        max_value=date.today(), key="mandi_from_date",
                    )
                with date_col2:
                    to_date = st.date_input(
                        "To Date", value=date.today(),
                        min_value=from_date, max_value=date.today(), key="mandi_to_date",
                    )

                district_record = district_options[selected_district]
                district_id = first_value(
                    district_record, ["census_district_id", "district_id", "id"]
                )

                if from_date > to_date:
                    st.error("From Date must be earlier than or equal to To Date.")
                elif st.button("🔍 Get Mandi Prices", use_container_width=True):
                    try:
                        with st.spinner("Fetching market prices from CEDA..."):
                            price_rows = get_ceda_prices(
                                commodity_id, state_id, district_id,
                                from_date.isoformat(), to_date.isoformat(),
                            )
                        st.session_state["mandi_price_rows"] = price_rows
                        st.session_state["mandi_query_label"] = (
                            f"{selected_commodity} | {selected_district}, {selected_state} "
                            f"| {from_date.isoformat()} to {to_date.isoformat()}"
                        )
                    except requests.Timeout:
                        st.error("CEDA request timed out. Please try again.")
                    except requests.RequestException as error:
                        st.error(f"Unable to retrieve mandi prices: {error}")
                    except (RuntimeError, ValueError, KeyError) as error:
                        st.error(str(error))

                if "mandi_price_rows" in st.session_state:
                    rows = st.session_state["mandi_price_rows"]
                    st.divider()
                    st.subheader("Market Price Results")
                    st.caption(st.session_state.get("mandi_query_label", ""))

                    if rows:
                        display_rows = []
                        for row in rows:
                            display_rows.append({
                                "Date": str(row.get("date", ""))[:10],
                                "Market ID": row.get("market_id", "—"),
                                "Minimum Price (₹/quintal)": row.get("min_price", "—"),
                                "Maximum Price (₹/quintal)": row.get("max_price", "—"),
                                "Modal Price (₹/quintal)": row.get("modal_price", "—"),
                            })
                        st.dataframe(
                            display_rows, use_container_width=True, hide_index=True
                        )
                        valid_modal = [
                            float(row["modal_price"]) for row in display_rows
                            if isinstance(row["modal_price"], (int, float))
                        ]
                        if valid_modal:
                            metric1, metric2, metric3 = st.columns(3)
                            metric1.metric("Lowest Modal Price", f"₹{min(valid_modal):,.0f}")
                            metric2.metric("Highest Modal Price", f"₹{max(valid_modal):,.0f}")
                            metric3.metric("Average Modal Price", f"₹{sum(valid_modal)/len(valid_modal):,.0f}")
                        st.caption(
                            "Source: CEDA Agmarknet agricultural market data. "
                            "Market ID is shown because a market-name lookup has not been configured."
                        )
                    else:
                        st.info(
                            "No price records were found for this selection and date range. "
                            "Try another commodity, district or date range."
                        )

    except requests.RequestException as error:
        st.error(f"Unable to load CEDA lookup data: {error}")

elif page == "📋  Government Schemes":
    st.title("📋 Agricultural Government Schemes")
    st.write(
        "Explore selected agricultural support schemes and open their official portals "
        "for current eligibility, application windows and guidelines."
    )

    schemes = [
        {
            "name": "PM-KISAN",
            "full": "Pradhan Mantri Kisan Samman Nidhi",
            "category": "Income Support",
            "summary": "Provides eligible farmer families financial support of ₹6,000 per year in three equal instalments through Direct Benefit Transfer, subject to scheme exclusions and verification.",
            "link": "https://pmkisan.gov.in/",
            "button": "Open PM-KISAN Portal",
        },
        {
            "name": "PMFBY",
            "full": "Pradhan Mantri Fasal Bima Yojana",
            "category": "Crop Insurance",
            "summary": "Crop insurance support for notified crops and areas against specified risks. Availability, enrolment dates and applicable premium depend on the notified season, crop and location.",
            "link": "https://pmfby.gov.in/",
            "button": "Open Crop Insurance Portal",
        },
        {
            "name": "Kisan Credit Card (KCC)",
            "full": "Agricultural Credit Facility",
            "category": "Farm Credit",
            "summary": "Facilitates access to institutional credit for eligible farmers for cultivation and certain allied activities. Contact a participating bank for current limits, interest terms and documents.",
            "link": "https://pmkisan.gov.in/",
            "button": "View KCC Information",
        },
        {
            "name": "PMKSY",
            "full": "Pradhan Mantri Krishi Sinchayee Yojana",
            "category": "Irrigation & Water Use",
            "summary": "Supports irrigation development and improved water-use efficiency. Relevant components and assistance are implemented through government departments and state-level arrangements.",
            "link": "https://pmksy.mowr.gov.in/",
            "button": "Open PMKSY Portal",
        },
        {
            "name": "Soil Health Card",
            "full": "Soil Health & Fertility",
            "category": "Soil Testing",
            "summary": "Provides soil nutrient information and recommendations to help farmers make informed decisions about fertilisers and soil amendments based on soil test results.",
            "link": "https://soilhealth.dac.gov.in/",
            "button": "Open Soil Health Card Portal",
        },
        {
            "name": "e-NAM",
            "full": "National Agriculture Market",
            "category": "Agricultural Marketing",
            "summary": "An electronic trading platform connecting participating APMC mandis to support transparent agricultural marketing and price discovery. Participation depends on the mandi and commodity.",
            "link": "https://enam.gov.in/",
            "button": "Open e-NAM Portal",
        },
    ]

    search_text = st.text_input("🔎 Search schemes", placeholder="Search by scheme name or category")
    categories = ["All"] + sorted({item["category"] for item in schemes})
    selected_category = st.selectbox("Filter by category", categories)
    filtered_schemes = [
        item for item in schemes
        if (selected_category == "All" or item["category"] == selected_category)
        and (search_text.strip().lower() in (item["name"] + " " + item["full"] + " " + item["category"] + " " + item["summary"]).lower())
    ]

    if filtered_schemes:
        for start in range(0, len(filtered_schemes), 2):
            columns = st.columns(2, gap="large")
            for column, item in zip(columns, filtered_schemes[start:start + 2]):
                with column:
                    with st.container(border=True):
                        st.subheader(item["name"])
                        st.caption(f"{item['full']} · {item['category']}")
                        st.write(item["summary"])
                        st.link_button(item["button"], item["link"], use_container_width=True)
    else:
        st.info("No schemes match your search. Try another name or category.")

    st.warning(
        "Important: This page is an informational project feature, not an eligibility checker. "
        "Scheme rules, benefits, documents and application dates can change. Confirm the latest "
        "details on the linked official portal or with your agriculture office/bank before applying."
    )
    st.caption("Scheme information reviewed against official government scheme portals and published government references. Links open external websites.")

elif page == "🌿  Crop Guidance":
    st.title("🌿 Crop Guidance")
    st.write(
        "Browse introductory cultivation information for selected crops. Choose a crop "
        "to view its general growing conditions and key management points."
    )

    crop_guides = {
        "Wheat": {
            "season": "Rabi",
            "climate": "A cool growing period and relatively dry, sunny weather during grain maturation are generally favourable.",
            "soil": "Well-drained, fertile loamy soils are commonly suitable. Avoid waterlogged fields.",
            "sowing": "Use locally recommended varieties and sowing windows for your district. Prepare a level, well-prepared seedbed and use certified seed where available.",
            "water": "Keep soil moisture adequate during establishment, crown-root initiation, flowering and grain development. Avoid both moisture stress and waterlogging.",
            "nutrients": "Base fertiliser decisions on a soil test and the locally recommended package of practices. Apply nutrients at the recommended crop stages; do not use a blanket dose.",
            "monitor": "Regularly inspect for weeds, aphids, rust and other locally prevalent diseases. Use integrated pest management and seek local advice before applying pesticides.",
        },
        "Rice": {
            "season": "Kharif (also grown in other seasons where irrigation and local conditions permit)",
            "climate": "Warm, humid conditions and a reliable water supply are generally favourable.",
            "soil": "Clayey or clay-loam soils with good water-holding capacity are often used; suitability depends on the production system.",
            "sowing": "Choose a locally recommended variety and establish the crop by the locally suitable transplanting or direct-seeding method.",
            "water": "Manage water according to crop stage, soil type and the chosen production method. Avoid uncontrolled continuous flooding and ensure drainage when needed.",
            "nutrients": "Use soil-test-based nutrient management and split applications as recommended locally. Avoid excess nitrogen, which can increase lodging and pest pressure.",
            "monitor": "Watch for stem borer, planthoppers, blast and bacterial leaf diseases. Monitor fields regularly and follow local integrated pest-management guidance.",
        },
        "Cotton": {
            "season": "Kharif",
            "climate": "A warm, frost-free growing period is generally required. Weather and soil drainage strongly affect crop performance.",
            "soil": "Deep, well-drained soils are commonly preferred. Avoid fields with prolonged waterlogging.",
            "sowing": "Select an approved variety or hybrid suited to the local agro-climatic zone and follow the recommended sowing window and spacing.",
            "water": "Provide moisture during critical growth and flowering/boll development stages while preventing waterlogging. Irrigation needs vary with rainfall and soil.",
            "nutrients": "Base nutrient application on soil testing and state recommendations. Avoid excess nitrogen and follow the recommended split schedule.",
            "monitor": "Scout regularly for sucking pests and bollworms, and conserve beneficial insects. Use only approved crop-protection products as per label and local advisories.",
        },
        "Soybean": {
            "season": "Kharif",
            "climate": "A warm growing season with well-distributed rainfall is generally suitable; standing water can damage the crop.",
            "soil": "Well-drained loam to clay-loam soils are commonly suitable. Good drainage is important.",
            "sowing": "Sow within the locally recommended monsoon window using a suitable variety and quality seed. Follow local guidance on seed treatment and inoculation.",
            "water": "Avoid waterlogging and monitor moisture around flowering and pod development, especially during dry spells.",
            "nutrients": "Use soil-test-based fertiliser recommendations. Follow local guidance for phosphorus, sulphur and bio-inoculants; avoid unnecessary nitrogen application.",
            "monitor": "Inspect for girdle beetle, stem fly, defoliators and major foliar diseases. Remove or manage affected plants according to local extension advice.",
        },
        "Sugarcane": {
            "season": "Planting windows vary by region (commonly autumn or spring in Maharashtra and other states).",
            "climate": "A long, warm growing period with adequate moisture is generally needed.",
            "soil": "Deep, fertile, well-drained soils support root development. Salinity and waterlogging can reduce crop performance.",
            "sowing": "Use healthy, disease-free setts from a reliable source and varieties recommended for the region. Follow locally advised sett treatment and row spacing.",
            "water": "Irrigation scheduling depends on soil, rainfall and growth stage. Use efficient methods where feasible and avoid prolonged waterlogging.",
            "nutrients": "Apply nutrients according to soil testing, variety, planting season and state recommendations. Split applications and earthing-up should follow local guidance.",
            "monitor": "Monitor for early shoot borer, internode borer, red rot and smut. Use clean planting material and seek local diagnosis when symptoms appear.",
        },
        "Tomato": {
            "season": "Can be grown in multiple seasons depending on local temperature, rainfall and irrigation availability.",
            "climate": "Moderate temperatures are generally favourable; extreme heat, cold and high humidity can affect flowering and fruit set.",
            "soil": "Well-drained, fertile loam with adequate organic matter is commonly suitable.",
            "sowing": "Use healthy seedlings of a locally recommended variety. Transplant at the locally advised age and spacing.",
            "water": "Maintain even soil moisture, particularly during flowering and fruit development. Avoid water stress and wetting foliage where disease pressure is high.",
            "nutrients": "Use soil-test-based nutrient management and locally recommended split applications. Avoid excessive nitrogen, which can favour vegetative growth over fruiting.",
            "monitor": "Scout for fruit borer, whiteflies, leaf curl symptoms and early/late blight. Remove diseased plant material where advised and use integrated pest management.",
        },
    }

    crop_name = st.selectbox("Select a crop", list(crop_guides.keys()))
    guide = crop_guides[crop_name]

    st.subheader(f"🌱 {crop_name} – Cultivation Overview")
    st.caption(f"Typical season: {guide['season']}")

    overview_left, overview_right = st.columns(2, gap="large")
    with overview_left:
        with st.container(border=True):
            st.markdown("#### 🌦️ Climate")
            st.write(guide["climate"])
            st.markdown("#### 🪴 Soil")
            st.write(guide["soil"])
            st.markdown("#### 🌾 Sowing & Establishment")
            st.write(guide["sowing"])
            st.markdown("#### 💧 Irrigation")
            st.write(guide["water"])
    with overview_right:
        with st.container(border=True):
            st.markdown("#### 🧪 Nutrient Management")
            st.write(guide["nutrients"])
            st.markdown("#### 🔎 Pest & Disease Monitoring")
            st.write(guide["monitor"])
            st.markdown("#### 📌 Good Practice")
            st.write(
                "Keep field records, inspect crops regularly, use quality seed and follow "
                "integrated crop management practices suited to your location."
            )

    st.warning(
        "This is general educational guidance, not a field-specific recommendation. "
        "Varieties, sowing dates, fertiliser quantities, irrigation schedules and pest-control "
        "measures depend on district, soil test, weather and current advisories. Confirm "
        "decisions with your local Krishi Vigyan Kendra (KVK) or agriculture department."
    )
    st.markdown("#### 🔗 Further Agricultural Resources")
    resource_col1, resource_col2 = st.columns(2)
    with resource_col1:
        st.link_button("ICAR – Agricultural Research", "https://icar.org.in/", use_container_width=True)
    with resource_col2:
        st.link_button("Maharashtra Agriculture Department", "https://krishi.maharashtra.gov.in/", use_container_width=True)

elif page == "ℹ️  About KiSaanarthi":
    st.title("🌾 About KiSaanarthi")
    st.markdown("""
**KiSaanarthi** is a Voice-First Multilingual Agricultural Assistant designed to make
agricultural information more accessible to farmers.

The application allows users to ask agricultural questions using voice or text.

### Key Features

- Multilingual interaction.
- Voice-to-text conversion.
- Semantic search using multilingual embeddings.
- Knowledge-base-based agricultural responses.
- Text-to-speech output.

### Supported Languages

- English
- Hindi
- Marathi

**Project Status:** Academic Prototype
""")


# ==================================================
# FOOTER
# ==================================================

render_html("""
<div class="footer">
  <div style="font-size:25px;">🌾 🧑‍🌾 🐂</div>
  <b>KiSaanarthi</b><br>
  Your Voice-First Multilingual Agricultural Assistant
  <br><br>
  Academic Project Prototype | Digital Agricultural Assistance
  <br>
  © 2026 KiSaanarthi
</div>
""")