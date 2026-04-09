# PS-18 — Privacy Preservation in Healthcare Using Federated Learning

> **Disclaimer:** This system is for demonstration and academic purposes only. Not a certified medical device.

---

## Overview

Healthcare institutions need to collaborate on training AI diagnostic models, but patient data is highly sensitive and governed by strict regulations such as **HIPAA** and **GDPR**. Centralising data from multiple hospitals increases privacy risks and is often infeasible due to institutional data-sharing policies.

**PS-18** solves this by implementing a Federated Learning-based system where multiple hospitals can collaboratively train AI models **without sharing raw patient data**. Only model weights or gradients are transmitted to a central aggregation server — raw records (EHRs, medical images, diagnostic reports) **never leave** the originating institution.

---

## System Architecture

The system follows the standard federated learning topology:

```
Hospital A (app.py)  ─┐
Hospital B (app.py)  ──┼──► Central Aggregation Server ──► Global Model ──► Web Portal
Hospital C (app.py)  ─┘          /send_weights (POST)        (FedAvg)       (Inference)
```

| Component | Description |
|---|---|
| **Hospital Clients (N nodes)** | Each runs `app.py` locally. Trains on private data, uploads weights only. |
| **Central Aggregation Server** | Receives weights via `POST /send_weights`. Aggregates using FedAvg or similar. |
| **Global Model** | The aggregated model used for inference in the web portal. |
| **Web Portal** | Frontend for clinical staff to run predictions against the global model. |

> 🔒 **Raw patient data never leaves each hospital's premises.** This is the core privacy guarantee of the system.

---

## Components

The project is split into two main components:

### 1. Hospital Client Application (`app.py`)
A desktop GUI built with Python (Tkinter) that runs at each participating hospital. Handles local dataset upload, local model training, and secure weight upload to the central server.

### 2. Diagnostic Web Portal (`index.html`, `style.css`, `script.js`)
A browser-based interface allowing clinical staff to run inference using the aggregated model hosted on a FastAPI backend.

Together, these simulate the full federated learning pipeline:

**Local Training → Weight Upload → Central Aggregation → Inference**

---

## Tech Stack

| Component | Technology |
|---|---|
| Hospital Client UI | Python, Tkinter |
| Local Model Training | Python (`training.py`) |
| Weight Upload | Python `requests` / HTTP POST |
| Web Portal Frontend | HTML, CSS, Vanilla JavaScript |
| Web Portal Backend | FastAPI (Python) |
| Treatment Plan Generation | Google Gemini AI |
| Aggregation Server Hosting | Render (`syntaxsurvival-technomist-2.onrender.com`) |

---

## Hospital Client — Screen Flow

| Screen | Purpose |
|---|---|
| **Login Screen** | Staff ID and password entry. Demo mode — no real auth backend. |
| **Terms & Conditions** | Staff must read and accept data handling terms before proceeding. |
| **Main Screen** | Lists available diagnostic models from the server. Supports search and custom model registration. |
| **Upload Screen** | Staff selects local dataset (CSV or image folder) and sets training epochs (default: 10). |
| **Loading / Training Screen** | Runs `train_and_upload()` in a background thread. Progress bar animates. |
| **Result Screen** | Displays training metrics: accuracy, loss, number of layers, model size. |
| **Server Upload Screen** | Staff confirms the server endpoint URL and initiates weight upload. |
| **Server Loading Screen** | Calls `upload_weights()` in background. Steps: Connecting → Serializing → Uploading → Verifying. |
| **Upload Success / Error** | Confirms receipt of weights and displays raw server JSON response. |

### Key Functions (`training.py`)

| Function | Description |
|---|---|
| `train_and_upload(model, filepath, epochs)` | Trains the model locally on the hospital's dataset and returns metrics. |
| `upload_weights()` | Serializes trained weights and POSTs them to the central server endpoint. |
| `get_models()` | Fetches available model list from server. Falls back to defaults if unreachable. |
| `add_model_to_server(name, type)` | Registers a new custom model name on the central server. |
| `predict_disease(model_id, data)` | Runs local inference for a given model and input. |
| `detect_data_type(filepath)` | Determines whether a dataset is tabular (CSV) or image-based. |

### Supported Model Types

- **Tabular models** (e.g., Heart Disease) — accept CSV datasets with features like age, cholesterol, blood pressure.
- **Image models** (e.g., Tumor / X-Ray) — accept a folder of images and use a CNN-based architecture.

---

## Diagnostic Web Portal

### Supported Diagnostic Modules

| Module | Inputs | Endpoint |
|---|---|---|
| **Diabetes** | Gender, age, hypertension, heart disease history, smoking history, BMI, HbA1c, blood glucose | `POST /api/diabetes/predict` |
| **Heart Disease** | Age, gender, cholesterol, resting blood pressure, max heart rate | `POST /api/heart/predict` |
| **COVID-19 X-Ray** | Chest X-ray image upload (PNG/JPG) | `POST /api/xray/predict` |

### Backend API Endpoints (FastAPI)

| Endpoint | Method | Input |
|---|---|---|
| `/api/diabetes/predict` | POST | JSON with 8 clinical parameters |
| `/api/heart/predict` | POST | JSON with 5 cardiac parameters |
| `/api/xray/predict` | POST | Multipart image file |
| `/send_weights` | POST | Serialized model weights from hospital clients |

### Frontend Flow

1. User selects a condition from the dropdown or clicks a disease card.
2. The relevant form is rendered dynamically via `renderForm()` in `script.js`.
3. On submission, an async function sends a `POST` request to the FastAPI backend.
4. The response `{ diagnosis, treatment_plan }` is displayed in a result card. Treatment plan is generated by Gemini AI.

---

## Privacy & Security

- 🔒 **No raw data leaves the hospital.** The client app only transmits trained model weights, not patient records or datasets.
- 🔄 **Federated aggregation.** The central server aggregates weights from multiple hospitals (FedAvg), producing a global model without ever holding institutional data.
- ⚠️ **Demo disclaimer.** The login and terms screens clearly indicate demo/reference mode. No credentials are stored or validated against a real backend.
- ⚙️ **Configurable server endpoint.** Hospital staff can modify the server URL in the upload screen, supporting different institutional network configurations.

---

## Limitations & Future Scope

- The current demo uses a single aggregation server with **no differential privacy** or secure multi-party computation. Adding noise injection before weight upload would further strengthen privacy guarantees.
- The **login system is UI-only** and would need a proper authentication backend (JWT tokens, role-based access) in production.
- The aggregation strategy (FedAvg or otherwise) is implemented server-side and is outside the scope of the client codebase.
- The web portal currently performs inference against a **single aggregated model**; future versions could support model versioning and rollback.

---

## Project Info

| | |
|---|---|
| **Project ID** | PS-18 |
| **Domain** | Healthcare AI / Privacy Preserving ML |
| **Documentation Date** | April 2026 |

---

## Team Technomist

- [Ravi Prakash Nag](https://github.com/divyanshagrawal51) 
- [Divyansh Agrawal](https://github.com/Devil-Gaming-Studios)
