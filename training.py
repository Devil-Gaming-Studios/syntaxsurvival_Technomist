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
        config = requests.get(
            f"{SERVER_URL}/model_config?model_id={model_id}"
        ).json()

        # 🔴 IMPORTANT FIX
        if "num_classes" not in config:
            config["num_classes"] = len(np.unique(y))

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

    # Save globally
    trained_model = model
    last_config = config

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
        config = requests.get(
            f"{SERVER_URL}/model_config?model_id={model_id}"
        ).json()

        if "num_classes" not in config:
            config["num_classes"] = 2

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
        target_size=(128,128),
        batch_size=16,
        class_mode='binary'
    )

    # ================================
    # TRAIN
    # ================================
    model.fit(train_data, epochs=epochs)

    trained_model = model
    last_config = config

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

    # Normalize same as training
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
        return "❌ No model to upload"

    weights = trained_model.get_weights()
    weights_list = [w.tolist() for w in weights]

    response = requests.post(
        f"{SERVER_URL}/send_weights",
        json={"weights": weights_list}
    )

    return response.json()


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
