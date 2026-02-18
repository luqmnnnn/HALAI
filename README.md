# ☪️ HALAI™

<div align="center">
  <img src="https://via.placeholder.com/150?text=HALAI" alt="HALAI Logo" width="150"/>
  <br>
  <b>Halal Artificial Intelligence Scanner</b>
</div>

**HALAI™** is an intelligent food scanner that instantly detects Haram and Syubhah ingredients using Google Gemini and Firebase. Built for **KitaHack 2026**.

This project directly addresses **UN Sustainable Development Goal 3: Good Health and Well-being** by empowering consumers to make informed dietary choices that align with their health, cultural, and religious needs.

## 🏗️ System Architecture

The app follows a streamlined flow to ensure accurate results:

`User (Image)` $\rightarrow$ `Gemini AI (OCR & Context)` $\rightarrow$ `Firebase (Validation)` $\rightarrow$ `Streamlit (Result Dashboard)`

## 🛠️ Tech Stack

*   **Python**: Core logic.
*   **Streamlit**: Frontend UI.
*   **Google Gemini**: Image analysis and semantic understanding.
*   **Firebase Firestore**: Real-time database for E-codes.

## 🚀 Features

*   **Smart Detection**: Understands context (e.g., "Vegetable E471" is Halal).
*   **Safety Score**: Instant visual rating of the product.
*   **Community Driven**: Users can report missing ingredients.

## 🔄 User Feedback & Iteration

We actively tested HALAI™ with real users to refine the experience:
1.  **Feedback:** "Text is too small." $\rightarrow$ **Fix:** Increased font size and contrast.
2.  **Feedback:** "What is Syubhah?" $\rightarrow$ **Fix:** Added clear definitions in the sidebar.
3.  **Feedback:** "App crashes on bad internet." $\rightarrow$ **Fix:** Added offline error handling.

## 💻 How to Run

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Setup Keys**
    *   Create a `.env` file with `GEMINI_API_KEY=your_key`.
    *   Place `firebase_key.json` in the root folder.

3.  **Launch App**
    ```bash
    streamlit run app.py
    ```
