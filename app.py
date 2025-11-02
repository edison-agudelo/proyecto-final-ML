from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_tu_app'

# Configuración de conexión MySQL (XAMPP)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # deja vacío si no tienes contraseña
app.config['MYSQL_DB'] = 'pure_ml'

mysql = MySQL(app)

# Ruta principal (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin WHERE usuario = %s AND contrasena = %s', (usuario, contrasena))
        cuenta = cursor.fetchone()

        if cuenta:
            session['logueado'] = True
            session['usuario'] = cuenta['usuario']
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')

# Ruta del dashboard (solo admin)
@app.route('/dashboard')
def dashboard():
    if 'logueado' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM productos')
        productos = cursor.fetchall()
        return render_template('dashboard.html', productos=productos)
    else:
        return redirect(url_for('login'))

# Ruta del catálogo público
@app.route('/catalogo')
def catalogo():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    return render_template('catalogo.html', productos=productos)

# Ruta del pedido (WhatsApp)
@app.route('/pedido', methods=['GET', 'POST'])
def pedido():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        producto = request.form['producto']
        cantidad = request.form['cantidad']

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO pedidos (nombre_cliente, telefono, producto, cantidad) VALUES (%s, %s, %s, %s)',
                       (nombre, telefono, producto, cantidad))
        mysql.connection.commit()

        # Generar link de WhatsApp (reemplaza con número real del cliente)
        numero_whatsapp = "573001112233"  # Ejemplo Colombia
        mensaje = f"Hola, soy {nombre}. Quiero pedir {cantidad} unidades de {producto}."
        link = f"https://wa.me/{numero_whatsapp}?text={mensaje}"

        flash('Pedido enviado correctamente. Serás redirigido a WhatsApp.', 'success')
        return redirect(link)

    return render_template('pedido.html')

#  Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('logueado', None)
    session.pop('usuario', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))

import pickle
import numpy as np

# 🔹 Cargar modelo entrenado
with open('ml_models/regression_model.pkl', 'rb') as f:
    modelo_regresion = pickle.load(f)

@app.route('/prediccion', methods=['GET', 'POST'])
def prediccion():
    if request.method == 'POST':
        tipo = int(request.form['tipo_camote'])
        humedad = float(request.form['humedad'])
        lote = float(request.form['tamano_lote'])

        # Preparar datos
        entrada = np.array([[tipo, humedad, lote]])
        prediccion = modelo_regresion.predict(entrada)[0]

        return render_template('prediccion.html', resultado=round(prediccion, 2))

    return render_template('prediccion.html')

if __name__ == '__main__':
    app.run(debug=True)
