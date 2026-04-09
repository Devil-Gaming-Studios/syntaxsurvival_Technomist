from fastapi import FastAPI, UploadFile, File
import numpy as np
from typing import Dict

app = FastAPI()

# ================================
# 🧠 GLOBAL STORAGE
# ================================
global_models = {
    "diabetes": None,
    "heart":    None,
    "xray":     None,
}

collected_weights = []

# ================================
# 📦 MODEL LIST
# ================================
@app.get("/models")
def get_models():
    return {
        "models": [
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
    }

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
    return configs.get(model_id, {})

# ================================
# 📤 RECEIVE WEIGHTS
# ================================
@app.post("/send_weights")
def receive_weights(data: Dict):
    weights = data.get("weights")

    if weights is None:
        return {"error": "No weights provided"}

    collected_weights.append(weights)

    # ✅ FIX: Average layer-by-layer only when shapes match
    # Each entry in collected_weights is a list of layers (list of lists)
    if len(collected_weights) >= 2:
        try:
            first = collected_weights[0]
            averaged = []
            for layer_idx in range(len(first)):
                # Stack the same layer from all clients and average
                layer_stack = [np.array(cw[layer_idx]) for cw in collected_weights]
                avg_layer = np.mean(layer_stack, axis=0)
                averaged.append(avg_layer.tolist())

            global_models["heart"] = averaged
            collected_weights.clear()
            return {"status": "weights received and aggregated"}

        except Exception as e:
            collected_weights.clear()
            return {"error": f"Aggregation failed: {str(e)}"}

    return {"status": "weights received"}

# ================================
# 🔮 TABULAR PREDICTION
# ================================
@app.post("/predict")
def predict(data: Dict):
    x = data.get("input", [])
    result = sum(x) * 0.1  # dummy logic
    return {"prediction": result}

# ================================
# 🖼️ IMAGE PREDICTION (DEMO)
# ================================
@app.post("/predict_image")
async def predict_image(file: UploadFile = File(...)):
    return {"prediction": "Pneumonia (demo)"}
