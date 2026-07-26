"""API Blueprint: Bestellungen & Positionen"""
from flask import Blueprint, request, jsonify
from src.models.bestellung import (
    get_oder_erstelle_bestellung, offene_bestellung_fuer_person,
    positionen_der_bestellung, produkt_hinzufuegen,
    position_entfernen, menge_aendern,
    gesamtpreis_berechnen, bestellung_abschliessen,
    GratisProduktSperreError
)

bestellungen_bp = Blueprint("bestellungen", __name__)

@bestellungen_bp.get("/aktiv/<int:person_id>")
def get_aktive_bestellung(person_id):
    """Gibt die aktive (offene) Bestellung einer Person zurück."""
    bid = get_oder_erstelle_bestellung(person_id)
    positionen = positionen_der_bestellung(bid)
    gesamt = gesamtpreis_berechnen(bid)
    return jsonify({"id": bid, "positionen": positionen, "gesamt": gesamt})

@bestellungen_bp.post("/<int:bid>/produkt")
def add_produkt(bid):
    data = request.get_json()
    try:
        produkt_hinzufuegen(bid, data["produkt_id"], data["einzelpreis"])
        positionen = positionen_der_bestellung(bid)
        gesamt = gesamtpreis_berechnen(bid)
        return jsonify({"positionen": positionen, "gesamt": gesamt})
    except GratisProduktSperreError as e:
        return jsonify({"error": str(e)}), 400

@bestellungen_bp.delete("/positionen/<int:pos_id>")
def remove_position(pos_id):
    position_entfernen(pos_id)
    return jsonify({"ok": True})

@bestellungen_bp.patch("/positionen/<int:pos_id>")
def patch_menge(pos_id):
    data = request.get_json()
    try:
        menge_aendern(pos_id, data.get("delta", 0))
        return jsonify({"ok": True})
    except GratisProduktSperreError as e:
        return jsonify({"error": str(e)}), 400

@bestellungen_bp.post("/<int:bid>/abschliessen")
def abschliessen(bid):
    positionen = positionen_der_bestellung(bid)
    if not positionen:
        return jsonify({"error": "Bestellung ist leer."}), 400
    gesamt = gesamtpreis_berechnen(bid)
    bestellung_abschliessen(bid)
    return jsonify({"ok": True, "gesamt": gesamt})
