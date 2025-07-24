import sqlite3
import time
from datetime import datetime
import psutil
import pygetwindow as gw

# Connexion à la base de données SQLite
conn = sqlite3.connect("usage_data.db")
cursor = conn.cursor()

# Création de la table si elle n'existe pas déjà
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_name TEXT,
        start_time TEXT,
        duration INTEGER
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

# Variables pour le suivi
last_app = None
start_time = time.time()

print("Suivi démarré... (CTRL+C pour arrêter)")

try:
    while True:
        current_app = get_active_window_name()
        if current_app != last_app:
            end_time = time.time()
            if last_app is not None:
                duration = int(end_time - start_time)
                timestamp = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
                
                # Enregistrement dans la base de données
                cursor.execute('''
                    INSERT INTO usage (app_name, start_time, duration)
                    VALUES (?, ?, ?)
                ''', (last_app, timestamp, duration))
                conn.commit()

                print(f"[{timestamp}] {last_app} utilisé pendant {format_duration(duration)}")

            # Mise à jour pour la nouvelle application
            last_app = current_app
            start_time = time.time()

        time.sleep(1)

except KeyboardInterrupt:
    print("\nArrêt du suivi.")
    conn.close()
