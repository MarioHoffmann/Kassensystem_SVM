"""API Blueprint: Personen"""
from flask import Blueprint, request, jsonify
from src.models.person import alle_personen, person_anlegen, person_loeschen, PersonError

personen_bp = Blueprint("personen", __name__)

@personen_bp.get("/")
def get_personen():
    return jsonify(alle_personen())

@personen_bp.post("/")
def post_person():
    data = request.get_json()
    try:
        pid = person_anlegen(data.get("vorname",""), data.get("nachname",""))
        return jsonify({"id": pid}), 201
    except PersonError as e:
        return jsonify({"error": str(e)}), 400

@personen_bp.delete("/<int:person_id>")
def delete_person(person_id):
    person_loeschen(person_id)
    return jsonify({"ok": True})
