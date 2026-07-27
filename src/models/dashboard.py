"""
Kassensystem – Datenmodell: Dashboard offene Beträge (SQLite)
"""

from database import get_connection, get_vienna_now


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


def person_als_bezahlt_markieren(person_id: int, gezahlt_betrag: float = None, trinkgeld_buchen: bool = False) -> float:
    """Markiert alle offenen Bestellungen einer Person als bezahlt (bzw. teilbezahlt) und verbucht den Umsatz.
    Gibt das Rückgeld zurück, falls überzahlt wurde."""
    with get_connection() as conn:
        # 1. Gesamtsumme aller aktuell offenen Bestellungen dieser Person berechnen
        gesamt_offen = conn.execute(
            """SELECT COALESCE(SUM(bp.menge * bp.einzelpreis), 0)
               FROM bestellpositionen bp
               JOIN bestellungen b ON bp.bestellung_id = b.id
               WHERE b.person_id = ? AND b.abgeschlossen = 1 AND b.bezahlt = 0""",
            (person_id,)
        ).fetchone()[0]

        # Prüfen, ob überhaupt offene Bestellungen vorliegen
        offene_anzahl = conn.execute(
            """SELECT COUNT(*) FROM bestellungen
               WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 0""",
            (person_id,)
        ).fetchone()[0]

        if offene_anzahl <= 0:
            return 0.0

        # Wenn gezahlt_betrag nicht angegeben ist oder den offenen Betrag übersteigt
        if gezahlt_betrag is None or gezahlt_betrag < 0:
            gezahlt_betrag = gesamt_offen

        # Falls Trinkgeld verbucht werden soll und überzahlt wurde
        if trinkgeld_buchen and gezahlt_betrag > gesamt_offen:
            trinkgeld_wert = gezahlt_betrag - gesamt_offen
            letzte_b = conn.execute(
                """SELECT id FROM bestellungen
                   WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 0
                   ORDER BY id DESC LIMIT 1""",
                (person_id,)
            ).fetchone()
            if letzte_b:
                conn.execute(
                    """INSERT INTO bestellpositionen (bestellung_id, produkt_id, menge, einzelpreis)
                       VALUES (?, 9998, 1, ?)""",
                    (letzte_b["id"], trinkgeld_wert)
                )
                gesamt_offen = gezahlt_betrag

        rueckgeld = 0.0
        tatsaechlicher_umsatz = gezahlt_betrag

        if gezahlt_betrag >= gesamt_offen:
            # Alles bezahlt
            rueckgeld = gezahlt_betrag - gesamt_offen
            tatsaechlicher_umsatz = gesamt_offen
            
            # Alle offenen Bestellungen als bezahlt markieren
            conn.execute(
                """UPDATE bestellungen SET bezahlt = 1
                   WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 0""",
                (person_id,)
            )
        else:
            # Teilzahlung
            remaining_gezahlt = gezahlt_betrag
            
            # Offene Bestellungen chronologisch holen (älteste zuerst)
            offene_bestellungen = conn.execute(
                """SELECT id FROM bestellungen
                   WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 0
                   ORDER BY id ASC""",
                (person_id,)
            ).fetchall()
            
            for row in offene_bestellungen:
                bid = row["id"]
                # Summe dieser Bestellung berechnen
                bid_sum = conn.execute(
                    """SELECT COALESCE(SUM(menge * einzelpreis), 0)
                       FROM bestellpositionen WHERE bestellung_id = ?""",
                    (bid,)
                ).fetchone()[0]
                
                if bid_sum <= 0:
                    # Leere Bestellung als bezahlt markieren
                    conn.execute("UPDATE bestellungen SET bezahlt = 1 WHERE id = ?", (bid,))
                    continue
                
                if bid_sum <= remaining_gezahlt:
                    # Bestellung wird voll bezahlt
                    conn.execute("UPDATE bestellungen SET bezahlt = 1 WHERE id = ?", (bid,))
                    remaining_gezahlt -= bid_sum
                else:
                    # Bestellung wird nur teilbezahlt
                    if remaining_gezahlt > 0:
                        conn.execute(
                            """INSERT INTO bestellpositionen (bestellung_id, produkt_id, menge, einzelpreis)
                               VALUES (?, 9999, 1, ?)""",
                            (bid, -remaining_gezahlt)
                        )
                        remaining_gezahlt = 0.0
                    break

        # 2. In die Tages-Statistik übertragen
        if tatsaechlicher_umsatz > 0:
            heute = get_vienna_now().strftime("%Y-%m-%d")
            conn.execute(
                """INSERT INTO statistiken (datum, umsatz) VALUES (?, ?)
                   ON CONFLICT(datum) DO UPDATE SET umsatz = umsatz + excluded.umsatz""",
                (heute, tatsaechlicher_umsatz)
            )
            
        return rueckgeld


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
