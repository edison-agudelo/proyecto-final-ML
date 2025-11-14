import os
import base64
import pickle
import json
import numpy as np
import sqlite3
from io import BytesIO
from PIL import Image
from datetime import timedelta
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g, jsonify
)
from tensorflow.keras.models import load_model

# =======================================================
# 🌿 CONFIGURACIÓN PRINCIPAL
# =======================================================
app = Flask(__name__)
app.secret_key = 'clave_secreta_para_tu_app'
app.permanent_session_lifetime = timedelta(minutes=30)

# =======================================================
# 📌 CONFIG SQLITE (Render-friendly)
# =======================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "pure_ml.db")
print(">>> Ruta BD:", DB_PATH)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db:
        db.close()

# =======================================================
# 📁 CONFIG IMÁGENES
# =======================================================
UPLOAD_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =======================================================
# 🔹 RUTAS PÚBLICAS
# =======================================================
@app.route('/')
def root_redirect():
    return redirect(url_for('inicio'))

@app.route('/inicio')
def inicio():
    db = get_db()
    productos = db.execute("SELECT * FROM productos WHERE activo = 1").fetchall()
    return render_template('inicio.html', productos=productos)

@app.route('/quienes')
def quienes():
    return render_template('quienes.html')

@app.route('/catalogo')
def catalogo():
    db = get_db()
    productos = db.execute("SELECT * FROM productos WHERE activo = 1").fetchall()
    return render_template('catalogo.html', productos=productos)

# =======================================================
# 🔐 LOGIN
# =======================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')

        db = get_db()
        cuenta = db.execute(
            "SELECT * FROM admin WHERE usuario=? AND contrasena=? LIMIT 1",
            (usuario, contrasena)
        ).fetchone()

        if cuenta:
            session['logueado'] = True
            session['usuario'] = cuenta['usuario']
            flash("Inicio de sesión exitoso ✅", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña incorrectos ❌", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('login'))

# =======================================================
# 🧭 DASHBOARD ADMIN
# =======================================================
@app.route('/dashboard')
def dashboard():
    if 'logueado' not in session:
        flash("Debe iniciar sesión para acceder al panel.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    productos = db.execute("SELECT * FROM productos").fetchall()
    pedidos = db.execute("SELECT * FROM pedidos ORDER BY fecha_pedido DESC").fetchall()

    metrics_path = os.path.join("ml_models", "training_metrics.json")
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

    return render_template("dashboard.html", productos=productos, pedidos=pedidos, metrics=metrics)

# =======================================================
# 🧾 CRUD PRODUCTOS
# =======================================================
@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'logueado' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    presentacion = request.form['presentacion']
    precio = request.form['precio']
    stock = request.form['stock']
    activo = 1 if request.form.get('activo') else 0

    imagen = request.files.get('imagen')
    filename = None
    if imagen and allowed_file(imagen.filename):
        filename = imagen.filename
        imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    db = get_db()
    db.execute("""
        INSERT INTO productos (nombre, descripcion, presentacion, precio, imagen, stock, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nombre, descripcion, presentacion, precio, filename, stock, activo))
    db.commit()

    flash("Producto agregado correctamente ✅", "success")
    return redirect(url_for('dashboard'))

@app.route('/actualizar_productos', methods=['POST'])
def actualizar_productos():
    if 'logueado' not in session:
        return redirect(url_for('login'))

    db = get_db()

    for key, value in request.form.items():
        if key.startswith("nombre_"):
            pid = key.split("_")[1]
            nombre = value
            descripcion = request.form.get(f"descripcion_{pid}")
            presentacion = request.form.get(f"presentacion_{pid}")
            stock = request.form.get(f"stock_{pid}")
            precio = request.form.get(f"precio_{pid}")
            activo = 1 if request.form.get(f"activo_{pid}") else 0

            db.execute("""
                UPDATE productos SET nombre=?, descripcion=?, presentacion=?, 
                stock=?, precio=?, activo=? WHERE id=?
            """, (nombre, descripcion, presentacion, stock, precio, activo, pid))

    db.commit()
    flash("Productos actualizados correctamente ✅", "success")
    return redirect(url_for('dashboard'))

@app.route('/eliminar_producto/<int:pid>')
def eliminar_producto(pid):
    if 'logueado' not in session:
        return redirect(url_for('login'))

    db = get_db()
    db.execute("DELETE FROM productos WHERE id=?", (pid,))
    db.commit()

    flash("Producto eliminado ❌", "info")
    return redirect(url_for('dashboard'))

# =======================================================
# 🛒 CARRITO + PEDIDOS
# =======================================================
@app.route('/carrito')
def carrito():
    cart = session.get('cart', {})
    if not cart:
        return render_template("carrito.html", productos=[], total=0, cart_count=0)

    ids = list(cart.keys())
    placeholders = ",".join(["?"] * len(ids))

    db = get_db()
    productos_db = db.execute(f"SELECT * FROM productos WHERE id IN ({placeholders})", ids).fetchall()

    productos = []
    total = 0

    for p in productos_db:
        pid = str(p['id'])
        cantidad = cart.get(pid, 0)
        subtotal = float(p['precio']) * cantidad
        total += subtotal
        productos.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "precio": p["precio"],
            "cantidad": cantidad,
            "subtotal": subtotal
        })

    return render_template("carrito.html", productos=productos, total=round(total, 2), cart_count=len(cart))

@app.route('/carrito_agregar', methods=['POST'])
def carrito_agregar():
    producto_id = request.form.get("producto_id")
    cantidad = int(request.form.get("cantidad", 1))

    cart = session.get("cart", {})
    cart[producto_id] = cart.get(producto_id, 0) + cantidad

    session["cart"] = cart
    session.modified = True

    flash("Producto agregado al carrito 🛒", "success")
    return redirect(url_for('catalogo'))

@app.route('/pedido_desde_carrito', methods=['GET', 'POST'])
def pedido_desde_carrito():
    cart = session.get("cart", {})
    if not cart:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for('catalogo'))

    ids = list(cart.keys())
    placeholders = ",".join(["?"] * len(ids))

    db = get_db()
    productos_db = db.execute(f"SELECT * FROM productos WHERE id IN ({placeholders})", ids).fetchall()

    productos = []
    total = 0
    for p in productos_db:
        pid = str(p['id'])
        cantidad = cart.get(pid, 0)
        subtotal = float(p['precio']) * cantidad
        productos.append({
            "id": p['id'],
            "nombre": p['nombre'],
            "precio": p['precio'],
            "cantidad": cantidad,
            "subtotal": subtotal
        })
        total += subtotal

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]

        db.execute("""
            INSERT INTO pedidos (cliente_nombre, cliente_email, cliente_telefono, total)
            VALUES (?, ?, ?, ?)
        """, (nombre, email, telefono, total))
        pedido_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        for item in productos:
            db.execute("""
                INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, subtotal)
                VALUES (?, ?, ?, ?)
            """, (pedido_id, item["id"], item["cantidad"], item["subtotal"]))

        db.commit()

        mensaje = f"Hola, soy {nombre}. Mi pedido es:%0A"
        for item in productos:
            mensaje += f"- {item['cantidad']} x {item['nombre']} = ${item['subtotal']:.2f}%0A"

        mensaje += f"%0ATotal: ${total:.2f}%0AEmail: {email}%0ATeléfono: {telefono}"

        whatsapp_url = f"https://wa.me/573012373875?text={mensaje}"

        session["cart"] = {}
        session.modified = True

        return redirect(whatsapp_url)

    return render_template("pedido_carrito.html", productos=productos, total=round(total, 2))

# =======================================================
# 🤖 MACHINE LEARNING – REGRESIÓN
# =======================================================
try:
    with open(os.path.join("ml_models", "regression_model.pkl"), "rb") as f:
        modelo_regresion = pickle.load(f)
except Exception as e:
    print("⚠ Error cargando modelo regresión:", e)
    modelo_regresion = None

# =======================================================
# 🤖 MACHINE LEARNING – CNN
# =======================================================
cnn_model_path = os.path.join("ml_models", "cnn_model.h5")
class_indices_path = os.path.join("ml_models", "class_indices.json")

cnn_model = None
CNN_CLASSES = []

if os.path.exists(cnn_model_path):
    try:
        cnn_model = load_model(cnn_model_path)
        print("✅ CNN cargado:", cnn_model_path)
    except Exception as e:
        print("⚠ Error cargando CNN:", e)

if os.path.exists(class_indices_path):
    with open(class_indices_path, "r") as f:
        class_dict = json.load(f)
    CNN_CLASSES = sorted(class_dict, key=class_dict.get)

CNN_LABELS_HUMAN = {
    "camote buena": "Camote de calidad A (bueno)",
    "camote mala": "Camote de calidad C (defectuoso)",
    "yuca buena": "Yuca de calidad A (buena)",
    "yuca mala": "Yuca de calidad C (defectuosa)"
}

@app.route('/prediccion', methods=['GET', 'POST'])
def prediccion():
    if "logueado" not in session:
        flash("Acceso restringido. Inicie sesión.", "danger")
        return redirect(url_for('login'))

    resultado_regresion = None
    resultado_cnn = None

    if request.method == "POST":
        tipo = request.form.get("tipo")

        if tipo == "regresion" and modelo_regresion:
            try:
                t1 = float(request.form["tipo_camote"])
                h = float(request.form["humedad"])
                t2 = float(request.form["tamano_lote"])
                entrada = np.array([[t1, h, t2]])
                resultado_regresion = round(modelo_regresion.predict(entrada)[0], 2)
            except Exception as e:
                resultado_regresion = f"⚠ Error: {e}"

        elif tipo == "cnn" and cnn_model:
            img_data = request.form.get("imagen")
            if img_data:
                try:
                    img_data = img_data.split(",")[1]
                    img = Image.open(BytesIO(base64.b64decode(img_data))).convert("RGB")
                    img = img.resize((128, 128))
                    img_array = np.array(img) / 255.0
                    img_array = np.expand_dims(img_array, axis=0)

                    pred = cnn_model.predict(img_array)
                    idx = int(np.argmax(pred))

                    clase = CNN_CLASSES[idx]
                    resultado_cnn = CNN_LABELS_HUMAN[clase]

                except Exception as e:
                    resultado_cnn = f"⚠ Error procesando imagen: {e}"

    return render_template(
        "prediccion.html",
        resultado_regresion=resultado_regresion,
        resultado_cnn=resultado_cnn
    )

# =======================================================
# 💬 CHATBOT INTEGRADO AQUÍ
# =======================================================
def responder_chatbot(mensaje: str) -> str:
    msg = mensaje.lower()

    if any(p in msg for p in ["hola", "buenas", "buenos días", "buenas tardes"]):
        return "¡Hola! 👋 ¿En qué puedo ayudarte hoy? Productos, precios, calidad o pedidos."

    if any(p in msg for p in ["catálogo", "catalogo", "producto", "productos"]):
        return "Tenemos puré de yuca y de camote en varias presentaciones. Puedes verlos en la sección Catálogo."

    if any(p in msg for p in ["precio", "vale", "cuánto"]):
        return "Los precios están actualizados en el catálogo. 😊"

    if any(p in msg for p in ["pedido", "comprar", "compra", "encargar"]):
        return "Para hacer un pedido, agrega productos al carrito y confirma desde la página de pedido."

    if any(p in msg for p in ["calidad", "dañado", "malo", "camote", "yuca"]):
        return "El sistema de control de calidad usa una CNN para analizar la calidad del camote/yuca desde la cámara."

    if any(p in msg for p in ["whatsapp", "contacto", "teléfono", "telefono"]):
        return "Nuestro WhatsApp es 📱 573012373875."

    if "ayuda" in msg:
        return "Puedo ayudarte con catálogo, pedidos, precios o control de calidad. ¿Qué deseas saber?"

    return "Interesante 🤔. ¿Quieres saber sobre productos, precios, pedidos o control de calidad?"

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({"respuesta": "No me llegó ningún mensaje 😅. Escribe algo y te ayudo."})

    respuesta = responder_chatbot(mensaje)
    return jsonify({"respuesta": respuesta})

# =======================================================
# 🚀 EJECUCIÓN LOCAL
# =======================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
