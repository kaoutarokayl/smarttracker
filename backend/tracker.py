import sqlite3
import time
from datetime import datetime
import pygetwindow as gw
import json  # ✅ Pour lire le fichier config

# ✅ Lire le user_id depuis un fichier JSON
try:
    with open("config_tracker.json") as f:
        config = json.load(f)
        user_id = config.get("user_id", 1)  # 1 par défaut si absent
except Exception as e:
    print("⚠️ Erreur lecture config_tracker.json :", e)
    user_id = 1

# Connexion à la base de données SQLite
conn = sqlite3.connect("usage_data.db")
cursor = conn.cursor()

# Création de la table "usage" si elle n'existe pas déjà
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_name TEXT,
        start_time TEXT,
        duration INTEGER,
        user_id INTEGER
    )
''')
conn.commit()

def get_active_window_name():
    try:
        window = gw.getActiveWindow()
        if window:
            return window.title
    except:
        pass
    return "Unknown"

def format_duration(seconds):
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"
    elif seconds >= 60:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        return f"{seconds}s"

last_app = None
start_time = time.time()

print(f"Suivi démarré pour l'utilisateur {user_id}... (CTRL+C pour arrêter)")

try:
    while True:
        current_app = get_active_window_name()
        if current_app != last_app:
            end_time = time.time()
            if last_app is not None:
                duration = int(end_time - start_time)
                timestamp = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute('''
                    INSERT INTO usage (app_name, start_time, duration, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (last_app, timestamp, duration, user_id))
                conn.commit()

                print(f"[{timestamp}] {last_app} utilisé pendant {format_duration(duration)}")

            last_app = current_app
            start_time = time.time()

        time.sleep(1)

except KeyboardInterrupt:
    print("\nArrêt du suivi.")
    conn.close()
