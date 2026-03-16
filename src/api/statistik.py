"""API Blueprint: Statistiken"""
from flask import Blueprint, request, jsonify
from src.models.statistik import (
    tagesumsaetze, wochen_umsatz, monats_umsatz,
    top_produkte, zusammenfassung_heute,
    zusammenfassung_woche, zusammenfassung_monat,
    kaeufe_pro_person, kaufhistorie_loeschen,
    bestellung_loeschen
)
from config import STATISTIK_PASSWORT

statistik_bp = Blueprint("statistik", __name__)

@statistik_bp.post("/auth")
def auth():
    from flask import request
    data = request.get_json()
    if data.get("passwort") == STATISTIK_PASSWORT:
        return jsonify({"ok": True})
    return jsonify({"error": "Falsches Passwort"}), 401

@statistik_bp.get("/")
def get_statistik():
    modus = request.args.get("modus", "tag")
    if modus == "woche":
        daten = wochen_umsatz()
        labels = [d["woche"] for d in daten]
    elif modus == "monat":
        daten = monats_umsatz()
        labels = [d["monat"] for d in daten]
    else:
        daten = tagesumsaetze(30)
        labels = [d["datum"] for d in daten]

    werte = [d["umsatz"] for d in daten]
    return jsonify({
        "labels": labels,
        "werte": werte,
        "heute": zusammenfassung_heute(),
        "woche": zusammenfassung_woche(),
        "monat": zusammenfassung_monat(),
        "top": top_produkte(10),
    })

@statistik_bp.get("/person/<int:person_id>")
def get_person_statistik(person_id):
    """Gibt die vollständige Kaufhistorie einer Person zurück."""
    import traceback
    try:
        daten = kaeufe_pro_person(person_id)
        return jsonify(daten)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@statistik_bp.delete("/person/<int:person_id>/historie")
def delete_person_historie(person_id):
    """Löscht die gesamte Kaufhistorie einer Person."""
    try:
        kaufhistorie_loeschen(person_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistik_bp.delete("/bestellung/<int:bestellung_id>")
def delete_bestellung(bestellung_id):
    """Löscht eine einzelne Bestellung."""
    try:
        bestellung_loeschen(bestellung_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
