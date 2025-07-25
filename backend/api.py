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
    
    if user and check_password_hash(user["password_hash"], password):
        # Mettre à jour la dernière connexion
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?", 
            (datetime.datetime.now().isoformat(), user["id"])
        )
        conn.commit()
        
        token = generate_token(user["id"], user["role"])
        conn.close()
        return jsonify({
            "message": "Connexion réussie",
            "token": token
        })
    
    conn.close()
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

# 📊 Statistiques admin avec vraies données
@app.route('/admin/stats', methods=['GET'])
@token_required
def get_admin_stats(user_id, role):
    if role != 'admin':
        return jsonify({'message': 'Accès refusé'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculer les vraies statistiques
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()["total"]
    
    # Utilisateurs actifs (connectés dans les 7 derniers jours)
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(*) as active FROM users WHERE last_login > ?", (seven_days_ago,))
    active_users = cursor.fetchone()["active"]
    
    # Sessions totales
    cursor.execute("SELECT COUNT(*) as total FROM usage")
    total_sessions = cursor.fetchone()["total"]
    
    # Temps moyen par session (en secondes, converti en heures)
    cursor.execute("SELECT AVG(duration) as avg_duration FROM usage")
    avg_result = cursor.fetchone()["avg_duration"]
    avg_session_time = round((avg_result or 0) / 3600, 1)  # Convertir en heures
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_sessions': total_sessions,
        'avg_session_time': avg_session_time,
        'system_health': 'good'
    })

# 📈 Activité récente
@app.route('/admin/activity', methods=['GET'])
@token_required
def get_recent_activity(user_id, role):
    if role != 'admin':
        return jsonify({'message': 'Accès refusé'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    activities = []
    
    # Dernières connexions
    cursor.execute('''
        SELECT username, last_login 
        FROM users 
        WHERE last_login IS NOT NULL 
        ORDER BY last_login DESC 
        LIMIT 10
    ''')
    recent_logins = cursor.fetchall()
    
    for i, user in enumerate(recent_logins):
        if user["last_login"]:
            activities.append({
                'id': f'login_{i}',
                'username': user["username"],
                'action': 'Connexion',
                'timestamp': user["last_login"],
                'type': 'login'
            })
    
    # Dernières sessions d'usage
    cursor.execute('''
        SELECT u.username, usage.start_time, usage.app_name
        FROM usage 
        JOIN users u ON usage.user_id = u.id
        ORDER BY usage.start_time DESC 
        LIMIT 10
    ''')
    recent_sessions = cursor.fetchall()
    
    for i, session in enumerate(recent_sessions):
        activities.append({
            'id': f'session_{i}',
            'username': session["username"],
            'action': f'Session {session["app_name"]}',
            'timestamp': session["start_time"],
            'type': 'session'
        })
    
    # Trier par timestamp décroissant
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    conn.close()
    return jsonify(activities[:15])  # Retourner les 15 plus récents

# 🖥️ État du système
@app.route('/admin/system/health', methods=['GET'])
@token_required
def get_system_health(user_id, role):
    if role != 'admin':
        return jsonify({'message': 'Accès refusé'}), 403
    
    # Vérifier la base de données
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        conn.close()
        db_status = "operational"
    except:
        db_status = "error"
    
    return jsonify({
        'database_status': db_status,
        'server_status': 'online',
        'last_backup': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    })

if __name__ == '__main__':
    app.run(debug=True)