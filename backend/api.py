from flask import Flask, jsonify, request
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_FILE = "usage_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Route : applications les plus utilisées
@app.route('/most_used')
def most_used():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT app_name, SUM(duration) as total_duration
        FROM usage
        GROUP BY app_name
        ORDER BY total_duration DESC
        LIMIT 10
    ''')
    results = cursor.fetchall()
    conn.close()

    apps = [
        {"app_name": row["app_name"], "total_duration": row["total_duration"]}
        for row in results
    ]
    return jsonify(apps)

# 2. Route : Si tu veux aussi juste afficher toutes les sessions brutes :
@app.route('/all_usage')
def all_usage():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT app_name, start_time, duration
        FROM usage
        ORDER BY start_time DESC
    ''')
    results = cursor.fetchall()
    conn.close()

    all_data = [
        {
            "app_name": row["app_name"],
            "start_time": row["start_time"],
            "duration": row["duration"]
        }
        for row in results
    ]
    return jsonify(all_data)


# 2. Route : résumé quotidien
@app.route('/daily_summary')
def daily_summary():
    date_param = request.args.get("date")  # format attendu: "2025-07-23"
    if not date_param:
        return jsonify({"error": "Paramètre ?date=YYYY-MM-DD manquant"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT app_name, SUM(duration) as total_duration
        FROM usage
        WHERE DATE(start_time) = ?
        GROUP BY app_name
        ORDER BY total_duration DESC
    ''', (date_param,))
    results = cursor.fetchall()
    conn.close()

    summary = [
        {"app_name": row["app_name"], "total_duration": row["total_duration"]}
        for row in results
    ]
    return jsonify(summary)

if __name__ == '__main__':
    app.run(debug=True)
