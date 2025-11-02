import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import pickle

# Simulación de datos (puedes reemplazar con tus datos reales del producto)
data = {
    'tipo_camote': [0, 1, 0, 1, 0, 1],  # 0 = yuca, 1 = camote
    'humedad': [40, 50, 42, 55, 44, 53],
    'tamano_lote': [10, 15, 20, 25, 30, 35],
    'tiempo_coccion': [20, 30, 22, 33, 25, 36]  # objetivo
}

df = pd.DataFrame(data)

#  Variables predictoras (X) y variable objetivo (y)
X = df[['tipo_camote', 'humedad', 'tamano_lote']]
y = df['tiempo_coccion']

#  Entrenar modelo
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
modelo = LinearRegression()
modelo.fit(X_train, y_train)

#  Guardar modelo entrenado
with open('ml_models/regression_model.pkl', 'wb') as f:
    pickle.dump(modelo, f)

print(" Modelo de regresión entrenado y guardado correctamente.")
