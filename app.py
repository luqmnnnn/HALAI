import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from PIL import Image
import os
import json
from google.api_core import exceptions as google_exceptions
import urllib.parse

# --- 1. CONFIGURATION ---
load_dotenv() # Load your .env file
st.set_page_config(page_title="HALAI™", page_icon="☪️", layout="wide")

# Setup Gemini AI (The Brain)
try:
    # Try getting key from Streamlit Secrets (Cloud)
    gemini_key = st.secrets.get("GEMINI_API_KEY")
except FileNotFoundError:
    gemini_key = None

# Fallback to .env (Local)
if not gemini_key:
    gemini_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Setup Firebase (The Validator)
# We check if it's already initialized to prevent errors when Streamlit refreshes
if not firebase_admin._apps:
    # 1. Try Streamlit Secrets (Best for Cloud)
    try:
        if "firebase" in st.secrets:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
    except FileNotFoundError:
        pass # Running locally without secrets.toml

    # 2. Try Local File (Best for Local)
    if not firebase_admin._apps and os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    
    # 3. Final Check
    if not firebase_admin._apps:
        st.error("🔥 Firebase credentials not found. Please set up secrets or add firebase_key.json.")
db = firestore.client()

# --- 2. CORE FUNCTIONS ---

def analyze_image(image):
    """
    Sends the image to Gemini and asks it to find E-codes.
    We ask for JSON format so we can process it easily.
    """
    prompt = """
    Analyze this food label image.
    1. Identify ALL food additives, E-numbers (e.g., E120), INS numbers (e.g., INS 471), and suspicious ingredients (e.g., Gelatin, Lard, Emulsifiers).
    2. If an ingredient is listed by name (e.g., "Citric Acid"), try to provide its E-number in the 'code' field (e.g., "E330").
    3. Look for context keywords like "Vegetable", "Plant-based", "Soy", "Synthetic", or "Animal".
    4. Return the result strictly as a JSON list of objects with keys: "code" (the E-number, INS number, or name) and "context" (the surrounding text indicating source).
    5. Do not add markdown like ```json. Just the raw JSON.
    
    Example Output: [{"code": "E471", "context": "Vegetable origin"}, {"code": "Gelatin", "context": ""}]
    """
    
    try:
        response = model.generate_content([prompt, image])
        text_output = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text_output)
    except google_exceptions.ResourceExhausted:
        st.error("AI Quota Error: You've exceeded the free request limit for today.")
        st.warning("Please wait for your quota to reset or enable billing on your Google Cloud project to continue.")
        st.info("For more information, visit: https://ai.google.dev/gemini-api/docs/rate-limits")
        return None
    except Exception as e:
        st.error(f"AI Error: {e}")
        try:
            st.write("🔍 Debug Info - Available Models:")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.write(f"- {m.name}")
        except Exception as debug_err:
            st.write(f"Could not list models: {debug_err}")
        return None

def check_database(ingredients):
    """
    Checks each ingredient against your Firebase 'Truth List'.
    """
    results_list = []
    overall_status = "Halal" # Optimistic default
    
    for item_obj in ingredients:
        # Handle input (expecting dict from new prompt)
        code_str = item_obj.get("code", "")
        context = item_obj.get("context", "")

        # Clean the text (e.g., "E-120" -> "E120", "INS 471" -> "E471")
        code_key = code_str.upper().replace("-", "").replace(" ", "").replace(".", "").replace("(", "").replace(")", "")
        
        # Handle INS codes (common in Asia)
        if "INS" in code_key:
            code_key = code_key.replace("INS", "E")
            
        # Handle raw numbers (e.g. "471" -> "E471")
        if code_key.isdigit():
            code_key = f"E{code_key}"
        
        # Check Firebase
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

        # Semantic Intelligence: Override Syubhah or Unknown if context is safe
        if current_status != "Haram":
            lower_context = context.lower()
            lower_name = name.lower()
            safe_keywords = ["vegetable", "plant", "soy", "synthetic", "mineral", "vegan", "polyol", "gum", "cocoa", "fiber", "vanilla", "amino", "bcaa", "fermentation"]
            
            if any(k in lower_context for k in safe_keywords) or any(k in lower_name for k in safe_keywords):
                if current_status in ["Syubhah", "Unknown"]:
                    current_status = "Halal"
                    if description == "Not in database yet.":
                        description = "Verified as Safe by AI Context."
                    elif "(Verified as Safe by AI Context)" not in description:
                        description += " (Verified as Safe by AI Context)"

        results_list.append({
            "code": code_str, 
            "name": name, 
            "status": current_status, 
            "description": description,
            "context": context
        })
            
        # Update Logic: Haram > Syubhah > Halal
        if current_status == 'Haram':
            overall_status = "Haram"
        elif current_status == 'Syubhah' and overall_status != "Haram":
            overall_status = "Syubhah"

    return overall_status, results_list

# --- 3. THE USER INTERFACE ---

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar: User Guide & History
with st.sidebar:
    st.title("☪️ HALAI™")
    st.caption("Halal Artificial Intelligence")
    st.header("📱 How to use / Panduan")
    st.markdown("""
    1. **Upload** photo of ingredients.
    2. **Scan** to detect E-codes.
    3. **Check** the safety score.
    """)
    st.info("💡 **Tip:** Ensure text is clear and readable.")
    st.divider()
    st.write("### 🛡️ Risk Levels")
    st.error("🔴 **Haram**: Prohibited")
    st.warning("🟠 **Syubhah**: Doubtful")
    st.success("🟢 **Halal**: Safe")
    st.divider()
    st.caption("🚀 Built for KitaHack 2026")

# Main Layout
st.title("HALAI™")
st.markdown("### 🛡️ Your AI-Powered Halal Food Scanner")

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.subheader("📸 Step 1: Upload Image")
    uploaded_file = st.file_uploader("Upload Label Image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Label', use_container_width=True)
        
        if st.button('🚀 Scan Ingredients / Imbas', type="primary", use_container_width=True):
            with st.spinner('🤖 AI is reading the label...'):
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
                    
                    # Sort results: Haram -> Syubhah -> Unknown -> Halal
                    sort_priority = {"Haram": 1, "Syubhah": 2, "Unknown": 3, "Halal": 4}
                    details.sort(key=lambda x: sort_priority.get(x['status'], 5))
                    
                    # Store in session state
                    st.session_state.results = {"status": status, "details": details}
                    st.toast("Scan complete!", icon="✅")

with col2:
    st.subheader("📊 Step 2: Analysis Result")
    
    if 'results' in st.session_state and st.session_state.results and uploaded_file:
        results = st.session_state.results
        status = results["status"]
        details = results["details"]
        
        # Dashboard Metrics
        total_items = len(details)
        safe_items = sum(1 for i in details if i['status'] == "Halal")
        score = int((safe_items / total_items) * 100) if total_items > 0 else 0
        
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Safety Score", f"{score}%")
        m_col2.metric("Ingredients Detected", total_items)
        
        # Verdict Card
        if status == "Haram":
            st.error(f"🚨 **HARAM DETECTED**\n\nContains prohibited ingredients.")
        elif status == "Syubhah":
            st.warning(f"⚠️ **SYUBHAH (Doubtful)**\n\nContains ingredients that require verification.")
            st.info("👉 **Recommendation:** Look for a Halal Logo (JAKIM) on the packaging to confirm safety.")
        else:
            st.success(f"✅ **LIKELY HALAL**\n\nNo flagged ingredients found.")
            
        # Share Button
        share_text = f"☪️ *HALAI™ Scan Result*\n\nStatus: *{status}*\nSafety Score: {score}%\n\nCheck your food with HALAI!"
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
        st.link_button("📤 Share Result on WhatsApp", whatsapp_url, use_container_width=True)

        st.divider()
        st.write("### 📝 Detailed Breakdown")
        
        for item in details:
            color = "red" if item['status'] == "Haram" else "orange" if item['status'] == "Syubhah" else "green"
            with st.container(border=True):
                st.markdown(f":{color}[**{item['code']} - {item['name']}**]")
                if item['context']:
                    st.caption(f"Context: {item['context']}")
                st.write(f"Status: **{item['status']}**")
                st.write(f"Note: {item['description']}")
        
        # Community Feature: Report Missing
        with st.expander("🚩 Report Incorrect Info"):
            with st.form("report_form"):
                missing_item = st.text_input("Ingredient Name")
                notes = st.text_area("Issue / Notes")
                submitted = st.form_submit_button("Submit Report")
                if submitted:
                    db.collection('reports').add({"item": missing_item, "notes": notes, "timestamp": firestore.SERVER_TIMESTAMP})
                    st.toast("Report submitted! Thank you.", icon="🙏")
    
    elif not uploaded_file:
        st.info("👈 Please upload an image to start.")