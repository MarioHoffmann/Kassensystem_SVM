"""API Blueprint: Dashboard Offene Beträge"""
from flask import Blueprint, request, jsonify
from src.models.dashboard import (
    gaeste_mit_offenen_betraegen,
    offene_bestellungen_der_person,
    gesamt_offen_fuer_person,
    person_als_bezahlt_markieren
)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.get("/")
def get_dashboard():
    return jsonify(gaeste_mit_offenen_betraegen())

@dashboard_bp.get("/<int:person_id>")
def get_person_detail(person_id):
    bestellungen = offene_bestellungen_der_person(person_id)
    gesamt = gesamt_offen_fuer_person(person_id)
    return jsonify({"bestellungen": bestellungen, "gesamt": gesamt})

@dashboard_bp.post("/<int:person_id>/bezahlen")
def bezahlen(person_id):
    data = request.get_json() or {}
    gezahlt = data.get("gezahlt")
    trinkgeld = bool(data.get("trinkgeld", False))
    if gezahlt is not None:
        try:
            gezahlt = float(str(gezahlt).replace(",", "."))
        except ValueError:
            return jsonify({"error": "Ungültiger Betrag"}), 400
    else:
        gezahlt = None
        
    rueckgeld = person_als_bezahlt_markieren(person_id, gezahlt, trinkgeld)
    return jsonify({"ok": True, "rueckgeld": rueckgeld})
