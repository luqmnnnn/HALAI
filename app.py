import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from PIL import Image
import os
import json
import base64
from google.api_core import exceptions as google_exceptions
import urllib.parse

# --- 1. CONFIGURATION ---
load_dotenv()
st.set_page_config(page_title="HALAI™", page_icon="☪️", layout="wide")

# Setup Gemini AI
try:
    gemini_key = st.secrets.get("GEMINI_API_KEY")
except FileNotFoundError:
    gemini_key = None

if not gemini_key:
    gemini_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Setup Firebase
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            firebase_conf = dict(st.secrets["firebase"])
            if "private_key" in firebase_conf:
                pkey = firebase_conf["private_key"].replace("\\n", "\n").strip('"').strip("'").strip()
                if "@" in pkey:
                    st.error("🚨 CONFIG ERROR: Your 'private_key' in Secrets contains an '@' symbol.")
                    st.stop()
                firebase_conf["private_key"] = pkey
            cred = credentials.Certificate(firebase_conf)
            firebase_admin.initialize_app(cred)
    except FileNotFoundError:
        pass

    if not firebase_admin._apps and os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)

    if not firebase_admin._apps:
        st.error("🔥 Firebase credentials not found.")
db = firestore.client()


# --- LOGO HELPER ---
# Place logohalai.jpg in the same folder as app.py.
# The function reads it and embeds it as base64 so it works
# both locally and on Streamlit Cloud without any extra config.
def get_logo_base64(path="logohalai.jpg"):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = path.rsplit(".", 1)[-1].lower()
        mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
        return f"data:{mime};base64,{data}"
    return None

LOGO_SRC = get_logo_base64("logohalai.jpg")


# --- 2. CORE FUNCTIONS ---

def analyze_image(image):
    prompt = """
    Analyze this food label image.
    1. Identify ALL food additives, E-numbers (e.g., E120), INS numbers (e.g., INS 471), and suspicious ingredients (e.g., Gelatin, Lard, Emulsifiers).
    2. If an ingredient is listed by name (e.g., "Citric Acid"), try to provide its E-number in the 'code' field (e.g., "E330").
    3. Use context keywords (like "Vegetable", "Soy", "Animal") ONLY to fill the 'context' field. DO NOT list them as separate ingredients.
    4. Return the result strictly as a JSON list of objects with keys: "code" (the E-number, INS number, or name) and "context" (the surrounding text indicating source).
    5. Do not list the same ingredient twice.
    6. Do not add markdown like ```json. Just the raw JSON.

    Example Output: [{"code": "E471", "context": "Vegetable origin"}, {"code": "Gelatin", "context": ""}]
    """
    try:
        response = model.generate_content([prompt, image])
        text_output = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text_output)
    except google_exceptions.ResourceExhausted:
        st.error("AI Quota Error: You've exceeded the free request limit for today.")
        st.warning("Please wait for your quota to reset or enable billing on your Google Cloud project.")
        return None
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None


def check_database(ingredients):
    results_list = []
    overall_status = "Halal"
    seen_codes = set()
    ignore_keywords = {"VEGETABLE", "PLANT", "PLANTBASED", "SOY", "SYNTHETIC", "ANIMAL",
                       "MINERAL", "FLAVOR", "COLOUR", "PRESERVATIVE", "INGREDIENTS", "CONTAINS"}

    for item_obj in ingredients:
        code_str = item_obj.get("code", "").strip()
        context = item_obj.get("context", "").strip()
        if not code_str:
            continue

        code_key = code_str.upper().replace("-", "").replace(" ", "").replace(".", "").replace("(", "").replace(")", "")
        if code_key in ignore_keywords:
            continue
        if "INS" in code_key:
            code_key = code_key.replace("INS", "E")
        if code_key.isdigit():
            code_key = f"E{code_key}"
        if code_key in seen_codes:
            continue
        seen_codes.add(code_key)

        doc_ref = db.collection('ecodes').document(code_key)
        doc = doc_ref.get()

        current_status = "Unknown"
        description = "Not in database yet."
        name = code_str

        if doc.exists:
            data = doc.to_dict()
            name = data.get('name', name)
            current_status = data.get('status', 'Unknown')
            description = data.get('description', '')

        if current_status != "Haram":
            lower_context = context.lower()
            lower_name = name.lower()
            safe_keywords = ["vegetable", "plant", "soy", "synthetic", "mineral", "vegan",
                             "polyol", "gum", "cocoa", "fiber", "vanilla", "amino", "bcaa", "fermentation"]
            if any(k in lower_context for k in safe_keywords) or any(k in lower_name for k in safe_keywords):
                if current_status in ["Syubhah", "Unknown"]:
                    current_status = "Halal"
                    if description == "Not in database yet.":
                        description = "Verified as Safe by AI Context."
                    elif "(Verified as Safe by AI Context)" not in description:
                        description += " (Verified as Safe by AI Context)"

        results_list.append({"code": code_str, "name": name, "status": current_status,
                              "description": description, "context": context})

        if current_status == 'Haram':
            overall_status = "Haram"
        elif current_status == 'Syubhah' and overall_status != "Haram":
            overall_status = "Syubhah"

    return overall_status, results_list


# --- 3. THE USER INTERFACE ---

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300&family=DM+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── Background ── */
.stApp {
    background-color: #F5F0E8;
    background-image:
        radial-gradient(ellipse 70% 40% at 15% 0%,  rgba(184,146,42,0.08) 0%, transparent 55%),
        radial-gradient(ellipse 50% 35% at 85% 90%, rgba(139,105,20,0.07) 0%, transparent 50%);
}
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #2C1F0A !important;
    border-right: 1px solid rgba(184,146,42,0.2) !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #E8CC7A !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] .stMarkdown p { color: #C8B48A !important; }
[data-testid="stSidebar"] hr { border-color: rgba(184,146,42,0.25) !important; }
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #D4AA55 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-weight: 600;
}

/* ── Sidebar logo block ── */
.sidebar-logo {
    display: flex; align-items: center; gap: 10px;
    padding: 0.25rem 0 0.5rem 0;
}
.sidebar-logo img {
    width: 46px; height: 46px;
    border-radius: 10px; object-fit: cover;
    border: 1px solid rgba(184,146,42,0.3);
}
.sidebar-brand {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #E8CC7A !important;
    letter-spacing: 0.06em; line-height: 1;
}
.sidebar-tagline {
    font-size: 0.62rem !important;
    color: #8B7355 !important;
    text-transform: uppercase; letter-spacing: 0.14em; margin-top: 2px;
}

/* ── Hero ── */
.hero-section {
    padding: 2rem 0 1.5rem 0;
    display: flex; align-items: center; gap: 1.5rem;
    border-bottom: 1px solid rgba(139,105,20,0.15);
    margin-bottom: 1.5rem;
}
.hero-logo img {
    width: 88px; height: 88px;
    border-radius: 18px; object-fit: cover;
    box-shadow: 0 4px 24px rgba(139,105,20,0.18);
    border: 1px solid rgba(184,146,42,0.25);
}
.hero-logo-fallback {
    width: 88px; height: 88px; border-radius: 18px;
    background: linear-gradient(135deg, #2C1F0A, #5C3A10);
    display: flex; align-items: center; justify-content: center;
    font-size: 2.4rem;
    box-shadow: 0 4px 24px rgba(139,105,20,0.18);
}
.badge {
    display: inline-block;
    background: rgba(139,105,20,0.1);
    border: 1px solid rgba(184,146,42,0.35);
    color: #8B6914; font-size: 0.64rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 2px 10px; border-radius: 20px; margin-bottom: 0.5rem;
}
.hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 3rem; font-weight: 700;
    letter-spacing: 0.06em; line-height: 1;
    background: linear-gradient(135deg, #8B6914 0%, #D4AA55 45%, #B8922A 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0 0 0.2rem 0;
}
.hero-sub {
    font-size: 0.68rem; color: #8B7355;
    letter-spacing: 0.2em; text-transform: uppercase; font-weight: 500;
}
.hero-desc {
    color: #5C4A2A; font-size: 0.87rem;
    margin-top: 0.6rem; font-weight: 300; line-height: 1.6; max-width: 520px;
}

/* ── Section label ── */
.section-label {
    font-size: 0.64rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.16em;
    color: #B8922A; margin-bottom: 0.9rem;
    display: flex; align-items: center; gap: 8px;
}
.section-label::before {
    content: ''; display: inline-block;
    width: 18px; height: 1.5px;
    background: linear-gradient(90deg, #B8922A, #E8CC7A);
    border-radius: 2px;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(245,240,232,0.5) !important;
    border: 2px dashed rgba(184,146,42,0.35) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(184,146,42,0.6) !important; }
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span { color: #8B7355 !important; }
[data-testid="stFileUploader"] button { color: #5C4A2A !important; }

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8B6914, #D4AA55) !important;
    color: #FAF7F2 !important; border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 0.88rem !important;
    letter-spacing: 0.05em !important;
    box-shadow: 0 4px 16px rgba(139,105,20,0.25) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(139,105,20,0.35) !important;
}

/* ── Secondary / form submit buttons ── */
.stButton > button:not([kind="primary"]),
[data-testid="stFormSubmitButton"] > button {
    background: rgba(245,240,232,0.9) !important;
    color: #5C4A2A !important;
    border: 1px solid rgba(184,146,42,0.3) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}
.stButton > button:not([kind="primary"]):hover,
[data-testid="stFormSubmitButton"] > button:hover {
    border-color: rgba(184,146,42,0.6) !important;
    background: #FAF7F2 !important;
    color: #2C1F0A !important;
}

/* ── Link button ── */
[data-testid="stLinkButton"] a {
    background: rgba(139,105,20,0.08) !important;
    color: #8B6914 !important;
    border: 1px solid rgba(184,146,42,0.35) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stLinkButton"] a:hover {
    background: rgba(139,105,20,0.15) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: rgba(255,252,245,0.85) !important;
    border: 1px solid rgba(184,146,42,0.2) !important;
    border-radius: 12px !important; padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 8px rgba(139,105,20,0.06) !important;
}
[data-testid="stMetricLabel"] {
    color: #8B7355 !important; font-size: 0.66rem !important;
    font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}
[data-testid="stMetricValue"] {
    color: #2C1F0A !important; font-size: 2rem !important;
    font-weight: 700 !important;
    font-family: 'Cormorant Garamond', serif !important;
}

/* ── Verdict cards ── */
.verdict-haram {
    background: #FFF5F5; border: 1px solid rgba(200,80,80,0.25);
    border-left: 4px solid #C94040; border-radius: 10px;
    padding: 1.1rem 1.4rem; color: #7A2020;
}
.verdict-syubhah {
    background: #FFFBF0; border: 1px solid rgba(184,146,42,0.3);
    border-left: 4px solid #B8922A; border-radius: 10px;
    padding: 1.1rem 1.4rem; color: #5C3A00;
}
.verdict-halal {
    background: #F5FFF8; border: 1px solid rgba(50,160,90,0.25);
    border-left: 4px solid #2D8A50; border-radius: 10px;
    padding: 1.1rem 1.4rem; color: #1A4D2E;
}
.verdict-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.15rem; font-weight: 700; margin-bottom: 0.35rem;
}
.verdict-body { font-size: 0.83rem; opacity: 0.88; line-height: 1.65; }

/* ── Ingredient cards ── */
.ing-card {
    background: rgba(255,252,245,0.9);
    border: 1px solid rgba(184,146,42,0.12);
    border-radius: 9px; padding: 0.85rem 1rem; margin-bottom: 0.55rem;
    transition: box-shadow 0.15s ease;
}
.ing-card:hover { box-shadow: 0 2px 12px rgba(139,105,20,0.1); }
.ing-card-haram   { border-left: 3px solid #C94040; }
.ing-card-syubhah { border-left: 3px solid #B8922A; }
.ing-card-halal   { border-left: 3px solid #2D8A50; }
.ing-card-unknown { border-left: 3px solid #9E8C72; }
.ing-code {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.79rem; font-weight: 500;
    color: #B8922A; background: rgba(184,146,42,0.09);
    padding: 1px 6px; border-radius: 4px;
}
.ing-name { font-size: 0.87rem; font-weight: 600; color: #2C1F0A; margin-left: 0.5rem; }
.ing-status-haram   { color: #C94040; font-size: 0.69rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.ing-status-syubhah { color: #B8922A; font-size: 0.69rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.ing-status-halal   { color: #2D8A50; font-size: 0.69rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.ing-status-unknown { color: #9E8C72; font-size: 0.69rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.ing-desc { font-size: 0.75rem; color: #8B7355; margin-top: 0.2rem; }
.ing-ctx  { font-size: 0.72rem; color: #A89070; font-style: italic; margin-top: 0.1rem; }

/* ── Placeholder ── */
.placeholder-box {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 210px; text-align: center; gap: 0.7rem;
    background: rgba(255,252,245,0.5);
    border: 1px dashed rgba(184,146,42,0.22);
    border-radius: 12px; padding: 2rem;
}
.placeholder-icon { font-size: 2.3rem; opacity: 0.3; }
.placeholder-text { font-size: 0.81rem; color: #A89070; font-weight: 300; line-height: 1.6; }

/* ── Divider ── */
hr { border-color: rgba(184,146,42,0.15) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(255,252,245,0.7) !important;
    border: 1px solid rgba(184,146,42,0.15) !important;
    border-radius: 9px !important;
}
[data-testid="stExpander"] > div,
[data-testid="stExpander"] > div > div {
    background: #FAF7F2 !important;
}
[data-testid="stExpander"] p,
[data-testid="stExpander"] label,
[data-testid="stExpander"] span,
[data-testid="stExpander"] div {
    color: #2C1F0A !important;
    background-color: transparent !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: #5C4A2A !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    background: #FAF7F2 !important;
    border: 1px solid rgba(184,146,42,0.15) !important;
    border-radius: 9px !important;
    padding: 0.5rem !important;
}
[data-testid="stForm"] p,
[data-testid="stForm"] label,
[data-testid="stForm"] span,
[data-testid="stForm"] div {
    color: #2C1F0A !important;
    background-color: transparent !important;
}

/* ── Toast notifications ── */
[data-testid="stToast"] {
    background: #FAF7F2 !important;
    border: 1px solid rgba(184,146,42,0.3) !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 20px rgba(139,105,20,0.15) !important;
}
[data-testid="stToast"] p,
[data-testid="stToast"] span,
[data-testid="stToast"] div {
    color: #2C1F0A !important;
    background: transparent !important;
}

/* ── Text inputs ── */
.stTextInput input, .stTextArea textarea {
    background: #FAF7F2 !important;
    border: 1px solid rgba(184,146,42,0.25) !important;
    border-radius: 7px !important;
    color: #2C1F0A !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #B8922A !important;
    box-shadow: 0 0 0 2px rgba(184,146,42,0.12) !important;
}
.stTextInput label, .stTextArea label {
    color: #8B7355 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 9px !important; }

/* ── Images ── */
[data-testid="stImage"] img {
    border-radius: 10px !important;
    border: 1px solid rgba(184,146,42,0.15) !important;
}

/* ── Typography ── */
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Cormorant Garamond', serif !important;
    color: #2C1F0A !important;
}
p, li { color: #3D2E14; }
.stCaption, [data-testid="stCaptionContainer"] {
    color: #A89070 !important; font-size: 0.73rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #B8922A !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #F5F0E8; }
::-webkit-scrollbar-thumb { background: rgba(184,146,42,0.35); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    if LOGO_SRC:
        st.markdown(f"""
        <div class="sidebar-logo">
            <img src="{LOGO_SRC}" alt="HALAI Logo">
            <div>
                <div class="sidebar-brand">HALAI™</div>
                <div class="sidebar-tagline">Halal AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-logo">
            <span style="font-size:1.8rem;">☪️</span>
            <div>
                <div class="sidebar-brand">HALAI™</div>
                <div class="sidebar-tagline">Halal AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📱 How to Use")
    st.markdown("""
1. **Upload** a photo of the ingredients label
2. **Scan** to detect E-codes & additives
3. **Review** your safety report
    """)
    st.info("💡 **Tip:** Ensure the text in your photo is clear and in focus.")
    st.divider()
    st.markdown("### 🛡️ Risk Levels")
    st.error("🔴 **Haram** — Prohibited")
    st.warning("🟠 **Syubhah** — Doubtful")
    st.success("🟢 **Halal** — Safe")
    st.divider()
    st.caption("🚀 Built for KitaHack 2026 · Team 4-midable")


# ══════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════
logo_html = (
    f'<div class="hero-logo"><img src="{LOGO_SRC}" alt="HALAI Logo"></div>'
    if LOGO_SRC else
    '<div class="hero-logo-fallback">☪️</div>'
)

st.markdown(f"""
<div class="hero-section">
    {logo_html}
    <div class="hero-text">
        <div class="badge">☪ AI-Powered · Free · Fast</div>
        <h1 class="hero-title">HALAI™</h1>
        <p class="hero-sub">Halal Artificial Intelligence</p>
        <p class="hero-desc">Scan any food label — our AI detects E-codes and additives,
        then checks them against a verified Halal database in seconds.</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# MAIN COLUMNS
# ══════════════════════════════════════════════════════════════
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="section-label">Step 1 — Upload Label</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Label Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed"
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Label", use_container_width=True)

        if st.button("🔬 Scan Ingredients", type="primary", use_container_width=True):
            with st.spinner("AI is reading the label..."):
                st.toast("Analyzing image...", icon="🔍")
                detected_ingredients = analyze_image(image)

                if detected_ingredients is None:
                    st.session_state.results = None
                elif not detected_ingredients:
                    st.warning("No E-codes or ingredients detected. Try a clearer photo.")
                    st.session_state.results = None
                else:
                    st.toast("Checking database...", icon="📚")
                    status, details = check_database(detected_ingredients)
                    sort_priority = {"Haram": 1, "Syubhah": 2, "Unknown": 3, "Halal": 4}
                    details.sort(key=lambda x: sort_priority.get(x["status"], 5))
                    st.session_state.results = {"status": status, "details": details}
                    st.toast("Scan complete!", icon="✅")
    else:
        st.markdown("""
        <div class="placeholder-box">
            <div class="placeholder-icon">📷</div>
            <div class="placeholder-text">Drop a photo of your food label here<br>JPG, PNG or JPEG accepted</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-label">Step 2 — Analysis Result</div>', unsafe_allow_html=True)

    if "results" in st.session_state and st.session_state.results and uploaded_file:
        results = st.session_state.results
        status = results["status"]
        details = results["details"]

        total_items = len(details)
        safe_items = sum(1 for i in details if i["status"] == "Halal")
        score = int((safe_items / total_items) * 100) if total_items > 0 else 0

        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Safety Score", f"{score}%")
        m_col2.metric("Ingredients Found", total_items)

        st.markdown("<br>", unsafe_allow_html=True)

        if status == "Haram":
            st.markdown("""
            <div class="verdict-haram">
                <div class="verdict-title">🚨 Haram Detected</div>
                <div class="verdict-body">This product contains prohibited ingredients.
                It is <strong>not permissible</strong> to consume.</div>
            </div>""", unsafe_allow_html=True)
        elif status == "Syubhah":
            st.markdown("""
            <div class="verdict-syubhah">
                <div class="verdict-title">⚠️ Syubhah — Doubtful</div>
                <div class="verdict-body">Contains ingredients that may be from animal sources.
                <strong>Look for a JAKIM Halal logo</strong> before consuming.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="verdict-halal">
                <div class="verdict-title">✅ Likely Halal</div>
                <div class="verdict-body">No flagged ingredients detected.
                This product <strong>appears safe</strong> to consume.</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        share_text = f"☪️ *HALAI™ Scan Result*\n\nStatus: *{status}*\nSafety Score: {score}%\n\nCheck your food with HALAI!"
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
        st.link_button("📤 Share on WhatsApp", whatsapp_url, use_container_width=True)

        st.divider()
        st.markdown('<div class="section-label">Detailed Breakdown</div>', unsafe_allow_html=True)

        for item in details:
            s = item["status"]
            status_icons = {"Haram": "🔴", "Syubhah": "🟠", "Halal": "🟢", "Unknown": "⚪"}
            icon = status_icons.get(s, "⚪")

            # Sanitize all text fields — prevents HTML characters in AI output
            # from breaking the card layout and showing raw HTML as text
            safe_desc = str(item["description"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe_name = str(item["name"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe_code = str(item["code"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe_ctx  = str(item["context"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            ctx_html = f'<div class="ing-ctx">Context: {safe_ctx}</div>' if safe_ctx else ""

            st.markdown(f"""
            <div class="ing-card ing-card-{s.lower()}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span>
                        <span class="ing-code">{safe_code}</span>
                        <span class="ing-name">{safe_name}</span>
                    </span>
                    <span class="ing-status-{s.lower()}">{icon} {s}</span>
                </div>
                {ctx_html}
                <div class="ing-desc">{safe_desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🚩 Report Incorrect Info"):
            with st.form("report_form"):
                missing_item = st.text_input("Ingredient Name or Code")
                notes = st.text_area("What's wrong? / Apa masalahnya?")
                submitted = st.form_submit_button("Submit Report")
                if submitted:
                    db.collection("reports").add({
                        "item": missing_item, "notes": notes,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.toast("Report submitted! Thank you.", icon="🙏")

    else:
        st.markdown("""
        <div class="placeholder-box">
            <div class="placeholder-icon">📊</div>
            <div class="placeholder-text">Your analysis results will appear here<br>after you upload and scan a label</div>
        </div>
        """, unsafe_allow_html=True)