from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_tu_app'

# ------------------------------
# 🔹 Configuración de conexión MySQL (XAMPP)
# ------------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # Deja vacío si no tienes contraseña
app.config['MYSQL_DB'] = 'pure_ml'

mysql = MySQL(app)

# ------------------------------
# 🔹 Página principal (Información institucional)
# ------------------------------
@app.route('/')
def inicio():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    return render_template('base.html', productos=productos)


# ------------------------------
# 🔹 Catálogo público
# ------------------------------
@app.route('/catalogo')
def catalogo():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    return render_template('catalogo.html', productos=productos)

# ------------------------------
# 🔹 Pedido (selección con menú y WhatsApp)
# ------------------------------
@app.route('/pedido', methods=['GET', 'POST'])
def pedido():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id, nombre, precio FROM productos')
    productos = cursor.fetchall()

    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        producto_id = request.form['producto_id']
        cantidad = int(request.form['cantidad'])

        # Obtener información del producto
        cursor.execute('SELECT nombre, precio FROM productos WHERE id = %s', [producto_id])
        producto = cursor.fetchone()
        if not producto:
            flash('Producto no encontrado.', 'danger')
            return redirect(url_for('pedido'))

        total = producto['precio'] * cantidad

        # Guardar pedido en la base de datos
        cursor.execute(
            'INSERT INTO pedidos (cliente_nombre, cliente_telefono, producto_id, cantidad, total) VALUES (%s, %s, %s, %s, %s)',
            (nombre, telefono, producto_id, cantidad, total)
        )
        mysql.connection.commit()

        # Crear link de WhatsApp
        numero_whatsapp = "573223052867"  # Cambia este número por el real
        mensaje = (
            f"Hola, soy {nombre}.%0A"
            f"Quiero pedir {cantidad} unidades de {producto['nombre']}.%0A"
            f"💰 Precio unitario: ${producto['precio']:.2f}%0A"
            f"💵 Total a pagar: ${total:.2f}"
        )
        link = f"https://wa.me/{numero_whatsapp}?text={mensaje}"

        flash('Pedido enviado correctamente. Serás redirigido a WhatsApp.', 'success')
        return redirect(link)

    return render_template('pedido.html', productos=productos)

# ------------------------------
# 🔹 Login de administrador
# ------------------------------
@app.route('/login', methods=['GET', 'POST'])
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

# ------------------------------
# 🔹 Dashboard (Solo Admin)
# ------------------------------
@app.route('/dashboard')
def dashboard():
    if 'logueado' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM productos')
        productos = cursor.fetchall()
        return render_template('dashboard.html', productos=productos)
    else:
        return redirect(url_for('login'))

# ------------------------------
# 🔹 Cerrar sesión
# ------------------------------
@app.route('/logout')
def logout():
    session.pop('logueado', None)
    session.pop('usuario', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('inicio'))

# ------------------------------
# 🔹 Cargar modelo de Machine Learning
# ------------------------------
with open('ml_models/regression_model.pkl', 'rb') as f:
    modelo_regresion = pickle.load(f)

@app.route('/prediccion', methods=['GET', 'POST'])
def prediccion():
    if request.method == 'POST':
        tipo = int(request.form['tipo_camote'])
        humedad = float(request.form['humedad'])
        lote = float(request.form['tamano_lote'])

        # Preparar datos para el modelo
        entrada = np.array([[tipo, humedad, lote]])
        prediccion = modelo_regresion.predict(entrada)[0]

        return render_template('prediccion.html', resultado=round(prediccion, 2))

    return render_template('prediccion.html')

@app.route('/quienes')
def quienes():
    return render_template('quienes.html')


# ------------------------------
# 🔹 Main
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
