"""
Kassensystem – Datenmodell: Dashboard offene Beträge (SQLite)
"""

from database import get_connection


def gaeste_mit_offenen_betraegen() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.id, p.vorname, p.nachname,
                      COUNT(DISTINCT b.id) AS anzahl_bestellungen,
                      COALESCE(SUM(bp.menge * bp.einzelpreis), 0) AS offener_betrag
               FROM personen p
               JOIN bestellungen b ON b.person_id = p.id
               LEFT JOIN bestellpositionen bp ON bp.bestellung_id = b.id
               WHERE b.abgeschlossen = 1 AND b.bezahlt = 0
               GROUP BY p.id
               ORDER BY p.nachname, p.vorname"""
        ).fetchall()
    return [dict(r) for r in rows]


def offene_bestellungen_der_person(person_id: int) -> list[dict]:
    with get_connection() as conn:
        bestellungen = conn.execute(
            """SELECT id, erstellt_am FROM bestellungen
               WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 0
               ORDER BY id""",
            (person_id,)
        ).fetchall()
        result = []
        for b in bestellungen:
            positionen = conn.execute(
                """SELECT bp.menge, bp.einzelpreis,
                          p.name AS produkt_name,
                          bp.menge * bp.einzelpreis AS gesamtpreis
                   FROM bestellpositionen bp
                   JOIN produkte p ON bp.produkt_id = p.id
                   WHERE bp.bestellung_id = ?
                   ORDER BY p.name""",
                (b["id"],)
            ).fetchall()
            result.append({
                "id": b["id"],
                "erstellt_am": b["erstellt_am"],
                "positionen": [dict(p) for p in positionen],
                "summe": sum(p["gesamtpreis"] for p in positionen),
            })
    return result


def person_als_bezahlt_markieren(person_id: int):
    """Markiert alle offenen Bestellungen einer Person als bezahlt und verbucht den Umsatz."""
    with get_connection() as conn:
        # 1. Gesamtsumme aller aktuell offenen Bestellungen dieser Person berechnen
        gesamt = conn.execute(
            """SELECT COALESCE(SUM(bp.menge * bp.einzelpreis), 0)
               FROM bestellpositionen bp
               JOIN bestellungen b ON bp.bestellung_id = b.id
               WHERE b.person_id = ? AND b.abgeschlossen = 1 AND b.bezahlt = 0""",
            (person_id,)
        ).fetchone()[0]

        # 2. In die Tages-Statistik übertragen
        if gesamt > 0:
            conn.execute(
                """INSERT INTO statistiken (datum, umsatz) VALUES (date('now','localtime'), ?)
                   ON CONFLICT(datum) DO UPDATE SET umsatz = umsatz + excluded.umsatz""",
                (gesamt,)
            )

        # 3. Alle offenen Bestellungen der Person als bezahlt markieren
        conn.execute(
            """UPDATE bestellungen SET bezahlt = 1
               WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 0""",
            (person_id,)
        )


def gesamt_offen_fuer_person(person_id: int) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(bp.menge * bp.einzelpreis), 0) AS gesamt
               FROM bestellpositionen bp
               JOIN bestellungen b ON bp.bestellung_id = b.id
               WHERE b.person_id = ? AND b.abgeschlossen = 1 AND b.bezahlt = 0""",
            (person_id,)
        ).fetchone()
    return row["gesamt"] if row else 0.0
