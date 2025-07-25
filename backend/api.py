from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# 🧩 Clé secrète pour signer les tokens JWT
app.config['SECRET_KEY'] = '1e1c9bc44ba69983f48ae547464a6d8b3fdbdb0736d59ad06d8b39c0c14df1b3'

DATABASE = "usage_data.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 🧩 Génération du token JWT
def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

# 🧩 Décorateur pour sécuriser les routes avec token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token requis'}), 401
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return f(user_id=data['user_id'], role=data['role'], *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Champs manquants"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, generate_password_hash(password), "user"))
        conn.commit()
        return jsonify({"message": "Inscription réussie"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Nom d'utilisateur ou email déjà utilisé"}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        token = generate_token(user["id"], user["role"])
        return jsonify({
            "message": "Connexion réussie",
            "token": token
        })
    return jsonify({"error": "Identifiants invalides"}), 401

@app.route('/usage/<int:user_id>', methods=['GET'])
def get_usage(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT app_name, start_time, duration
        FROM usage
        WHERE user_id = ?
        ORDER BY start_time DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    usage_data = [
        {
            "app_name": row["app_name"],
            "start_time": row["start_time"],
            "duration": row["duration"]
        }
        for row in rows
    ]
    return jsonify(usage_data)

# 🔐 Route protégée par token JWT
@app.route('/admin/users', methods=['GET'])
@token_required
def get_all_users(user_id, role):
    if role != 'admin':
        return jsonify({'message': 'Accès refusé'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role FROM users')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'users': users})

if __name__ == '__main__':
    app.run(debug=True)
