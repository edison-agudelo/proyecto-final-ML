import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
import os

# ======================================================
# 📁 Configuración de rutas
# ======================================================
# Asegúrate de que el dataset está dentro de ml_models/dataset
dataset_dir = os.path.join('ml_models', 'dataset')

# Validar que la carpeta exista
if not os.path.exists(dataset_dir):
    raise FileNotFoundError(f"No se encontró la carpeta del dataset en: {dataset_dir}")

# ======================================================
# ⚙️ Preprocesamiento de imágenes
# ======================================================
datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=25,
    width_shift_range=0.2,
    height_shift_range=0.2,
    zoom_range=0.2,
    shear_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

train_data = datagen.flow_from_directory(
    dataset_dir,
    target_size=(128, 128),
    batch_size=8,
    class_mode='categorical',
    subset='training'
)

val_data = datagen.flow_from_directory(
    dataset_dir,
    target_size=(128, 128),
    batch_size=8,
    class_mode='categorical',
    subset='validation'
)

# ======================================================
# 🧠 Definición del modelo CNN (multiclase)
# ======================================================
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
    MaxPooling2D(2,2),

    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2,2),

    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.3),
    Dense(train_data.num_classes, activation='softmax')  # Detecta automáticamente el número de clases
])

# ======================================================
# 🧩 Compilación y entrenamiento
# ======================================================
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("\n🚀 Entrenando modelo CNN...")
history = model.fit(train_data, validation_data=val_data, epochs=15)
print("\n✅ Entrenamiento finalizado correctamente.")

# ======================================================
# 💾 Guardar modelo actualizado
# ======================================================
os.makedirs('ml_models', exist_ok=True)
model.save('ml_models/cnn_model.keras')


print("\n✅ Modelo multiclase entrenado y guardado en 'ml_models/cnn_model.keras'")

import json

# ======================================================
# 📊 Guardar métricas del entrenamiento
# ======================================================
metrics_data = {
    "accuracy": history.history["accuracy"],
    "val_accuracy": history.history["val_accuracy"],
    "loss": history.history["loss"],
    "val_loss": history.history["val_loss"]
}

# Guardamos el JSON en la carpeta ml_models
with open(os.path.join("ml_models", "training_metrics.json"), "w") as f:
    json.dump(metrics_data, f)

print("\n📊 Métricas de entrenamiento guardadas en 'ml_models/training_metrics.json'")
