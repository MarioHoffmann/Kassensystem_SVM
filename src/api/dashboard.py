"""API Blueprint: Dashboard Offene Beträge"""
from flask import Blueprint, jsonify
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
    person_als_bezahlt_markieren(person_id)
    return jsonify({"ok": True})
