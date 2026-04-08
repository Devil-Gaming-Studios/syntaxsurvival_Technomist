from fastapi import FastAPI, UploadFile, File
import numpy as np
from typing import Dict

app = FastAPI()

# ================================
# 🧠 GLOBAL STORAGE
# ================================
global_models = {
    "diabetes": [1.0, 2.0, 3.0],
    "xray": None
}

collected_weights = []

# ================================
# 📦 MODEL LIST
# ================================
@app.get("/models")
def get_models():
    return {
        "models": [
            {"id": "diabetes", "name": "Diabetes Predictor", "type": "tabular"},
            {"id": "heart", "name": "Heart Disease", "type": "tabular"},
            {"id": "xray", "name": "X-ray Classifier", "type": "image"}
        ]
    }

# ================================
# ⚙️ MODEL CONFIG
# ================================
@app.get("/model_config")
def get_model_config(model_id: str):

    configs = {
        "diabetes": {
            "type": "tabular",
            "input_size": 3,
            "model": "dense_small",
            "output": "binary"
        },
        "heart": {
            "type": "tabular",
            "input_size": 5,
            "model": "dense_medium",
            "output": "binary"
        },
        "xray": {
            "type": "image",
            "input_size": [128, 128, 3],
            "model": "cnn_small",
            "output": "binary"
        }
    }

    return configs.get(model_id, {})

# ================================
# 📤 RECEIVE WEIGHTS
# ================================
@app.post("/send_weights")
def receive_weights(data: Dict):

    weights = data["weights"]
    collected_weights.append(weights)

    # Simple aggregation
    if len(collected_weights) >= 2:
        avg = np.mean(collected_weights, axis=0)
        global_models["diabetes"] = avg.tolist()
        collected_weights.clear()

    return {"status": "weights received"}

# ================================
# 🔮 TABULAR PREDICTION
# ================================
@app.post("/predict")
def predict(data: Dict):

    x = data["input"]
    result = sum(x) * 0.1  # dummy logic

    return {"prediction": result}

# ================================
# 🖼️ IMAGE PREDICTION (DEMO)
# ================================
@app.post("/predict_image")
async def predict_image(file: UploadFile = File(...)):

    # Dummy prediction
    return {"prediction": "Pneumonia (demo)"}
