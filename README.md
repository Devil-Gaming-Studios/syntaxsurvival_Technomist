**✚ MediCare AI**

Project Documentation & Setup Guide

Version 1.0 \| 2026

**1. Project Overview**

MediCare AI is a full-stack medical diagnostic web application that
combines machine learning models with Gemini AI to provide instant
clinical diagnoses and personalised treatment plans across three medical
conditions.

The system accepts clinical parameters or medical images from users,
runs them through trained ML models, and generates a RAG-based treatment
plan using Google Gemini 1.5 Flash.

  ---------------------- ------------------------------------------------
  **Frontend**           Plain HTML, CSS, JavaScript

  **Backend**            Python FastAPI

  **AI / RAG**           Google Gemini 1.5 Flash

  **ML Models**          scikit-learn / Keras (placeholder --- swap in
                         real models)

  **Image Model**        PIL + deep learning (COVID X-Ray)
  ---------------------- ------------------------------------------------

**2. Features**

**2.1 Diagnostic Modules**

-   Diabetes Screening --- analyses glucose, HbA1c, BMI, hypertension,
    and lifestyle factors

-   Heart Disease Screening --- evaluates ECG, cholesterol, blood
    pressure, exercise data

-   COVID-19 X-Ray Analysis --- deep learning image classification on
    chest X-rays

**2.2 AI Treatment Plans**

-   Each diagnosis triggers a Gemini AI call that generates a
    structured, personalised treatment plan

-   Covers lifestyle changes, monitoring, medications, warning signs,
    and follow-up care

-   Falls back to hardcoded plans if Gemini API key is not configured

**2.3 Desktop Application (Tkinter)**

-   Full-screen medical portal built with Python Tkinter

-   Login screen with pseudo-authentication

-   Terms & Conditions screen with scrollable text and checkbox
    agreement

-   Model selection screen with Tumor Detection and Heart Disease models

-   Dataset upload with epoch configuration for training

-   Animated loading/progress screens for training and server upload

-   Results screen with weights JSON preview and download

-   Server upload flow with success confirmation screen

**3. Project Structure**

**medicare-web/**

> backend/
>
> main.py FastAPI app entry point
>
> requirements.txt Python dependencies
>
> .env Environment variables (Gemini API key)
>
> models/
>
> diabetes_model.py Diabetes prediction logic
>
> heart_model.py Heart disease prediction logic
>
> xray_model.py COVID X-ray prediction logic
>
> routes/
>
> diabetes.py POST /api/diabetes/predict
>
> heart.py POST /api/heart/predict
>
> xray.py POST /api/xray/predict
>
> rag/
>
> treatment.py Gemini AI treatment plan generator
>
> frontend/
>
> index.html Single-page portal
>
> style.css Styling (DM Serif Display + DM Sans)
>
> script.js Form rendering + API calls
>
> app.py Tkinter desktop application

**4. Setup & Installation**

**4.1 Prerequisites**

-   Python 3.10 (with tkinter --- use the official .exe installer,
    enable tcl/tk)

-   Node.js (optional, for frontend tooling)

-   A Google Gemini API key (free tier available at aistudio.google.com)

**4.2 Backend Setup**

Step 1 --- Create and activate a virtual environment:

> py -3.10 -m venv venv
>
> venv\\Scripts\\activate

Step 2 --- Install dependencies:

> pip install -r backend/requirements.txt

Step 3 --- Add your Gemini API key:

Open backend/.env and replace the placeholder:

> GEMINI_API_KEY=your_actual_key_here

Step 4 --- Run the FastAPI server:

> cd backend
>
> python main.py

The API will be available at http://localhost:8000

Interactive docs available at http://localhost:8000/docs

**4.3 Frontend Setup**

No build step required. Simply open frontend/index.html in a browser
while the FastAPI backend is running.

For best results, serve via a local server to avoid CORS issues:

> cd frontend
>
> python -m http.server 5500

Then visit http://localhost:5500 in your browser.

**4.4 Desktop App Setup**

Make sure your venv is activated and tkinter is installed, then run:

> python app.py

If you see ModuleNotFoundError, install missing packages:

> pip install pandas numpy scikit-learn pillow

**5. API Reference**

**POST /api/diabetes/predict**

  ------------------------- ------------------------------------------------
  **Endpoint**              /api/diabetes/predict

  **Method**                POST

  **Body**                  JSON

  **gender**                String: Male / Female / Other

  **age**                   Float

  **hypertension**          Int: 0 or 1

  **heart_disease**         Int: 0 or 1

  **smoking_history**       String: never / former / current / not current /
                            ever

  **bmi**                   Float (e.g. 27.5)

  **HbA1c_level**           Float (e.g. 5.5)

  **blood_glucose_level**   Int (mg/dL)
  ------------------------- ------------------------------------------------

**POST /api/heart/predict**

  ---------------------- ------------------------------------------------
  **Endpoint**           /api/heart/predict

  **Method**             POST

  **Body**               JSON

  **age**                Int

  **gender**             String: Male / Female

  **chest_pain**         Int: 0-3

  **rest_bp**            Int (mmHg)

  **cholesterol**        Int (mg/dL)

  **fasting_bs**         Int: 0 or 1

  **rest_ecg**           Int: 0-2

  **max_hr**             Int (bpm)

  **exercise_angina**    Int: 0 or 1

  **st_depression**      Float

  **st_slope**           Int: 0-2

  **num_vessels**        Int: 0-3

  **thalassemia**        Int: 1-3
  ---------------------- ------------------------------------------------

**POST /api/xray/predict**

  ---------------------- ------------------------------------------------
  **Endpoint**           /api/xray/predict

  **Method**             POST

  **Body**               multipart/form-data

  **file**               Image file (PNG, JPG, JPEG)
  ---------------------- ------------------------------------------------

**Response Format (all endpoints)**

> { \"prediction\": 1, \"probability\": 0.87, \"diagnosis\":
> \"Diabetic\",
>
> \"risk_level\": \"High\", \"treatment_plan\": \"\...\", \"disease\":
> \"diabetes\" }

**6. Plugging In Real Models**

Each model file contains a placeholder prediction function with clear
comments showing exactly where to swap in your trained model. For
example, in backend/models/diabetes_model.py:

> \# Replace the dummy logic below with:
>
> \# import pickle
>
> \# model = pickle.load(open(\'diabetes_model.pkl\', \'rb\'))
>
> \# prob = model.predict_proba(features)\[0\]\[1\]

Similarly, xray_model.py shows the Keras/TensorFlow pattern for image
models. Save your .pkl, .h5, or .pt files in the backend/models/
directory and update the relevant function.

**7. Building the Desktop App as .exe**

To package app.py as a standalone Windows executable:

> pip install pyinstaller
>
> pyinstaller \--onefile \--windowed \\
>
> \--hidden-import=pandas \\
>
> \--hidden-import=numpy \\
>
> \--hidden-import=sklearn \\
>
> \--hidden-import=PIL \\
>
> app.py

The output .exe will be in the dist/ folder. If the app crashes
silently, run it from cmd to see the error:

> app.exe & pause

**8. Known Issues & Troubleshooting**

**tkinter not found**

Reinstall Python 3.10 using the official .exe installer from python.org.
During installation, choose Customize Installation and ensure tcl/tk and
IDLE is checked.

**ModuleNotFoundError when running .exe**

Add the missing module as a \--hidden-import flag when running
PyInstaller. Common ones: pandas, numpy, sklearn, PIL, tkinter.

**CORS error in browser**

Make sure the FastAPI server is running. The backend includes CORS
middleware allowing all origins. If issues persist, serve the frontend
via a local HTTP server instead of opening the file directly.

**Gemini API not responding**

Verify your GEMINI_API_KEY in backend/.env is correct. The system
automatically falls back to hardcoded treatment plans if the API call
fails.

**ev.txt / requirements file not found**

Make sure the requirements file is in the same folder as your
terminal\'s working directory, or provide the full path: pip install -r
C:\\full\\path\\to\\ev.txt

**9. Disclaimer**

*This application is for demonstration and educational purposes only. It
does not constitute medical advice and should not be used as a
substitute for professional medical diagnosis or treatment. Always
consult a qualified healthcare professional.*

✚ MediCare AI \| Built with FastAPI + Gemini AI \| 2026
