from fastapi import FastAPI
import numpy as np

app = FastAPI()

# Dummy global model weights (replace later with real model)
global_model_weights = [1.0, 2.0, 3.0]

all_weights = []

@app.get("/")
def home():
    return {"message": "Server is running"}

# 📥 Get model
@app.get("/get_model")
def get_model():
    return {"weights": global_model_weights}

# 📤 Send weights
@app.post("/send_weights")
def send_weights(data: dict):
    global global_model_weights

    weights = data["weights"]
    all_weights.append(weights)

    # Aggregate after 2 clients (demo)
    if len(all_weights) >= 2:
        avg = np.mean(all_weights, axis=0)
        global_model_weights = avg.tolist()
        all_weights.clear()

    return {"status": "received"}

# 🔮 Prediction (dummy logic)
@app.post("/predict")
def predict(data: dict):
    x = data["input"]
    result = sum(x) * 0.1  # fake prediction

    return {"prediction": result}