import pandas as pd
import numpy as np
import requests
import os

from model import build_model_from_config, suggest_model_config

SERVER_URL = "https://syntaxsurvival-technomist-2.onrender.com"

# ================================
# 🧠 GLOBAL STORAGE
# ================================
trained_model = None
last_config = None


# ================================
# 📊 TABULAR TRAINING
# ================================
def train_tabular(file_path, epochs, use_server_model=True, model_id=None):

    global trained_model, last_config

    data = pd.read_csv(file_path)

    X = data.iloc[:, :-1].values
    y = data.iloc[:, -1].values

    # Normalize safely
    X = X / (np.max(X, axis=0) + 1e-8)

    # ================================
    # 🧠 CONFIG
    # ================================
    if use_server_model and model_id:
        try:
            config = requests.get(
                f"{SERVER_URL}/model_config?model_id={model_id}",
                timeout=10
            ).json()
        except Exception:
            # Server unreachable — fall back to auto config
            config = suggest_model_config(X, y)

        # ✅ FIX: Always override input_size with actual data shape
        # Server config may have been saved for a different dataset
        config["num_classes"] = int(len(np.unique(y)))
        config["input_size"]  = int(X.shape[1])   # <-- this was the shape mismatch bug

        # If server didn't return a type/model, fill in defaults
        if "type" not in config:
            config["type"] = "tabular"
        if "model" not in config:
            config["model"] = "dense_small"
        if "output" not in config:
            unique = len(np.unique(y))
            config["output"] = "binary" if unique == 2 else "multi_class" if unique < 10 else "regression"

    else:
        config = suggest_model_config(X, y)

    # ================================
    # 🏗️ MODEL
    # ================================
    model = build_model_from_config(config)

    # ================================
    # 🚀 TRAIN
    # ================================
    model.fit(X, y, epochs=epochs, verbose=1)

    trained_model = model
    last_config   = config

    return "Tabular training completed"


# ================================
# 🖼️ IMAGE TRAINING
# ================================
def train_image(folder_path, epochs, use_server_model=True, model_id="xray"):

    global trained_model, last_config

    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    # ================================
    # CONFIG
    # ================================
    if use_server_model:
        try:
            config = requests.get(
                f"{SERVER_URL}/model_config?model_id={model_id}",
                timeout=10
            ).json()
        except Exception:
            config = {}

        if "num_classes" not in config:
            config["num_classes"] = 2
        # ✅ Always enforce known-good image defaults
        if "type" not in config:
            config["type"] = "image"
        if "model" not in config:
            config["model"] = "cnn_small"
        if "output" not in config:
            config["output"] = "binary"
        config["input_size"] = [128, 128, 3]  # fixed for ImageDataGenerator

    else:
        config = {
            "type": "image",
            "input_size": [128, 128, 3],
            "model": "cnn_small",
            "output": "binary",
            "num_classes": 2
        }

    # ================================
    # MODEL
    # ================================
    model = build_model_from_config(config)

    # ================================
    # DATA
    # ================================
    datagen = ImageDataGenerator(rescale=1./255)

    train_data = datagen.flow_from_directory(
        folder_path,
        target_size=(128, 128),
        batch_size=16,
        class_mode='binary'
    )

    # ================================
    # TRAIN
    # ================================
    model.fit(train_data, epochs=epochs)

    trained_model = model
    last_config   = config

    return "Image training completed"


# ================================
# 🔍 DETECT DATA TYPE
# ================================
def detect_data_type(path):

    if os.path.isdir(path):
        return "image"

    elif path.endswith(".csv"):
        return "tabular"

    else:
        return "unknown"


# ================================
# 🧪 TEST / PREDICT FUNCTION
# ================================
def predict_disease(input_data):

    global trained_model, last_config

    if trained_model is None:
        return "❌ Model not trained yet"

    X = np.array(input_data).reshape(1, -1)
    X = X / (np.max(X) + 1e-8)

    prediction = trained_model.predict(X)

    if last_config["output"] == "binary":
        return "Disease Detected" if prediction[0][0] > 0.5 else "No Disease"

    elif last_config["output"] == "multi_class":
        return f"Class: {np.argmax(prediction)}"

    else:
        return f"Value: {prediction[0][0]}"


# ================================
# 📤 MANUAL UPLOAD (CONTROLLED)
# ================================
def upload_weights():

    global trained_model

    if trained_model is None:
        return {"error": "❌ No model to upload"}

    weights      = trained_model.get_weights()
    weights_list = [w.tolist() for w in weights]

    try:
        response = requests.post(
            f"{SERVER_URL}/send_weights",
            json={"weights": weights_list},
            timeout=30
        )
        # Server may return empty body on success — handle gracefully
        try:
            return response.json()
        except Exception:
            if response.status_code in (200, 201, 204):
                return {"status": "success", "code": response.status_code}
            else:
                return {"error": f"Server returned status {response.status_code} with no body"}

    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to server. It may be offline or still waking up — try again in 30 seconds."}
    except requests.exceptions.Timeout:
        return {"error": "Server timed out. It may be waking up (free tier) — try again in 30 seconds."}
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}


# ================================
# 🚀 MAIN TRAIN FUNCTION
# ================================
def train_and_upload(path, epochs, use_server_model=True, model_id=None):

    data_type = detect_data_type(path)

    if data_type == "tabular":
        return train_tabular(path, epochs, use_server_model, model_id)

    elif data_type == "image":
        return train_image(path, epochs, use_server_model, model_id)

    else:
        return "Unsupported data format"
