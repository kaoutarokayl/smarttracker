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

# 3. Créer un compte admin s'il n'existe pas
cursor.execute("SELECT * FROM users WHERE role = 'admin'")
admin_exists = cursor.fetchone()

if not admin_exists:
    admin_password = generate_password_hash("admin123")  # Mot de passe temporaire
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ("admin", "admin@example.com", admin_password, "admin"))
    print("✅ Admin créé avec le mot de passe : admin123")

conn.commit()
conn.close()

print("Initialisation terminée.")
