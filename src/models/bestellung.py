"""
Kassensystem – Datenmodell Bestellungen & Bestellpositionen (SQLite)
"""

import sqlite3
from database import get_connection


def offene_bestellung_fuer_person(person_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id FROM bestellungen
               WHERE person_id = ? AND abgeschlossen = 0
               ORDER BY id DESC LIMIT 1""",
            (person_id,)
        ).fetchone()
    return dict(row) if row else None


def bestellung_erstellen(person_id: int) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO bestellungen (person_id) VALUES (?)", (person_id,)
        )
    return cur.lastrowid


def get_oder_erstelle_bestellung(person_id: int) -> int:
    offen = offene_bestellung_fuer_person(person_id)
    if offen:
        return offen["id"]
    return bestellung_erstellen(person_id)


def bestellung_abschliessen(bestellung_id: int):
    """Markiert eine Bestellung als abgeschlossen (bereit zum Bezahlen)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE bestellungen SET abgeschlossen = 1 WHERE id = ?",
            (bestellung_id,)
        )


# ─────────────────────────────────── Positionen ──────────────────────────────

def positionen_der_bestellung(bestellung_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT bp.id, bp.menge, bp.einzelpreis,
                      p.name AS produkt_name, p.id AS produkt_id,
                      bp.menge * bp.einzelpreis AS gesamtpreis
               FROM bestellpositionen bp
               JOIN produkte p ON bp.produkt_id = p.id
               WHERE bp.bestellung_id = ?
               ORDER BY bp.id""",
            (bestellung_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def produkt_hinzufuegen(bestellung_id: int, produkt_id: int, einzelpreis: float):
    with get_connection() as conn:
        existing = conn.execute(
            """SELECT id, menge FROM bestellpositionen
               WHERE bestellung_id = ? AND produkt_id = ?""",
            (bestellung_id, produkt_id)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE bestellpositionen SET menge = menge + 1 WHERE id = ?",
                (existing["id"],)
            )
        else:
            conn.execute(
                """INSERT INTO bestellpositionen
                   (bestellung_id, produkt_id, menge, einzelpreis)
                   VALUES (?, ?, 1, ?)""",
                (bestellung_id, produkt_id, einzelpreis)
            )


def position_entfernen(position_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM bestellpositionen WHERE id = ?", (position_id,))


def menge_aendern(position_id: int, delta: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT menge FROM bestellpositionen WHERE id = ?", (position_id,)
        ).fetchone()
        if not row:
            return
        neue_menge = row["menge"] + delta
        if neue_menge <= 0:
            conn.execute("DELETE FROM bestellpositionen WHERE id = ?", (position_id,))
        else:
            conn.execute(
                "UPDATE bestellpositionen SET menge = ? WHERE id = ?",
                (neue_menge, position_id)
            )


def gesamtpreis_berechnen(bestellung_id: int) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(menge * einzelpreis), 0) AS gesamt
               FROM bestellpositionen WHERE bestellung_id = ?""",
            (bestellung_id,)
        ).fetchone()
    return row["gesamt"] if row else 0.0
