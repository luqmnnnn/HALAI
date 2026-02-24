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
                    st.error("CONFIG ERROR: Your 'private_key' in Secrets contains an '@' symbol.")
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
        st.error("Firebase credentials not found.")
db = firestore.client()


# --- LOGO HELPER ---
def get_logo_base64(path="logohalai.jpg"):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = path.rsplit(".", 1)[-1].lower()
        mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
        return f"data:{mime};base64,{data}"
    return None

LOGO_SRC = get_logo_base64("logohalai.jpg")


# --- SVG ICON HELPER ---
def icon(name, size=16, color="currentColor"):
    paths = {
        "smartphone":     '<rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>',
        "shield":         '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        "upload-cloud":   '<polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>',
        "scan":           '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/>',
        "bar-chart":      '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
        "share-2":        '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>',
        "list":           '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
        "flag":           '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
        "send":           '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
        "info":           '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
        "zap":            '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
        "x-circle":       '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
        "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        "check-circle":   '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "check":          '<polyline points="20 6 9 16 4 11"/>',
        "minus-circle":   '<circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>',
        "menu":           '<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>',
    }
    inner = paths.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:middle;flex-shrink:0">'
        f'{inner}</svg>'
    )


# --- SAFE TEXT HELPER ---
# Strips ALL HTML from AI-generated text so it never breaks card rendering
def safe_text(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


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

/* ── Header / Toolbar (Star, Menu, etc.) ── */
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"], [data-testid="stHeaderActionElements"] { right: 1rem; top: 0.5rem; }

/* Target buttons in toolbar and header actions */
[data-testid="stToolbar"] button, [data-testid="stHeaderActionElements"] button {
    color: #5C4A2A !important; 
    border: 1px solid #5C4A2A !important;
    background: #FAF7F2 !important; 
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(139,105,20,0.1) !important;
}

/* Ensure SVGs are visible */
[data-testid="stToolbar"] button svg, [data-testid="stHeaderActionElements"] button svg {
    stroke: #5C4A2A !important;
}

[data-testid="stToolbar"] button:hover, [data-testid="stHeaderActionElements"] button:hover {
    border-color: #5C4A2A !important;
    background: #E8CC7A !important;
    color: #2C1F0A !important;
}

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
    color: #D4AA55 !important; font-size: 0.72rem !important;
    text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600;
}

/* ── Sidebar logo ── */
.sidebar-logo { display: flex; align-items: center; gap: 10px; padding: 0.25rem 0 0.5rem 0; }
.sidebar-logo img { width: 46px; height: 46px; border-radius: 10px; object-fit: cover; border: 1px solid rgba(184,146,42,0.3); }
.sidebar-brand { font-family: 'Cormorant Garamond', serif !important; font-size: 1.4rem !important; font-weight: 700 !important; color: #E8CC7A !important; letter-spacing: 0.06em; line-height: 1; }
.sidebar-tagline { font-size: 0.62rem !important; color: #8B7355 !important; text-transform: uppercase; letter-spacing: 0.14em; margin-top: 2px; }
.sidebar-nav-item { display: flex; align-items: flex-start; gap: 10px; padding: 0.5rem 0; color: #C8B48A; font-size: 0.83rem; line-height: 1.5; }
.sidebar-nav-item svg { margin-top: 2px; flex-shrink: 0; }
.sidebar-nav-num { font-family: 'Cormorant Garamond', serif; font-size: 0.95rem; font-weight: 700; color: #D4AA55; line-height: 1; min-width: 16px; }
.risk-row { display: flex; align-items: center; gap: 10px; padding: 0.45rem 0.6rem; border-radius: 7px; margin-bottom: 4px; font-size: 0.8rem; font-weight: 500; }
.risk-row.haram   { background: rgba(180,40,40,0.18);  color: #F5A0A0; }
.risk-row.syubhah { background: rgba(184,146,42,0.18); color: #E8CC7A; }
.risk-row.halal   { background: rgba(45,138,80,0.18);  color: #86EFAC; }

/* ── Mobile sidebar toggle hint ── */
.mobile-sidebar-hint {
    display: none;
    background: rgba(184,146,42,0.1);
    border: 1px solid rgba(184,146,42,0.25);
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 1rem;
    font-size: 0.78rem;
    color: #8B6914;
    align-items: center;
    gap: 8px;
}
@media (max-width: 768px) {
    .mobile-sidebar-hint { display: flex !important; }
}
/* ── Sidebar collapse/expand button ── */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button {
    background: #FAF7F2 !important;
    border: 1px solid #5C4A2A !important;
    border-radius: 8px !important;
    color: #5C4A2A !important;
    box-shadow: 0 2px 6px rgba(139,105,20,0.1) !important;
}
[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="stSidebarCollapsedControl"] button svg {
    fill: #5C4A2A !important;
    stroke: #5C4A2A !important;
}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {
    background: #E8CC7A !important;
    color: #2C1F0A !important;
    border-color: #5C4A2A !important;
}

/* ── Hero ── */
.hero-section {
    padding: 1.5rem 0 1.2rem 0;
    display: flex; align-items: center; gap: 1.2rem;
    border-bottom: 1px solid rgba(139,105,20,0.15);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.hero-logo img { width: 72px; height: 72px; border-radius: 14px; object-fit: contain; box-shadow: 0 4px 24px rgba(139,105,20,0.18); border: 1px solid rgba(184,146,42,0.25); }
.hero-logo-fallback { width: 72px; height: 72px; border-radius: 14px; background: linear-gradient(135deg, #2C1F0A, #5C3A10); display: flex; align-items: center; justify-content: center; font-size: 2rem; box-shadow: 0 4px 24px rgba(139,105,20,0.18); }
.badge { display: inline-flex; align-items: center; gap: 5px; background: rgba(139,105,20,0.1); border: 1px solid rgba(184,146,42,0.35); color: #8B6914; font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; padding: 2px 9px; border-radius: 20px; margin-bottom: 0.4rem; }
.hero-title { font-family: 'Cormorant Garamond', serif; font-size: 2.6rem; font-weight: 700; letter-spacing: 0.06em; line-height: 1; background: linear-gradient(135deg, #8B6914 0%, #D4AA55 45%, #B8922A 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0 0 0.15rem 0; }
.hero-sub { font-size: 1.4rem; color: #8B6914; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 700; }
.hero-desc { color: #5C4A2A; font-size: 1.25rem; margin-top: 0.8rem; font-weight: 500; line-height: 1.4; max-width: 650px; }

/* ── Section label ── */
.section-label { font-size: 1.4rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #8B6914; margin-bottom: 1.0rem; display: flex; align-items: center; gap: 10px; }
.section-label::before { content: ''; display: inline-block; width: 18px; height: 1.5px; background: linear-gradient(90deg, #B8922A, #E8CC7A); border-radius: 2px; }

/* ── File uploader ── */
[data-testid="stFileUploader"] { background: rgba(245,240,232,0.5) !important; border: 2px dashed rgba(184,146,42,0.35) !important; border-radius: 12px !important; }
[data-testid="stFileUploader"]:hover { border-color: rgba(184,146,42,0.6) !important; }
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span { color: #8B7355 !important; }
[data-testid="stFileUploader"] button { color: #5C4A2A !important; }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8B6914, #D4AA55) !important;
    color: #FAF7F2 !important; border: none !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important;
    font-size: 0.88rem !important; letter-spacing: 0.05em !important;
    box-shadow: 0 4px 16px rgba(139,105,20,0.25) !important; transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 8px 24px rgba(139,105,20,0.35) !important; }
.stButton > button:not([kind="primary"]),
[data-testid="stFormSubmitButton"] > button {
    background: rgba(245,240,232,0.9) !important; color: #5C4A2A !important;
    border: 1px solid rgba(184,146,42,0.3) !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
}
.stButton > button:not([kind="primary"]):hover,
[data-testid="stFormSubmitButton"] > button:hover { border-color: rgba(184,146,42,0.6) !important; background: #FAF7F2 !important; color: #2C1F0A !important; }
[data-testid="stLinkButton"] a { background: #FAF7F2 !important; color: #5C4A2A !important; border: 1px solid #B8922A !important; border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important; font-weight: 700 !important; transition: all 0.2s ease !important; box-shadow: 0 2px 5px rgba(139,105,20,0.1) !important; }
[data-testid="stLinkButton"] a:hover { background: #E8CC7A !important; color: #2C1F0A !important; border-color: #8B6914 !important; }

/* ── Metrics ── */
[data-testid="stMetric"] { background: rgba(255,252,245,0.85) !important; border: 1px solid rgba(184,146,42,0.2) !important; border-radius: 12px !important; padding: 1rem 1.25rem !important; box-shadow: 0 1px 8px rgba(139,105,20,0.06) !important; }
[data-testid="stMetricLabel"] { color: #8B7355 !important; font-size: 0.66rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.12em !important; }
[data-testid="stMetricValue"] { color: #2C1F0A !important; font-size: 2rem !important; font-weight: 700 !important; font-family: 'Cormorant Garamond', serif !important; }

/* ── Verdict cards ── */
.verdict-haram { background: #FFF5F5; border: 1px solid rgba(200,80,80,0.25); border-left: 4px solid #C94040; border-radius: 10px; padding: 1rem 1.2rem; color: #7A2020; }
.verdict-syubhah { background: #FFFBF0; border: 1px solid rgba(184,146,42,0.3); border-left: 4px solid #B8922A; border-radius: 10px; padding: 1rem 1.2rem; color: #5C3A00; }
.verdict-halal { background: #F5FFF8; border: 1px solid rgba(50,160,90,0.25); border-left: 4px solid #2D8A50; border-radius: 10px; padding: 1rem 1.2rem; color: #1A4D2E; }
.verdict-title { font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; font-weight: 700; margin-bottom: 0.3rem; display: flex; align-items: center; gap: 8px; }
.verdict-body { font-size: 1.1rem; opacity: 0.95; line-height: 1.5; }

/* ── Ingredient cards ──
   NOTE: Each card section (header, context, desc) is rendered as a
   SEPARATE st.markdown() call — this avoids mobile HTML rendering bugs
   where multi-line f-strings with dynamic content get escaped.        ── */
.ing-card-wrap {
    background: rgba(255,252,245,0.9);
    border: 1px solid rgba(184,146,42,0.12);
    border-radius: 9px;
    padding: 0.8rem 1rem 0.6rem 1rem;
    margin-bottom: 0.55rem;
    transition: box-shadow 0.15s ease;
}
.ing-card-wrap:hover { box-shadow: 0 2px 12px rgba(139,105,20,0.1); }
.ing-card-wrap.bl-haram   { border-left: 3px solid #C94040; }
.ing-card-wrap.bl-syubhah { border-left: 3px solid #B8922A; }
.ing-card-wrap.bl-halal   { border-left: 3px solid #2D8A50; }
.ing-card-wrap.bl-unknown { border-left: 3px solid #9E8C72; }

.ing-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; }
.ing-code { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; font-weight: 600; color: #B8922A; background: rgba(184,146,42,0.09); padding: 2px 8px; border-radius: 4px; }
.ing-name { font-size: 1.1rem; font-weight: 700; color: #2C1F0A; margin-left: 0.5rem; }
.ing-status { display: inline-flex; align-items: center; gap: 5px; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.ing-status.haram   { color: #C94040; }
.ing-status.syubhah { color: #B8922A; }
.ing-status.halal   { color: #2D8A50; }
.ing-status.unknown { color: #9E8C72; }
.ing-ctx  { font-size: 0.9rem; color: #A89070; font-style: italic; margin-top: 0.3rem; display: flex; align-items: center; gap: 5px; }
.ing-desc { font-size: 1.0rem; color: #5C4A2A; margin-top: 0.3rem; line-height: 1.4; font-weight: 500; }

/* ── Placeholder ── */
.placeholder-box { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 220px; text-align: center; gap: 0.8rem; background: rgba(255,252,245,0.5); border: 2px dashed rgba(184,146,42,0.4); border-radius: 12px; padding: 2rem; }
.placeholder-text { font-size: 1.25rem; color: #8B6914; font-weight: 600; line-height: 1.4; }

/* ── Misc ── */
hr { border-color: rgba(184,146,42,0.15) !important; }
[data-testid="stExpander"] { background: rgba(255,252,245,0.7) !important; border: 1px solid rgba(184,146,42,0.15) !important; border-radius: 9px !important; }
[data-testid="stExpander"] > div, [data-testid="stExpander"] > div > div { background: #FAF7F2 !important; }
[data-testid="stExpander"] p, [data-testid="stExpander"] label, [data-testid="stExpander"] span, [data-testid="stExpander"] div { color: #2C1F0A !important; background-color: transparent !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: #5C4A2A !important; font-size: 0.83rem !important; font-weight: 500 !important; }
[data-testid="stForm"] { background: #FAF7F2 !important; border: 1px solid rgba(184,146,42,0.15) !important; border-radius: 9px !important; padding: 0.5rem !important; }
[data-testid="stForm"] p, [data-testid="stForm"] label, [data-testid="stForm"] span, [data-testid="stForm"] div { color: #2C1F0A !important; background-color: transparent !important; }
[data-testid="stToast"] { background: #FAF7F2 !important; border: 1px solid rgba(184,146,42,0.3) !important; border-radius: 10px !important; box-shadow: 0 4px 20px rgba(139,105,20,0.15) !important; }
[data-testid="stToast"] p, [data-testid="stToast"] span, [data-testid="stToast"] div { color: #2C1F0A !important; background: transparent !important; }
.stTextInput input, .stTextArea textarea { background: #FAF7F2 !important; border: 1px solid rgba(184,146,42,0.25) !important; border-radius: 7px !important; color: #2C1F0A !important; font-family: 'DM Sans', sans-serif !important; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color: #B8922A !important; box-shadow: 0 0 0 2px rgba(184,146,42,0.12) !important; }
.stTextInput label, .stTextArea label { color: #8B7355 !important; font-size: 0.78rem !important; font-weight: 500 !important; }
[data-testid="stAlert"] { border-radius: 9px !important; }
[data-testid="stImage"] img { border-radius: 10px !important; border: 1px solid rgba(184,146,42,0.15) !important; }
h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { font-family: 'Cormorant Garamond', serif !important; color: #2C1F0A !important; }
p, li { color: #3D2E14; }
.stCaption, [data-testid="stCaptionContainer"] { color: #A89070 !important; font-size: 0.73rem !important; }
.stSpinner > div { border-top-color: #B8922A !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #F5F0E8; }
::-webkit-scrollbar-thumb { background: rgba(184,146,42,0.35); border-radius: 10px; }

/* ── Mobile responsive tweaks ── */
@media (max-width: 768px) {
    .hero-title { font-size: 2rem !important; }
    .hero-desc  { font-size: 0.8rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
}
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
            <div><div class="sidebar-brand">HALAI™</div><div class="sidebar-tagline">Halal AI</div></div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-logo">
            <span style="font-size:1.8rem;">☪️</span>
            <div><div class="sidebar-brand">HALAI™</div><div class="sidebar-tagline">Halal AI</div></div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style="color:#D4AA55;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:0.6rem;display:flex;align-items:center;gap:6px;">
        {icon("smartphone", 13, "#D4AA55")} How to Use
    </div>
    <div class="sidebar-nav-item">{icon("upload-cloud",14,"#B8922A")}<span><span class="sidebar-nav-num">1</span>&nbsp; <strong>Upload</strong> a photo of the ingredients label</span></div>
    <div class="sidebar-nav-item">{icon("scan",14,"#B8922A")}<span><span class="sidebar-nav-num">2</span>&nbsp; <strong>Scan</strong> to detect E-codes &amp; additives</span></div>
    <div class="sidebar-nav-item">{icon("bar-chart",14,"#B8922A")}<span><span class="sidebar-nav-num">3</span>&nbsp; <strong>Review</strong> your safety report</span></div>
    <div style="background:rgba(184,146,42,0.1);border:1px solid rgba(184,146,42,0.25);border-radius:8px;padding:0.6rem 0.8rem;margin:0.8rem 0;display:flex;align-items:flex-start;gap:8px;color:#C8B48A;font-size:0.79rem;line-height:1.5;">
        {icon("info",14,"#D4AA55")} <span>Ensure the text in your photo is clear and in focus.</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style="color:#D4AA55;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:0.6rem;display:flex;align-items:center;gap:6px;">
        {icon("shield", 13, "#D4AA55")} Risk Levels
    </div>
    <div class="risk-row haram">{icon("x-circle",14,"#F5A0A0")} <strong>Haram</strong> — Prohibited</div>
    <div class="risk-row syubhah">{icon("alert-triangle",14,"#E8CC7A")} <strong>Syubhah</strong> — Doubtful</div>
    <div class="risk-row halal">{icon("check-circle",14,"#86EFAC")} <strong>Halal</strong> — Safe</div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:6px;color:#6B5A3E;font-size:0.7rem;">
        {icon("zap",11,"#6B5A3E")} Built for KitaHack 2026 · Team 4-midable
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════
logo_html = (
    f'<div class="hero-logo"><img src="{LOGO_SRC}" alt="HALAI Logo"></div>'
    if LOGO_SRC else '<div class="hero-logo-fallback">☪️</div>'
)

# Mobile hint banner — only visible on small screens via CSS
st.markdown(f"""
<div class="mobile-sidebar-hint">
    {icon("menu", 14, "#8B6914")}
    <span>Tap the <strong>&gt;</strong> arrow (top-left) to open the guide &amp; risk levels</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero-section">
    {logo_html}
    <div class="hero-text">
        <div class="badge">{icon("zap",11,"#8B6914")} AI-Powered &nbsp;·&nbsp; Free &nbsp;·&nbsp; Fast</div>
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
    st.markdown(f'<div class="section-label">{icon("upload-cloud",24,"#8B6914")} &nbsp;Step 1 — Upload Label</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Label Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

    if uploaded_file is not None:
        # Reset results if a new file is uploaded
        if "last_file_name" not in st.session_state or st.session_state.last_file_name != uploaded_file.name:
            st.session_state.last_file_name = uploaded_file.name
            st.session_state.results = None

        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Label", use_container_width=True)

        if st.button("Scan Ingredients", type="primary", use_container_width=True):
            with st.spinner("AI is reading the label..."):
                st.toast("Analyzing image...")
                detected_ingredients = analyze_image(image)

                if detected_ingredients is None:
                    st.session_state.results = None
                elif not detected_ingredients:
                    st.warning("No E-codes or ingredients detected. Try a clearer photo.")
                    st.session_state.results = None
                else:
                    st.toast("Checking database...")
                    status, details = check_database(detected_ingredients)
                    sort_priority = {"Haram": 1, "Syubhah": 2, "Unknown": 3, "Halal": 4}
                    details.sort(key=lambda x: sort_priority.get(x["status"], 5))
                    st.session_state.results = {"status": status, "details": details}
                    st.toast("Scan complete!")
    else:
        # Clear results if file is removed
        st.session_state.results = None
        
        st.markdown(f"""
        <div class="placeholder-box">
            <div>{icon("upload-cloud", 48, "#8B6914")}</div>
            <div class="placeholder-text">Drop a photo of your food label here<br>JPG, PNG or JPEG accepted</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="section-label">{icon("bar-chart",24,"#8B6914")} &nbsp;Step 2 — Analysis Result</div>', unsafe_allow_html=True)

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
            st.markdown(f"""
            <div class="verdict-haram">
                <div class="verdict-title">{icon("x-circle",18,"#C94040")} Haram Detected</div>
                <div class="verdict-body">This product contains prohibited ingredients. It is <strong>not permissible</strong> to consume.</div>
            </div>""", unsafe_allow_html=True)
        elif status == "Syubhah":
            st.markdown(f"""
            <div class="verdict-syubhah">
                <div class="verdict-title">{icon("alert-triangle",18,"#B8922A")} Syubhah — Doubtful</div>
                <div class="verdict-body">Contains ingredients that may be from animal sources. <strong>Look for a JAKIM Halal logo</strong> before consuming.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="verdict-halal">
                <div class="verdict-title">{icon("check-circle",18,"#2D8A50")} Likely Halal</div>
                <div class="verdict-body">No flagged ingredients detected. This product <strong>appears safe</strong> to consume.</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        share_text = f"☪️ *HALAI™ Scan Result*\n\nStatus: *{status}*\nSafety Score: {score}%\n\nCheck your food with HALAI!"
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
        st.link_button("Share Result on WhatsApp", whatsapp_url, use_container_width=True)

        st.divider()
        st.markdown(f'<div class="section-label">{icon("list",13,"#B8922A")} &nbsp;Detailed Breakdown</div>', unsafe_allow_html=True)

        # Status SVG map
        status_svg = {
            "Haram":   icon("x-circle",      13, "#C94040"),
            "Syubhah": icon("alert-triangle", 13, "#B8922A"),
            "Halal":   icon("check",          13, "#2D8A50"),
            "Unknown": icon("minus-circle",   13, "#9E8C72"),
        }

        for item in details:
            s = item["status"]
            svg = status_svg.get(s, icon("minus-circle", 13, "#9E8C72"))
            bl  = s.lower()

            # Sanitize every field individually
            t_code = safe_text(item["code"])
            t_name = safe_text(item["name"])
            t_desc = safe_text(item["description"])
            t_ctx  = safe_text(item["context"])

            # ── Card header (code + name + status) ──
            # Construct HTML without indentation to prevent Markdown code-block rendering issues
            ctx_html = f'<div class="ing-ctx">{icon("info",11,"#A89070")} {t_ctx}</div>' if t_ctx else ''
            
            st.markdown(f"""
<div class="ing-card-wrap bl-{bl}">
<div class="ing-header"><span><span class="ing-code">{t_code}</span><span class="ing-name">{t_name}</span></span><span class="ing-status {bl}">{svg} {s}</span></div>
{ctx_html}
<div class="ing-desc">{t_desc}</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Report Incorrect Info"):
            with st.form("report_form"):
                missing_item = st.text_input("Ingredient Name or Code")
                notes = st.text_area("What's wrong? / Apa masalahnya?")
                submitted = st.form_submit_button("Submit Report")
                if submitted:
                    db.collection("reports").add({
                        "item": missing_item, "notes": notes,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.toast("Report submitted! Thank you.")

    else:
        st.markdown(f"""
        <div class="placeholder-box">
            <div>{icon("bar-chart", 48, "#8B6914")}</div>
            <div class="placeholder-text">Your analysis results will appear here<br>after you upload and scan a label</div>
        </div>
        """, unsafe_allow_html=True)