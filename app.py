from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pickle
import numpy as np
import os
import base64
from io import BytesIO
from PIL import Image
from keras.models import load_model
from keras.preprocessing import image


# ------------------------------------------------------
# CONFIGURACIÓN PRINCIPAL
# ------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'clave_secreta_para_tu_app'

# Configuración de conexión MySQL (XAMPP)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # deja vacío si no tienes contraseña
app.config['MYSQL_DB'] = 'pure_ml'

mysql = MySQL(app)

# ------------------------------------------------------
# RUTA PRINCIPAL (LOGIN)
# ------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM admin WHERE usuario = %s AND contrasena = %s', (usuario, contrasena))
            cuenta = cursor.fetchone()
            cursor.close()
        except Exception as e:
            flash('Error de conexión a la base de datos', 'danger')
            return render_template('login.html')

        if cuenta:
            session['logueado'] = True
            session['usuario'] = cuenta['usuario']
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')

# ------------------------------------------------------
# DASHBOARD (SOLO ADMIN)
# ------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'logueado' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM productos')
            productos = cursor.fetchall()
            cursor.close()
            return render_template('dashboard.html', productos=productos)
        except Exception as e:
            flash('Error al cargar productos: ' + str(e), 'danger')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

# ------------------------------------------------------
# CATÁLOGO PÚBLICO
# ------------------------------------------------------
@app.route('/catalogo')
def catalogo():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM productos')
        productos = cursor.fetchall()
        cursor.close()
        return render_template('catalogo.html', productos=productos)
    except Exception as e:
        flash('Error al cargar el catálogo: ' + str(e), 'danger')
        return redirect(url_for('login'))

# ------------------------------------------------------
# PEDIDOS CON WHATSAPP
# ------------------------------------------------------
@app.route('/pedido', methods=['GET', 'POST'])
def pedido():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        producto = request.form['producto']
        cantidad = request.form['cantidad']

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                'INSERT INTO pedidos (nombre_cliente, telefono, producto, cantidad) VALUES (%s, %s, %s, %s)',
                (nombre, telefono, producto, cantidad)
            )
            mysql.connection.commit()
            cursor.close()
        except Exception as e:
            flash('Error al guardar el pedido: ' + str(e), 'danger')
            return redirect(url_for('catalogo'))

        # Generar link de WhatsApp (reemplaza con número real del cliente)
        numero_whatsapp = "573001112233"  # Ejemplo Colombia
        mensaje = f"Hola, soy {nombre}. Quiero pedir {cantidad} unidades de {producto}."
        link = f"https://wa.me/{numero_whatsapp}?text={mensaje}"

        flash('Pedido enviado correctamente. Serás redirigido a WhatsApp.', 'success')
        return redirect(link)

    return render_template('pedido.html')

# ------------------------------------------------------
# CERRAR SESIÓN
# ------------------------------------------------------
@app.route('/logout')
def logout():
    session.pop('logueado', None)
    session.pop('usuario', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))

# ------------------------------------------------------
# MODELO DE REGRESIÓN SUPERVISADA (PREDICCIÓN)
# ------------------------------------------------------
try:
    with open('ml_models/regression_model.pkl', 'rb') as f:
        modelo_regresion = pickle.load(f)
except:
    modelo_regresion = None

@app.route('/prediccion', methods=['GET', 'POST'])
def prediccion():
    resultado = None
    if request.method == 'POST' and modelo_regresion:
        tipo = float(request.form['tipo_camote'])
        humedad = float(request.form['humedad'])
        lote = float(request.form['tamano_lote'])

        entrada = np.array([[tipo, humedad, lote]])
        prediccion = modelo_regresion.predict(entrada)[0]
        resultado = round(prediccion, 2)

    return render_template('prediccion.html', resultado=resultado)

# ------------------------------------------------------
# MODELO CNN (CONTROL DE CALIDAD AUTOMATIZADO CON CÁMARA)
# ------------------------------------------------------
cnn_model_path = 'ml_models/cnn_model.h5'
cnn_model = None
if os.path.exists(cnn_model_path):
    cnn_model = load_model(cnn_model_path)

@app.route('/calidad', methods=['GET', 'POST'])
def calidad():
    resultado = None
    if request.method == 'POST':
        if not cnn_model:
            flash('Modelo de control de calidad no disponible.', 'danger')
            return render_template('calidad.html')

        img_data = request.form['imagen']
        if img_data:
            try:
                # Decodificar imagen base64 enviada desde la cámara
                img_data = img_data.split(',')[1]
                img = Image.open(BytesIO(base64.b64decode(img_data)))
                img = img.resize((128, 128))
                img_array = np.array(img) / 255.0
                img_array = np.expand_dims(img_array, axis=0)

                # Predicción CNN
                prediccion = cnn_model.predict(img_array)[0][0]
                resultado = " Buena calidad" if prediccion < 0.5 else "❌ Mala calidad"
            except Exception as e:
                resultado = f"Error procesando imagen: {e}"

    return render_template('calidad.html', resultado=resultado)

# ------------------------------------------------------
# INICIO DE APLICACIÓN
# ------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
