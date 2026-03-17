"""
Kassensystem – Flask Hauptserver
Start: python server.py
Zugriff: http://<Server-IP>:5000
"""

import os
import sys
import socket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from database import init_db
from backup import starte_backup_service

from src.api.personen import personen_bp
from src.api.produkte import produkte_bp
from src.api.bestellungen import bestellungen_bp
from src.api.dashboard import dashboard_bp
from src.api.statistik import statistik_bp

app = Flask(__name__, static_folder="static", static_url_path="")

# Blueprints registrieren
app.register_blueprint(personen_bp,    url_prefix="/api/personen")
app.register_blueprint(produkte_bp,    url_prefix="/api/produkte")
app.register_blueprint(bestellungen_bp, url_prefix="/api/bestellungen")
app.register_blueprint(dashboard_bp,   url_prefix="/api/dashboard")
app.register_blueprint(statistik_bp,   url_prefix="/api/statistik")


from flask import Flask, send_from_directory, request, jsonify
from config import APP_PIN

@app.post("/api/app/auth")
def app_auth():
    data = request.get_json()
    if data.get("pin") == APP_PIN:
        return jsonify({"ok": True})
    return jsonify({"error": "Falscher PIN"}), 401


@app.route("/")
@app.route("/<path:path>")
def index(path=""):
    """Alle nicht-API Routen → index.html (SPA)"""
    return send_from_directory("static", "index.html")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "?.?.?.?"


if __name__ == "__main__":
    init_db()
    starte_backup_service()

    local_ip = get_local_ip()
    print("\n" + "="*55)
    print("  🍽️  SVM Kantine – Kassensystem")
    print("="*55)
    print(f"  💻  Dieser PC:  http://localhost:5000")
    print(f"  📱  Tablets:    http://{local_ip}:5000")
    print(f"  💾  Backups:    stündlich → OneDrive")
    print("="*55 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

