import os
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash
)
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_tu_app'

# ===========================
# 🔹 Sesión
# ===========================
app.permanent_session_lifetime = timedelta(minutes=30)


# ===========================
# 🔹 MySQL
# ===========================
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pure_ml'
mysql = MySQL(app)

# ===========================
# 🔹 Archivo de imágenes
# ===========================
UPLOAD_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ===========================
# 🔹 Rutas públicas
# ===========================
@app.route('/')
def root_redirect():
    return redirect(url_for('inicio'))


@app.route('/inicio')
def inicio():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM productos WHERE activo = 1')
    productos = cur.fetchall()
    return render_template('inicio.html', productos=productos)


@app.route('/quienes')
def quienes():
    return render_template('quienes.html')


@app.route('/catalogo')
def catalogo():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM productos WHERE activo = 1')
    productos = cur.fetchall()
    return render_template('catalogo.html', productos=productos)


# ===========================
# 🔹 Login (simple, sin hash)
# ===========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            'SELECT * FROM admin WHERE usuario=%s AND contrasena=%s LIMIT 1',
            (usuario, contrasena)
        )
        account = cur.fetchone()

        if account:
            session['logueado'] = True
            session['usuario'] = account['usuario']
            flash('Inicio de sesión exitoso ✅', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos ❌', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))


# ===========================
# 🔹 Dashboard Admin
# ===========================
@app.route('/dashboard')
def dashboard():
    if 'logueado' not in session:
        flash('Debe iniciar sesión para acceder.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()

    cur.execute('SELECT * FROM pedidos ORDER BY fecha_pedido DESC')
    pedidos = cur.fetchall()

    return render_template('dashboard.html', productos=productos, pedidos=pedidos)


# ===========================
# 🔹 CRUD Productos
# ===========================
@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'logueado' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    presentacion = request.form['presentacion']
    precio = request.form['precio']
    stock = request.form['stock']
    activo = 1 if request.form.get('activo') == 'on' else 0

    imagen = request.files.get('imagen')
    filename = None
    if imagen and allowed_file(imagen.filename):
        filename = imagen.filename
        imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        '''INSERT INTO productos (nombre, descripcion, presentacion, precio, imagen, stock, activo)
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (nombre, descripcion, presentacion, precio, filename, stock, activo)
    )
    mysql.connection.commit()
    flash('Producto agregado correctamente ✅', 'success')
    return redirect(url_for('dashboard'))


@app.route('/actualizar_productos', methods=['POST'])
def actualizar_productos():
    if 'logueado' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    for key, value in request.form.items():
        if key.startswith('nombre_'):
            _id = key.split('_', 1)[1]
            nombre = value
            descripcion = request.form.get(f'descripcion_{_id}')
            presentacion = request.form.get(f'presentacion_{_id}')
            stock = request.form.get(f'stock_{_id}')
            precio = request.form.get(f'precio_{_id}')
            activo = 1 if request.form.get(f'activo_{_id}') else 0

            cur.execute(
                '''UPDATE productos 
                   SET nombre=%s, descripcion=%s, presentacion=%s, stock=%s, precio=%s, activo=%s
                   WHERE id=%s''',
                (nombre, descripcion, presentacion, stock, precio, activo, _id)
            )
    mysql.connection.commit()
    flash('Productos actualizados correctamente ✅', 'success')
    return redirect(url_for('dashboard'))


@app.route('/eliminar_producto/<int:pid>')
def eliminar_producto(pid):
    if 'logueado' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('DELETE FROM productos WHERE id=%s', (pid,))
    mysql.connection.commit()
    flash('Producto eliminado ❌', 'info')
    return redirect(url_for('dashboard'))


# ===========================
# 🔹 Carrito y pedidos
# ===========================
@app.route('/carrito')
def carrito():
    cart = session.get('cart', {})
    if not cart:
        return render_template('carrito.html', productos=[], total=0, cart_count=0)

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ids = tuple(cart.keys())
    query = f"SELECT * FROM productos WHERE id IN {ids}"
    cur.execute(query)
    productos_db = cur.fetchall()

    productos = []
    total = 0
    for p in productos_db:
        pid = str(p['id'])
        cantidad = cart.get(pid, 0)
        subtotal = float(p['precio']) * cantidad
        total += subtotal
        productos.append({
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': p['precio'],
            'cantidad': cantidad,
            'subtotal': subtotal
        })

    return render_template('carrito.html', productos=productos, total=round(total, 2), cart_count=len(cart))


@app.route('/carrito_agregar', methods=['POST'])
def carrito_agregar():
    producto_id = request.form.get('producto_id')
    cantidad = int(request.form.get('cantidad', 1))

    cart = session.get('cart', {})
    cart[producto_id] = cart.get(producto_id, 0) + cantidad

    session['cart'] = cart
    session.modified = True

    flash('Producto agregado al carrito 🛒', 'success')
    return redirect(url_for('catalogo'))


@app.route('/pedido_desde_carrito', methods=['GET', 'POST'])
def pedido_desde_carrito():
    cart = session.get('cart', {})
    if not cart:
        flash('Tu carrito está vacío. Agrega productos antes de continuar.', 'warning')
        return redirect(url_for('catalogo'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ids = tuple(cart.keys())
    query = f"SELECT * FROM productos WHERE id IN {ids}"
    cur.execute(query)
    productos_db = cur.fetchall()

    productos = []
    total = 0
    for p in productos_db:
        pid = str(p['id'])
        cantidad = cart.get(pid, 0)
        subtotal = float(p['precio']) * cantidad
        total += subtotal
        productos.append({
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': p['precio'],
            'cantidad': cantidad,
            'subtotal': subtotal
        })

    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']

        cur.execute("""
            INSERT INTO pedidos (cliente_nombre, cliente_email, cliente_telefono, total)
            VALUES (%s, %s, %s, %s)
        """, (nombre, email, telefono, total))
        mysql.connection.commit()
        pedido_id = cur.lastrowid

        for item in productos:
            cur.execute("""
                INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, subtotal)
                VALUES (%s, %s, %s, %s)
            """, (pedido_id, item['id'], item['cantidad'], item['subtotal']))
        mysql.connection.commit()

        mensaje = f"Hola, soy {nombre}. Mi pedido es:%0A"
        for item in productos:
            mensaje += f"- {item['cantidad']} x {item['nombre']} = ${item['subtotal']:.2f}%0A"
        mensaje += f"%0ATotal: ${total:.2f}%0AEmail: {email}%0ATeléfono: {telefono}"
        whatsapp_url = f"https://wa.me/573012373875?text={mensaje}"

        session['cart'] = {}
        session.modified = True

        return redirect(whatsapp_url)

    return render_template('pedido_carrito.html', productos=productos, total=round(total, 2))
@app.route('/prediccion')
def prediccion():
    return "<h2>Sección de predicción próximamente...</h2>"


# ===========================
# 🔹 Main
# ===========================
if __name__ == '__main__':
    app.run(debug=True)
