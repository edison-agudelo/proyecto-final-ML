import os
import json
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout

# ==========================================
# 📂 1. Ruta del dataset
# ==========================================
data_dir = "ml_models/dataset"

# ==========================================
# 🔧 2. Preprocesamiento + Aumentación
# ==========================================
datagen = ImageDataGenerator(
    rescale=1.0/255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2   # 80% train, 20% test
)

train = datagen.flow_from_directory(
    data_dir,
    target_size=(128, 128),
    batch_size=8,
    class_mode="categorical",
    subset="training",
    shuffle=True
)

val = datagen.flow_from_directory(
    data_dir,
    target_size=(128, 128),
    batch_size=8,
    class_mode="categorical",
    subset="validation",
    shuffle=True
)

print("\n🔍 Clases detectadas:", train.class_indices)

# ==========================================
# 🧠 3. Arquitectura CNN optimizada
# ==========================================
model = Sequential([
    
    Conv2D(32, (3, 3), activation='relu', input_shape=(128,128,3)),
    MaxPooling2D(),

    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(),

    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D(),

    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),

    Dense(train.num_classes, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ==========================================
# 🏋️ 4. Entrenamiento
# ==========================================
history = model.fit(
    train,
    validation_data=val,
    epochs=20
)

# ==========================================
# 💾 5. Guardar modelo en formato H5
# ==========================================
output_path = os.path.join("ml_models", "cnn_model.h5")
model.save(output_path)

print(f"\n✅ Modelo guardado correctamente en: {output_path}")

# ==========================================
# 📝 6. Guardar las clases para Flask
# ==========================================
class_json_path = os.path.join("ml_models", "class_indices.json")
with open(class_json_path, "w") as f:
    json.dump(train.class_indices, f, indent=4)

print(f"📁 Clases guardadas en: {class_json_path}")
