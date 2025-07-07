from flask import Flask, render_template, url_for, redirect, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import random
import os
from keras.layers import TFSMLayer
from keras.models import Sequential
from PIL import Image, ImageOps
import numpy as np
import traceback

# Configuración de la app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecreto123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicialización
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'iniciar_sesion'

# Modelo Keras
model_path = "app/keras_model"
model = Sequential([
    TFSMLayer(model_path, call_endpoint="serving_default")
])

# Clases del modelo
class_names = [
    "anillas de plastico",
    "bolsas",
    "botellas",
    "tapones de botella",
    "colillas",
    "electronicos",
    "envases de comida",
    "frascos",
    "humano",
    "latas",
    "papel usado",
    "pilas"
]

objetivos = [
    "Recoge al menos -- bolsas plásticas del suelo y colócalas en el contenedor correspondiente.",
    "Separa y recicla -- botellas plásticas.",
    "Reúce -- latas de aluminio.",
    "Reutiliza -- frascos o envases de vidrio vacíos.",
    "Lleva -- pilas usadas a un punto de reciclaje especializado.",
    "Recicla -- hojas de papel usadas por ambas caras.",
    "Separa y desecha correctamente -- anillas de plastico (plastico de packs de latas).",
    "Limpia y recicla -- envases de comida plásticos.",
    "Recoge -- colillas de cigarro del suelo.",
    "Lleva -- objetos electrónicos pequeños al punto limpio (pilas, cables, cargadores).",
    "Recolecta al menos -- tapas plásticas."
]

# Modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_pic = db.Column(db.String(256), default="default.png")
    challenges = db.Column(db.JSON, nullable=False)
    progress = db.Column(db.JSON, nullable=False)
    trash_collected_kg = db.Column(db.Float, default=0.0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def incrementar_progreso(self, clase_detectada):
        for i, challenge in enumerate(self.challenges):
            if challenge['clase'] == clase_detectada:
                if self.progress[i] < challenge['cantidad']:
                    nuevo_progreso = self.progress.copy()
                    nuevo_progreso[i] += 1
                    self.progress = nuevo_progreso
                    self.trash_collected_kg += 0.005
                    return True
        return False

# Cargar usuario para login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Asignar desafíos aleatorios
def asignar_desafios():
    desafios = []
    for objetivo in random.sample(objetivos, 4):
        cantidad = random.randint(1, 6)
        desafios.append({
            "texto": objetivo.replace("--", str(cantidad)),
            "clase": class_names[objetivos.index(objetivo)],
            "cantidad": cantidad
        })
    return desafios

# Reinicia desafíos diarios
def resetear_desafios_diarios():
    with app.app_context():
        usuarios = User.query.all()
        for user in usuarios:
            user.challenges = asignar_desafios()
            user.progress = [0, 0, 0, 0]
        db.session.commit()
        print("✔️ Desafíos diarios reiniciados para todos los usuarios.")

# Scheduler diario
scheduler = BackgroundScheduler()
scheduler.add_job(resetear_desafios_diarios, 'cron', hour=0, minute=0)
scheduler.start()

# Rutas
@app.route('/')
def index():
    return redirect(url_for('iniciar_sesion'))

@app.route('/home')
@login_required
def home():
    print("Usuario autenticado:", current_user.is_authenticated)
    return render_template('home.html', usuario=current_user)

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        profile_pic = request.files.get('profile_pic')

        if User.query.filter_by(username=username).first():
            flash('❌ Usuario ya existe', 'error')
            return redirect(url_for('registrarse'))

        filename = "default.png"
        if profile_pic:
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_user = User(
            username=username,
            profile_pic=filename,
            challenges=asignar_desafios(),
            progress=[0, 0, 0, 0]
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('✅ Usuario creado con éxito. Inicia sesión.', 'success')
        return redirect(url_for('iniciar_sesion'))

    return render_template('registrarse.html')

@app.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            print("✅ Sesión iniciada correctamente para:", user.username)
            return redirect(url_for('home'))
        else:
            print("❌ Fallo de login: usuario o contraseña incorrectos")
            flash('❌ Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('iniciar_sesion'))

    return render_template('iniciar_sesion.html')

@app.route('/login', methods=['GET', 'POST'])
def login_alias():
    return redirect(url_for('iniciar_sesion'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('iniciar_sesion'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se envió ningún archivo."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Ningún archivo seleccionado."}), 400

        image = Image.open(file).convert("RGB")
        image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
        image_array = np.asarray(image)
        normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
        data = np.expand_dims(normalized_image_array, axis=0)

        prediction = model.predict(data)
        if isinstance(prediction, dict):
            prediction_array = list(prediction.values())[0]
        else:
            prediction_array = prediction

        index = np.argmax(prediction_array)
        class_name = class_names[index]
        confidence_score = float(prediction_array[0][index]) * 100

        if current_user.incrementar_progreso(class_name):
            db.session.commit()

        return jsonify({
            "clase": class_name,
            "confianza": round(confidence_score, 2)
        })

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        return jsonify({"error": "Error al procesar la imagen."}), 500

# Crear DB al inicio si no existe
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
