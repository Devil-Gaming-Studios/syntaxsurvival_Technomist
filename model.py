import tensorflow as tf

# ================================
# 🔹 Main Builder Function
# ================================
def build_model_from_config(config):

    model_type = config.get("type")
    model_name = config.get("model")

    # ================================
    # 🟦 TABULAR MODELS
    # ================================
    if model_type == "tabular":

        input_size = int(config.get("input_size"))  # ✅ cast to plain Python int

        if model_name == "dense_small":
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(16, activation='relu', input_shape=(input_size,)),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])

        elif model_name == "dense_medium":
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(32, activation='relu', input_shape=(input_size,)),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])

        elif model_name == "dense_large":
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(64, activation='relu', input_shape=(input_size,)),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])

        else:
            raise ValueError("Unknown tabular model")

    # ================================
    # 🟩 IMAGE MODELS (CNN)
    # ================================
    elif model_type == "image":

        input_shape = tuple(int(x) for x in config.get("input_size", (128, 128, 3)))  # ✅ cast each dim

        if model_name == "cnn_small":
            model = tf.keras.Sequential([
                tf.keras.layers.Conv2D(32, (3,3), activation='relu', input_shape=input_shape),
                tf.keras.layers.MaxPooling2D(2,2),

                tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
                tf.keras.layers.MaxPooling2D(2,2),

                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])

        elif model_name == "cnn_medium":
            model = tf.keras.Sequential([
                tf.keras.layers.Conv2D(32, (3,3), activation='relu', input_shape=input_shape),
                tf.keras.layers.MaxPooling2D(2,2),

                tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
                tf.keras.layers.MaxPooling2D(2,2),

                tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
                tf.keras.layers.MaxPooling2D(2,2),

                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])

        else:
            raise ValueError("Unknown image model")

    else:
        raise ValueError("Unknown model type")

    # ================================
    # ⚙️ Compile Model
    # ================================
    loss = "binary_crossentropy"

    if config.get("output") == "multi_class":
        loss = "sparse_categorical_crossentropy"

    model.compile(
        optimizer='adam',
        loss=loss,
        metrics=['accuracy']
    )

    return model


# ================================
# 🔧 CUSTOM MODEL BUILDER
# ================================
def build_custom_model(input_size, layers, output_type="binary"):

    model = tf.keras.Sequential()

    model.add(tf.keras.layers.Input(shape=(int(input_size),)))  # ✅ cast to plain Python int

    for units in layers:
        model.add(tf.keras.layers.Dense(int(units), activation='relu'))  # ✅ cast each unit count

    if output_type == "binary":
        model.add(tf.keras.layers.Dense(1, activation='sigmoid'))
        loss = "binary_crossentropy"

    elif output_type == "multi_class":
        model.add(tf.keras.layers.Dense(3, activation='softmax'))
        loss = "sparse_categorical_crossentropy"

    else:
        model.add(tf.keras.layers.Dense(1))
        loss = "mse"

    model.compile(
        optimizer='adam',
        loss=loss,
        metrics=['accuracy']
    )

    return model


# ================================
# 🧠 AUTO MODEL SUGGESTION
# ================================
def suggest_model_config(X, y):

    import numpy as np

    config = {}

    if len(X.shape) == 2:
        config["type"] = "tabular"
        config["input_size"] = int(X.shape[1])          # ✅ was numpy.int64, now plain int

    elif len(X.shape) == 4:
        config["type"] = "image"
        config["input_size"] = [int(x) for x in X.shape[1:]]  # ✅ cast each dim

    unique_values = len(np.unique(y))

    if unique_values == 2:
        config["output"] = "binary"
    elif unique_values < 10:
        config["output"] = "multi_class"
    else:
        config["output"] = "regression"

    return config
