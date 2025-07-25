import sqlite3
from werkzeug.security import generate_password_hash

# Connexion à la base de données
conn = sqlite3.connect("usage_data.db")
cursor = conn.cursor()

# 1. Créer la table users si elle n'existe pas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
''')

# 2. Ajouter la colonne user_id à usage si elle n'existe pas déjà
try:
    cursor.execute('ALTER TABLE usage ADD COLUMN user_id INTEGER')
except sqlite3.OperationalError:
    # La colonne existe déjà, on ignore l'erreur
    pass

# 3. Ajouter la colonne last_login à users si elle n'existe pas déjà
try:
    cursor.execute('ALTER TABLE users ADD COLUMN last_login TEXT')
    print("✅ Colonne last_login ajoutée à la table users")
except sqlite3.OperationalError:
    # La colonne existe déjà, on ignore l'erreur
    print("ℹ️ Colonne last_login existe déjà")

# 4. Créer un compte admin s'il n'existe pas
cursor.execute("SELECT * FROM users WHERE role = 'admin'")
admin_exists = cursor.fetchone()

if not admin_exists:
    admin_password = generate_password_hash("admin123")  # Mot de passe temporaire
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ("admin", "admin@example.com", admin_password, "admin"))
    print("✅ Admin créé avec le mot de passe : admin123")
else:
    print("ℹ️ Compte admin existe déjà")

# 5. Créer la table usage si elle n'existe pas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        app_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        duration INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

conn.commit()
conn.close()
print("✅ Initialisation terminée.")