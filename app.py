from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pickle
import numpy as np
import os
import base64
from io import BytesIO
from PIL import Image
from tensorflow.keras.models import load_model

# ------------------------------------------------------
# CONFIGURACIÓN PRINCIPAL
# ------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'clave_secreta_para_tu_app'

# Configuración conexión MySQL (XAMPP)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''      # si tu MySQL no tiene contraseña
app.config['MYSQL_DB'] = 'pure_ml'

mysql = MySQL(app)

# ------------------------------------------------------
# LOGIN
# ------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM admin WHERE usuario = %s AND contrasena = %s',
            (usuario, contrasena)
        )
        cuenta = cursor.fetchone()
        cursor.close()

        if cuenta:
            session['logueado'] = True
            session['usuario'] = cuenta['usuario']
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')

# ------------------------------------------------------
# DASHBOARD (solo admin)
# ------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'logueado' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM productos')
        productos = cursor.fetchall()
        cursor.close()
        return render_template('dashboard.html', productos=productos)

    return redirect(url_for('login'))

# ------------------------------------------------------
# CATÁLOGO PÚBLICO
# ------------------------------------------------------
@app.route('/catalogo')
def catalogo():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    cursor.close()
    return render_template('catalogo.html', productos=productos)

# ------------------------------------------------------
# PEDIDOS (guarda en BD y redirige a WhatsApp)
# ------------------------------------------------------
@app.route('/pedido', methods=['GET', 'POST'])
def pedido():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        producto = request.form['producto']
        cantidad = request.form['cantidad']

        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO pedidos (nombre_cliente, telefono, producto, cantidad) '
            'VALUES (%s,%s,%s,%s)',
            (nombre, telefono, producto, cantidad)
        )
        mysql.connection.commit()
        cursor.close()

        numero_whatsapp = "573001112233"
        mensaje = f"Hola, soy {nombre}. Quiero pedir {cantidad} unidades de {producto}."
        link = f"https://wa.me/{numero_whatsapp}?text={mensaje}"
        return redirect(link)

    return render_template('pedido.html')

# ------------------------------------------------------
# CERRAR SESIÓN
# ------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------------------------------------------
# PREDICCIÓN (MODELO DE REGRESIÓN)
# ------------------------------------------------------
try:
    with open('ml_models/regression_model.pkl', 'rb') as f:
        modelo_regresion = pickle.load(f)
except Exception:
    modelo_regresion = None
    print("⚠ No se pudo cargar regression_model.pkl")

@app.route('/prediccion', methods=['GET', 'POST'])
def prediccion():
    resultado = None
    if request.method == 'POST' and modelo_regresion:
        try:
            tipo = float(request.form['tipo_camote'])
            humedad = float(request.form['humedad'])
            lote = float(request.form['tamano_lote'])
            entrada = np.array([[tipo, humedad, lote]])
            resultado = round(float(modelo_regresion.predict(entrada)[0]), 2)
        except Exception as e:
            flash(f"Error en la predicción: {e}", 'danger')

    return render_template('prediccion.html', resultado=resultado)

# ------------------------------------------------------
# CARGA DEL MODELO CNN
# ------------------------------------------------------
cnn_model_path = os.path.join("ml_models", "cnn_model.h5")

if os.path.exists(cnn_model_path):
    try:
        cnn_model = load_model(cnn_model_path)
        print("✅ Modelo CNN cargado correctamente.")
    except Exception as e:
        cnn_model = None
        print("⚠ Error cargando el modelo CNN:", e)
else:
    cnn_model = None
    print("⚠ Modelo CNN NO encontrado:", cnn_model_path)

# ------------------------------------------------------
# CONTROL DE CALIDAD (CNN + CÁMARA)
# ------------------------------------------------------
@app.route('/calidad', methods=['GET', 'POST'])
def calidad():
    resultado = None

    if request.method == 'POST':
        if not cnn_model:
            flash('Modelo de control de calidad no disponible.', 'danger')
            return render_template('calidad.html', resultado=resultado)

        img_data = request.form.get('imagen')

        if img_data:
            try:
                # Decodificar imagen base64 desde la cámara
                img_data = img_data.split(',')[1]
                img = Image.open(BytesIO(base64.b64decode(img_data))).convert("RGB")
                img = img.resize((128, 128))
                img_array = np.array(img) / 255.0
                img_array = np.expand_dims(img_array, axis=0)

                pred = float(cnn_model.predict(img_array)[0][0])

                # pred ~ 0 -> mala, ~1 -> buena  (ajustamos según como entrenaste)
                if pred >= 0.5:
                    resultado = "✅ Buena calidad"
                else:
                    resultado = "❌ Mala calidad"

            except Exception as e:
                resultado = f"⚠ Error procesando imagen: {e}"

    return render_template('calidad.html', resultado=resultado)

# ------------------------------------------------------
# CHATBOT (no guarda mensajes, solo responde)
# ------------------------------------------------------

def responder_chatbot(mensaje: str) -> str:
    """Reglas simples para el chatbot de atención al cliente."""
    msg = mensaje.lower()

    # SALUDOS
    if any(pal in msg for pal in ["hola", "buenas", "buenos días", "buenas tardes"]):
        return "¡Hola! 👋 Soy el asistente del Puré Inteligente. ¿Quieres ayuda con productos, pedidos o calidad del puré?"

    # CATÁLOGO / PRODUCTOS
    if any(pal in msg for pal in ["catálogo", "catalogo", "producto", "productos", "tienen"]):
        return "Tenemos puré de yuca y puré de camote en diferentes presentaciones. Puedes ver el catálogo completo en el menú «Catálogo»."

    # PRECIOS
    if "precio" in msg or "cuánto vale" in msg or "cuanto vale" in msg:
        return "Los precios están actualizados en el catálogo. Entra al menú «Catálogo» para ver cada producto con su valor. 😊"

    # PEDIDOS
    if "pedido" in msg or "comprar" in msg or "compra" in msg or "encargar" in msg:
        return "Para hacer un pedido, ve al menú «Catálogo» o «Pedido». Ahí puedes registrar tu pedido y te enviamos a WhatsApp para confirmarlo. 🛒"

    # CALIDAD / CNN
    if any(pal in msg for pal in ["calidad", "dañado", "dañada", "malo", "mala", "bueno", "buena", "camote", "yuca"]):
        return ("Usamos una cámara con un modelo de Visión por Computador (CNN) "
                "que analiza la imagen de la yuca o el camote y te dice si está en buena "
                "o mala calidad para hacer el puré. Solo entra a «Control de Calidad» y toma una foto. 📷")

    # CONTACTO
    if "whatsapp" in msg or "contacto" in msg or "teléfono" in msg or "telefono" in msg:
        return "Puedes contactarnos al WhatsApp 📱 3001112233 para dudas especiales o pedidos grandes."

    # AYUDA GENÉRICA
    if "ayuda" in msg or "no entiendo" in msg or "explica" in msg:
        return "Claro, puedo ayudarte con: catálogo, precios, cómo hacer un pedido, o cómo funciona el control de calidad. ¿Sobre qué tema quieres saber?"

    # RESPUESTA POR DEFECTO
    return ("Interesante 🤔. Puedo ayudarte con información de productos, precios, pedidos "
            "y con el funcionamiento del control de calidad del puré. ¿Sobre qué quieres preguntar?")

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({"respuesta": "No recibí ningún mensaje 😅. Escribe algo y con gusto te ayudo."})

    respuesta = responder_chatbot(mensaje)
    # No guardamos nada en BD, solo respondemos
    return jsonify({"respuesta": respuesta})

# ------------------------------------------------------
# RUN
# ------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
