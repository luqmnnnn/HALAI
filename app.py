import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from PIL import Image
import os
import json
from google.api_core import exceptions as google_exceptions

# --- 1. CONFIGURATION ---
load_dotenv() # Load your .env file
st.set_page_config(page_title="Halal-Check AI", page_icon="🔍")

# Setup Gemini AI (The Brain)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Setup Firebase (The Validator)
# We check if it's already initialized to prevent errors when Streamlit refreshes
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- 2. CORE FUNCTIONS ---

def analyze_image(image):
    """
    Sends the image to Gemini and asks it to find E-codes.
    We ask for JSON format so we can process it easily.
    """
    prompt = """
    Analyze this food label image.
    1. Identify all E-numbers (e.g., E120, E471) or suspicious ingredients (Gelatin, Lard).
    2. Return the result strictly as a JSON list of strings.
    3. Do not add markdown like ```json. Just the raw list.
    
    Example Output: ["E120", "E471", "Gelatin"]
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
    
    for item in ingredients:
        # Clean the text (e.g., "E-120" -> "E120")
        code_key = item.upper().replace("-", "").replace(" ", "")
        
        # Check Firebase
        doc_ref = db.collection('ecodes').document(code_key)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            results_list.append(data)
            
            # Update Logic: Haram > Syubhah > Halal
            if data['status'] == 'Haram':
                overall_status = "Haram"
            elif data['status'] == 'Syubhah' and overall_status != "Haram":
                overall_status = "Syubhah"
        else:
            # Item not in database (Unknown)
            results_list.append({
                "code": item, 
                "name": item, 
                "status": "Unknown", 
                "description": "Not in database yet."
            })

    return overall_status, results_list

# --- 3. THE USER INTERFACE ---

st.title("🔍 Halal-Check AI")
st.write("Snap a photo of ingredients. We'll check if it's safe.")

# The Camera/Upload Button
uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Show the image
    image = Image.open(uploaded_file)
    st.image(image, caption='Your Label', use_container_width=True)
    
    if st.button('🚀 Scan Now'):
        with st.spinner('🤖 AI is reading the label...'):
            # Step 1: Ask Gemini
            detected_ingredients = analyze_image(image)
        
        if detected_ingredients is None:
            pass # Error already displayed above
        elif not detected_ingredients:
            st.warning("No E-codes or ingredients detected. Try a clearer photo.")
        else:
            with st.spinner('📚 Checking Database...'):
                # Step 2: Check Firebase
                status, details = check_database(detected_ingredients)
            
            # Step 3: Show Result
            st.divider()
            
            if status == "Haram":
                st.error(f"🚨 HARAM DETECTED")
                st.write("Contains prohibited ingredients.")
            elif status == "Syubhah":
                st.warning(f"⚠️ SYUBHAH (Doubtful)")
                st.write("Contains ingredients that require verification (e.g. Gelatin source).")
            else:
                st.success(f"✅ LIKELY HALAL")
                st.write("No flagged ingredients found in our database.")

            # Show details
            st.write("### Detailed Breakdown:")
            for item in details:
                color = "red" if item['status'] == "Haram" else "orange" if item['status'] == "Syubhah" else "green"
                st.markdown(f":{color}[**{item['code']} - {item['name']}**]")
                st.write(f"Status: **{item['status']}**")
                st.write(f"Note: {item['description']}")
                st.divider()