from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
CORS(app)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "workshop_db"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "message": "Flask API is running"})

@app.get("/api/items")
def get_items():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, description, created_at FROM items ORDER BY id DESC")
        rows = cursor.fetchall()
        return jsonify(rows)
    finally:
        cursor.close()
        conn.close()

@app.get("/api/items/<int:item_id>")
def get_item(item_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, description, created_at FROM items WHERE id = %s", (item_id,))
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(row)
    finally:
        cursor.close()
        conn.close()

@app.post("/api/items")
def create_item():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO items (name, description) VALUES (%s, %s)",
            (name, description)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return jsonify({"message": "Item created", "id": new_id}), 201
    finally:
        cursor.close()
        conn.close()

@app.put("/api/items/<int:item_id>")
def update_item(item_id):
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE items SET name = %s, description = %s WHERE id = %s",
            (name, description, item_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Item not found"}), 404
        return jsonify({"message": "Item updated"})
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/items/<int:item_id>")
def delete_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Item not found"}), 404
        return jsonify({"message": "Item deleted"})
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)