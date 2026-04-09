from fastapi import FastAPI, UploadFile, File, Request
import numpy as np
from typing import Dict
import requests as http_requests
import json
import io
from PIL import Image
from fastapi.responses import StreamingResponse
import time


app = FastAPI()

# ================================
# 🧠 GLOBAL STORAGE
# ================================
global_models = {
    "diabetes": None,
    "heart":    None,
    "xray":     None,
}

collected_weights = {}
custom_models     = []   # models added at runtime via /add_model
custom_configs    = {}   # configs for custom models

# ================================
# 🤖 GEMINI HELPER
# ================================
GEMINI_API_KEY = "AIzaSyD2JE1mtrjdpdsaO3qBdHbvGGQcl5eyHkI"

# ================================
# 🤖 GEMINI HELPER (STREAMING)
# ================================
def ask_gemini_stream(prompt: str):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        with http_requests.post(url, json=payload, stream=True, timeout=60) as res:
            for line in res.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data:"):
                        try:
                            chunk = json.loads(line[5:])
                            text  = chunk["candidates"][0]["content"]["parts"][0]["text"]
                            yield text
                        except Exception:
                            continue
    except Exception as e:
        yield f"Treatment plan unavailable: {str(e)}"
# ================================
# 📦 MODEL LIST
# ================================
@app.get("/models")
def get_models():
    base_models = [
            {
                "id":          "diabetes",
                "name":        "Diabetes Predictor",
                "type":        "tabular",
                "description": "Predicts diabetes risk from patient tabular data."
            },
            {
                "id":          "heart",
                "name":        "Heart Disease Model",
                "type":        "tabular",
                "description": "Evaluates cardiac indicators to assess heart disease risk."
            },
            {
                "id":          "xray",
                "name":        "Tumor Detection",
                "type":        "image",
                "description": "Analyzes imaging data to identify and classify tumor regions."
            }
        ]
    return {"models": base_models + custom_models}

# ================================
# ⚙️ MODEL CONFIG
# ================================
@app.get("/model_config")
def get_model_config(model_id: str):
    configs = {
        "diabetes": {
            "type":       "tabular",
            "input_size": 3,
            "model":      "dense_small",
            "output":     "binary"
        },
        "heart": {
            "type":       "tabular",
            "input_size": 5,       # input_size is overridden by actual data in training.py
            "model":      "dense_medium",
            "output":     "binary"
        },
        "xray": {
            "type":       "image",
            "input_size": [128, 128, 3],
            "model":      "cnn_small",
            "output":     "binary"
        }
    }
    return configs.get(model_id) or custom_configs.get(model_id, {})

# ================================
# ➕ ADD CUSTOM MODEL
# ================================
@app.post("/add_model")
def add_model(data: Dict):
    model_id   = data.get("id", "").strip().lower().replace(" ", "_")
    model_name = data.get("name", "").strip()
    model_type = data.get("type", "tabular")
    description = data.get("description", f"Custom {model_type} model.")

    if not model_id or not model_name:
        return {"error": "id and name are required"}

    # Check for duplicates
    existing_ids = [m["id"] for m in custom_models]
    if model_id in existing_ids or model_id in ["diabetes", "heart", "xray"]:
        return {"error": f"Model '{model_id}' already exists"}

    custom_models.append({
        "id":          model_id,
        "name":        model_name,
        "type":        model_type,
        "description": description,
    })

    # Also create a default config for it
    custom_configs[model_id] = {
        "type":       model_type,
        "input_size": [128, 128, 3] if model_type == "image" else 10,
        "model":      "cnn_small" if model_type == "image" else "dense_small",
        "output":     "binary",
    }

    return {"status": "model added", "id": model_id}

# ================================
# 📤 RECEIVE WEIGHTS
# ================================
@app.post("/send_weights")
def receive_weights(data: Dict):
    model_id = data.get("model_id")
    weights  = data.get("weights")

    if not model_id or weights is None:
        return {"error": "model_id and weights required"}

    # 🔥 Create model entry if not exists
    if model_id not in collected_weights:
        collected_weights[model_id] = []

    # ➕ Add weights
    collected_weights[model_id].append(weights)

    # 🔄 Aggregate when enough weights collected
    if len(collected_weights[model_id]) >= 2:
        try:
            first = collected_weights[model_id][0]
            averaged = []

            for layer_idx in range(len(first)):
                layer_stack = [
                    np.array(cw[layer_idx])
                    for cw in collected_weights[model_id]
                ]
                avg_layer = np.mean(layer_stack, axis=0)
                averaged.append(avg_layer.tolist())

            # ✅ Store in correct model
            global_models[model_id] = averaged

            # 🧹 Clear only that model’s weights
            collected_weights[model_id].clear()

            return {"status": f"{model_id} aggregated successfully"}

        except Exception as e:
            collected_weights[model_id].clear()
            return {"error": f"Aggregation failed: {str(e)}"}

    return {"status": f"{model_id} weights added"}
# ================================
# 🧮 MANUAL FORWARD PASS
# ================================
def manual_predict(x, weights, output_type="binary"):
    try:
        out        = x
        num_layers = len(weights) // 2
        for i in range(num_layers):
            W   = np.array(weights[i * 2])
            b   = np.array(weights[i * 2 + 1])
            out = out @ W + b
            if i < num_layers - 1:
                out = np.maximum(0, out)
        if output_type == "binary":
            out = 1 / (1 + np.exp(-out))
            return float(out.flatten()[0])
        elif output_type == "multi_class":
            e   = np.exp(out - np.max(out))
            out = e / e.sum()
            return float(np.argmax(out))
        else:
            return float(out.flatten()[0])
    except Exception:
        return 0.5

# ================================
# 🔮 GENERIC PREDICT
# ================================
@app.post("/predict/{model_id}")
async def predict(model_id: str, request: Request):
    try:
        config = get_model_config(model_id)
        if not config:
            return {"prediction": "Error", "treatment": f"Unknown model: {model_id}"}

        model_type  = config.get("type", "tabular")
        output_type = config.get("output", "binary")
        weights     = global_models.get(model_id)
        label       = model_id.replace("_", " ").title()

        if model_type == "image":
            form    = await request.form()
            file    = form.get("file")
            content = await file.read()
            img = Image.open(io.BytesIO(content)).convert("RGB").resize((128, 128))
            x   = np.array(img, dtype=float) / 255.0
            x   = x.flatten().reshape(1, -1)
            data = {}
        else:
            body = await request.body()
            data = json.loads(body)
            x    = np.array([list(data.values())], dtype=float)
            x    = x / (np.max(x) + 1e-8)

        if weights:
            raw = manual_predict(x, weights, output_type)
        else:
            raw = 0.5

        if output_type == "binary":
            result = f"{label} Detected" if raw > 0.5 else f"No {label} Detected"
        elif output_type == "multi_class":
            result = f"Class {int(raw)}"
        else:
            result = f"Value: {round(raw, 4)}"

        if model_type == "image":
            prompt = f"""
            A medical image was submitted for {label} screening.
            AI Prediction: {result}.
            Provide a brief personalised treatment plan in 4-5 bullet points.
            """
        else:
            prompt = f"""
            A patient was screened for {label} with the following data: {data}.
            AI Prediction: {result}.
            Provide a brief personalised treatment and lifestyle plan in 4-5 bullet points.
            """

        def stream():
            # First send prediction as a JSON line
            yield json.dumps({"prediction": result}) + "\n"
            # Then stream treatment word by word
            for chunk in ask_gemini_stream(prompt):
                yield json.dumps({"treatment_chunk": chunk}) + "\n"

            return StreamingResponse(stream(), media_type="text/event-stream")
    except Exception as e:
        return {"prediction": "Error", "treatment": str(e)}
