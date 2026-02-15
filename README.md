# ☪️ HALAI™

<div align="center">
  <img src="https://via.placeholder.com/150?text=HALAI" alt="HALAI Logo" width="150"/>
  <br>
  <b>Halal Artificial Intelligence Scanner</b>
</div>

**HALAI™** is an intelligent food scanner that instantly detects Haram and Syubhah ingredients using Google Gemini and Firebase. Built for **KitaHack 2026**.

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
