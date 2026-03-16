"""API Blueprint: Kategorien & Produkte"""
from flask import Blueprint, request, jsonify
from src.models.produkt import (
    alle_kategorien, kategorie_anlegen, kategorie_loeschen,
    produkte_der_kategorie, alle_produkte,
    produkt_anlegen, produkt_bearbeiten, produkt_loeschen,
    KategorieError, ProduktError
)

produkte_bp = Blueprint("produkte", __name__)

# ── Kategorien ────────────────────────────────────────────────────────────────

@produkte_bp.get("/kategorien")
def get_kategorien():
    return jsonify(alle_kategorien())

@produkte_bp.post("/kategorien")
def post_kategorie():
    data = request.get_json()
    try:
        kid = kategorie_anlegen(data.get("name", ""))
        return jsonify({"id": kid}), 201
    except KategorieError as e:
        return jsonify({"error": str(e)}), 400

@produkte_bp.put("/kategorien/<int:kid>")
def put_kategorie(kid):
    data = request.get_json()
    try:
        kategorie_bearbeiten(kid, data.get("name", ""))
        return jsonify({"ok": True})
    except KategorieError as e:
        return jsonify({"error": str(e)}), 400

@produkte_bp.delete("/kategorien/<int:kid>")
def delete_kategorie(kid):
    try:
        kategorie_loeschen(kid)
        return jsonify({"ok": True})
    except KategorieError as e:
        return jsonify({"error": str(e)}), 400

# ── Produkte ──────────────────────────────────────────────────────────────────

@produkte_bp.get("/")
def get_produkte():
    kid = request.args.get("kategorie_id", type=int)
    if kid:
        return jsonify(produkte_der_kategorie(kid))
    return jsonify(alle_produkte())

@produkte_bp.post("/")
def post_produkt():
    data = request.get_json()
    try:
        preis = float(str(data.get("preis", 0)).replace(",", "."))
        pid = produkt_anlegen(data.get("name", ""), preis, data.get("kategorie_id"))
        return jsonify({"id": pid}), 201
    except (ProduktError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

@produkte_bp.put("/<int:pid>")
def put_produkt(pid):
    data = request.get_json()
    try:
        preis = float(str(data.get("preis", 0)).replace(",", "."))
        produkt_bearbeiten(pid, data.get("name", ""), preis, data.get("kategorie_id"))
        return jsonify({"ok": True})
    except (ProduktError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

@produkte_bp.delete("/<int:pid>")
def delete_produkt(pid):
    produkt_loeschen(pid)
    return jsonify({"ok": True})
