import pandas as pd
import numpy as np
import requests
import os

from model import build_model_from_config, suggest_model_config

# 🔹 CHANGE THIS
SERVER_URL = "https://your-app.onrender.com"

# ================================
# 📊 TABULAR DATA TRAINING
# ================================
def train_tabular(file_path, use_server_model=True, model_id=None):

    # Load CSV
    data = pd.read_csv(file_path)

    X = data.iloc[:, :-1].values
    y = data.iloc[:, -1].values

    # Normalize
    X = X / np.max(X, axis=0)

    # ================================
    # 🧠 Get Model Config
    # ================================
    if use_server_model and model_id:
        config = requests.get(
            f"{SERVER_URL}/model_config?model_id={model_id}"
        ).json()
    else:
        config = suggest_model_config(X, y)

    # ================================
    # 🏗️ Build Model
    # ================================
    model = build_model_from_config(config)

    # ================================
    # 🚀 Train
    # ================================
    model.fit(X, y, epochs=5, verbose=1)

    # ================================
    # 📤 Send Weights
    # ================================
    send_weights(model)

    return "Tabular training completed"


# ================================
# 🖼️ IMAGE DATA TRAINING
# ================================
def train_image(folder_path,epochs, use_server_model=True, model_id="xray"):

    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    # ================================
    # 🧠 Get Model Config
    # ================================
    if use_server_model:
        config = requests.get(
            f"{SERVER_URL}/model_config?model_id={model_id}"
        ).json()
    else:
        config = {
            "type": "image",
            "input_size": [128, 128, 3],
            "model": "cnn_small",
            "output": "binary"
        }

    # ================================
    # 🏗️ Build Model
    # ================================
    model = build_model_from_config(config)

    # ================================
    # 📁 Load Image Data
    # ================================
    datagen = ImageDataGenerator(rescale=1./255)

    train_data = datagen.flow_from_directory(
        folder_path,
        target_size=(128,128),
        batch_size=16,
        class_mode='binary'
    )

    # ================================
    # 🚀 Train
    # ================================
    model.fit(train_data, epochs)

    # ================================
    # 📤 Send Weights
    # ================================
    send_weights(model)

    return "Image training completed"


# ================================
# 🔍 AUTO DETECT DATA TYPE
# ================================
def detect_data_type(path):

    if os.path.isdir(path):
        return "image"

    elif path.endswith(".csv"):
        return "tabular"

    else:
        return "unknown"


# ================================
# 📤 SEND WEIGHTS TO SERVER
# ================================
def send_weights(model):

    weights = model.get_weights()
    weights_list = [w.tolist() for w in weights]

    response = requests.post(
        f"{SERVER_URL}/send_weights",
        json={"weights": weights_list}
    )

    print("Server Response:", response.json())


# ================================
# 🚀 MAIN TRAIN FUNCTION (USE THIS)
# ================================
def train_and_upload(path, use_server_model=True, model_id=None):

    data_type = detect_data_type(path)

    if data_type == "tabular":
        return train_tabular(path, use_server_model, model_id)

    elif data_type == "image":
        return train_image(path, use_server_model, model_id)

    else:
        return "Unsupported data format"
