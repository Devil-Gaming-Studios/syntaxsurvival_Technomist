import pandas as pd
import numpy as np
import requests
import os

from model import build_model_from_config, suggest_model_config

SERVER_URL = "https://syntaxsurvival-technomist-2.onrender.com"

# ================================
# 🧠 GLOBAL STORAGE
# ================================
trained_model  = None
last_config    = None
last_model_id  = None
last_history   = None   # NEW: stores {"loss": [...], "accuracy": [...]}


# ================================
# 📋 FETCH MODEL LIST FROM SERVER
# ================================
def get_models():
    """
    Fetches the available model list from the server.
    Returns a list of tuples: (id, name, description)
    Falls back to a default list if server is unreachable.
    """
    try:
        response = requests.get(f"{SERVER_URL}/models", timeout=10)
        data = response.json()
        models = []
        for m in data.get("models", []):
            model_id   = m.get("id", "unknown")
            model_name = m.get("name", model_id.title())
            model_type = m.get("type", "tabular")
            desc = m.get("description",
                f"{'Analyzes imaging data.' if model_type == 'image' else 'Analyzes tabular data.'}"
            )
            models.append((model_id, model_name, desc))
        return models if models else _default_models()
    except Exception:
        return _default_models()

def add_model_to_server(name, model_type="tabular"):
    """
    Sends a new custom model to the server.
    model_type: "tabular" or "image"
    Returns (success: bool, message: str)
    """
    model_id = name.strip().lower().replace(" ", "_")
    try:
        response = requests.post(
            f"{SERVER_URL}/add_model",
            json={
                "id":          model_id,
                "name":        name.strip(),
                "type":        model_type,
                "description": f"Custom model: {name.strip()}.",
            },
            timeout=10
        )
        data = response.json()
        if "error" in data:
            return False, data["error"]
        return True, data.get("status", "Model added")
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to server."
    except requests.exceptions.Timeout:
        return False, "Server timed out."
    except Exception as e:
        return False, str(e)

def _default_models():
    """Fallback if server is unreachable."""
    return [
        ("tumor", "Tumor Detection",     "Analyzes imaging data to identify and classify tumor regions."),
        ("heart", "Heart Disease Model", "Evaluates cardiac indicators to assess heart disease risk."),
    ]

# ================================
# 📊 TABULAR TRAINING
# ================================
def train_tabular(file_path, epochs, use_server_model=True, model_id=None):

    global trained_model, last_config, last_model_id, last_history

    data = pd.read_csv(file_path)

    for col in data.columns:
        if data[col].dtype == object:
            data[col] = pd.Categorical(data[col]).codes

    X = data.iloc[:, :-1].values
    y = data.iloc[:, -1].values

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
            config = suggest_model_config(X, y)

        config["num_classes"] = int(len(np.unique(y)))
        config["input_size"]  = int(X.shape[1])

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
    # 🚀 TRAIN — capture history
    # ================================
    history = model.fit(X, y, epochs=epochs, verbose=1)

    trained_model = model
    last_config   = config
    last_model_id = model_id
    last_history  = history.history   # NEW: e.g. {"loss": [...], "accuracy": [...]}

    return "Tabular training completed"



# ================================
# 🖼️ IMAGE TRAINING
# ================================
def train_image(folder_path, epochs, use_server_model=True, model_id="xray"):

    global trained_model, last_config, last_model_id, last_history

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
        if "type" not in config:
            config["type"] = "image"
        if "model" not in config:
            config["model"] = "cnn_small"
        if "output" not in config:
            config["output"] = "binary"
        config["input_size"] = [128, 128, 3]

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
        class_mode='binary',
        classes=['no', 'yes']
    )

    # ================================
    # TRAIN — capture history
    # ================================
    history = model.fit(train_data, epochs=epochs)

    trained_model = model
    last_config   = config
    last_model_id = model_id
    last_history  = history.history   # NEW: e.g. {"loss": [...], "accuracy": [...]}

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
            json={"weights": weights_list, "model_id": last_model_id or "unknown"},
            timeout=120
        )
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


# ================================
# 🔬 PREDICT FROM FILE  ← NEW
# ================================
def predict_from_file(path):
    """
    Run the trained model on a new dataset file.

    For tabular (.csv):
        - Encodes categoricals, normalises, runs each row through the model.
        - Returns list of (row_label, prediction_str, confidence_str).
        - If the file has a label column (last col) it is used as the row label
          so you can visually compare ground-truth vs prediction.

    For image (folder):
        - Expects sub-folders named 'no' and 'yes' (same convention as training).
        - Returns one result per image file found.

    Returns:
        list of (sample_label: str, prediction: str, confidence: str)
        On error raises an exception (caller handles it).
    """
    global trained_model, last_config

    if trained_model is None:
        raise RuntimeError("No trained model found. Please train a model first.")

    data_type = detect_data_type(path)

    # ── TABULAR ──────────────────────────────────────────────────────────
    if data_type == "tabular":
        data = pd.read_csv(path)

        for col in data.columns:
            if data[col].dtype == object:
                data[col] = pd.Categorical(data[col]).codes

        # Use the last column as ground-truth label if it exists
        if data.shape[1] > 1:
            labels = data.iloc[:, -1].values.astype(str)
            X = data.iloc[:, :-1].values.astype(float)
        else:
            labels = [f"Row {i+1}" for i in range(len(data))]
            X = data.values.astype(float)

        X = X / (np.max(X, axis=0) + 1e-8)

        raw = trained_model.predict(X)

        results = []
        output_type = last_config.get("output", "binary") if last_config else "binary"

        for i, (row_label, pred_raw) in enumerate(zip(labels, raw)):
            sample_lbl = f"Row {i+1} (GT: {row_label})"

            if output_type == "binary":
                prob = float(pred_raw[0])
                pred_str = "Disease Detected" if prob > 0.5 else "No Disease"
                conf_str = f"{prob*100:.1f}%"

            elif output_type == "multi_class":
                cls = int(np.argmax(pred_raw))
                prob = float(np.max(pred_raw))
                pred_str = f"Class {cls}"
                conf_str = f"{prob*100:.1f}%"

            else:  # regression
                val = float(pred_raw[0])
                pred_str = f"{val:.4f}"
                conf_str = "—"

            results.append((sample_lbl, pred_str, conf_str))

        return results

    # ── IMAGE ─────────────────────────────────────────────────────────────
    elif data_type == "image":
        from tensorflow.keras.preprocessing import image as keras_image

        EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff"}
        results = []

        # Walk the folder; try to detect label from sub-folder name
        for root, dirs, files in os.walk(path):
            for fname in sorted(files):
                if os.path.splitext(fname)[1].lower() not in EXTS:
                    continue
                fpath = os.path.join(root, fname)

                # Infer ground-truth label from parent folder name if available
                parent = os.path.basename(root)
                gt_str  = f" (GT: {parent})" if parent.lower() in ("yes", "no", "0", "1") else ""
                sample_lbl = fname + gt_str

                try:
                    img = keras_image.load_img(fpath, target_size=(128, 128))
                    arr = keras_image.img_to_array(img) / 255.0
                    arr = np.expand_dims(arr, axis=0)
                    pred_raw = trained_model.predict(arr, verbose=0)

                    output_type = last_config.get("output", "binary") if last_config else "binary"

                    if output_type == "binary":
                        prob = float(pred_raw[0][0])
                        pred_str = "Detected (Yes)" if prob > 0.5 else "Not Detected (No)"
                        conf_str = f"{prob*100:.1f}%"
                    elif output_type == "multi_class":
                        cls  = int(np.argmax(pred_raw[0]))
                        prob = float(np.max(pred_raw[0]))
                        pred_str = f"Class {cls}"
                        conf_str = f"{prob*100:.1f}%"
                    else:
                        val = float(pred_raw[0][0])
                        pred_str = f"{val:.4f}"
                        conf_str = "—"

                    results.append((sample_lbl, pred_str, conf_str))

                except Exception as img_err:
                    results.append((sample_lbl, f"Error: {img_err}", ""))

        if not results:
            raise RuntimeError(
                "No image files found in the selected folder.\n"
                "Make sure the folder contains .jpg / .png images "
                "(optionally in 'yes' / 'no' sub-folders)."
            )

        return results

    else:
        raise ValueError(f"Unsupported data format for path: {path}")
