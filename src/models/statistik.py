"""
Kassensystem – Datenmodell Statistiken (SQLite)
"""

from database import get_connection, get_vienna_now


def tagesumsaetze(tage: int = 30) -> list[dict]:
    heute = get_vienna_now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT datum, umsatz FROM statistiken
               WHERE datum >= date(?, ? || ' days')
               ORDER BY datum""",
            (heute, f"-{tage}")
        ).fetchall()
    return [dict(r) for r in rows]


def wochen_umsatz() -> list[dict]:
    heute = get_vienna_now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-KW%W', datum) AS woche,
                      SUM(umsatz) AS umsatz
               FROM statistiken
               WHERE datum >= date(?, '-84 days')
               GROUP BY woche
               ORDER BY woche""",
            (heute,)
        ).fetchall()
    return [dict(r) for r in rows]


def monats_umsatz() -> list[dict]:
    heute = get_vienna_now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', datum) AS monat,
                      SUM(umsatz) AS umsatz
               FROM statistiken
               WHERE datum >= date(?, '-365 days')
               GROUP BY monat
               ORDER BY monat""",
            (heute,)
        ).fetchall()
    return [dict(r) for r in rows]


def top_produkte(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.name, SUM(bp.menge) AS menge, SUM(bp.menge * bp.einzelpreis) AS umsatz
               FROM bestellpositionen bp
               JOIN produkte p ON bp.produkt_id = p.id
               JOIN bestellungen b ON bp.bestellung_id = b.id
               WHERE b.abgeschlossen = 1
               GROUP BY p.id
               ORDER BY menge DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def zusammenfassung_heute() -> dict:
    heute = get_vienna_now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        stat = conn.execute(
            "SELECT umsatz FROM statistiken WHERE datum = ?", (heute,)
        ).fetchone()
        bestellungen = conn.execute(
            """SELECT COUNT(*) AS anzahl FROM bestellungen
               WHERE abgeschlossen = 1
               AND date(erstellt_am) = ?""",
            (heute,)
        ).fetchone()
        trinkgeld = conn.execute(
            """SELECT COALESCE(SUM(bp.menge * bp.einzelpreis), 0) AS gesamt
               FROM bestellpositionen bp
               JOIN bestellungen b ON bp.bestellung_id = b.id
               WHERE b.abgeschlossen = 1
                 AND bp.produkt_id = 9998
                 AND date(b.erstellt_am) = ?""",
            (heute,)
        ).fetchone()
    return {
        "umsatz_heute": stat["umsatz"] if stat else 0.0,
        "bestellungen_heute": bestellungen["anzahl"] if bestellungen else 0,
        "trinkgeld_heute": trinkgeld["gesamt"] if trinkgeld else 0.0,
    }


def zusammenfassung_woche() -> dict:
    heute = get_vienna_now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        stat = conn.execute(
            """SELECT COALESCE(SUM(umsatz), 0) AS umsatz FROM statistiken
               WHERE datum >= date(?,'weekday 1','-7 days')""",
            (heute,)
        ).fetchone()
    return {"umsatz_woche": stat["umsatz"] if stat else 0.0}


def zusammenfassung_monat() -> dict:
    monat = get_vienna_now().strftime("%Y-%m")
    with get_connection() as conn:
        stat = conn.execute(
            """SELECT COALESCE(SUM(umsatz), 0) AS umsatz FROM statistiken
               WHERE strftime('%Y-%m', datum) = ?""",
            (monat,)
        ).fetchone()
    return {"umsatz_monat": stat["umsatz"] if stat else 0.0}




def kaeufe_pro_person(person_id: int) -> list[dict]:
    """Gibt alle bezahlten Bestellungen einer Person zurück,
    gruppiert nach Bestellung mit allen Positionen."""
    with get_connection() as conn:
        # Alle abgeschlossenen Bestellungen der Person
        bestellungen = conn.execute(
            """SELECT id, erstellt_am
               FROM bestellungen
               WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 1
               ORDER BY erstellt_am DESC""",
            (person_id,)
        ).fetchall()

        result = []
        for b in bestellungen:
            positionen = conn.execute(
                """SELECT p.name AS produkt, bp.menge, bp.einzelpreis,
                          ROUND(bp.menge * bp.einzelpreis, 2) AS summe
                   FROM bestellpositionen bp
                   JOIN produkte p ON bp.produkt_id = p.id
                   WHERE bp.bestellung_id = ?
                   ORDER BY p.name""",
                (b["id"],)
            ).fetchall()

            gesamt = sum(pos["summe"] for pos in positionen)
            result.append({
                "id": b["id"],
                "datum": b["erstellt_am"],
                "gesamt": round(gesamt, 2),
                "positionen": [dict(p) for p in positionen],
            })
    return result


def kaufhistorie_loeschen(person_id: int):
    """Löscht alle bezahlten Bestellungen einer Person und passt die Statistik an."""
    with get_connection() as conn:
        # Alle Bestellungen finden, die gelöscht werden sollen
        bestellungen = conn.execute(
            """SELECT id, date(erstellt_am) as tag FROM bestellungen 
               WHERE person_id = ? AND abgeschlossen = 1 AND bezahlt = 1""",
            (person_id,)
        ).fetchall()
        
        for b in bestellungen:
            # Summe dieser einen Bestellung berechnen
            summe = conn.execute(
                "SELECT SUM(menge * einzelpreis) FROM bestellpositionen WHERE bestellung_id = ?",
                (b["id"],)
            ).fetchone()[0] or 0
            
            # Von Tages-Statistik abziehen (da bezahlt = 1, war es in der Statistik)
            conn.execute(
                "UPDATE statistiken SET umsatz = MAX(0, umsatz - ?) WHERE datum = ?",
                (summe, b["tag"])
            )
            
            # Bestellung löschen (Positionen per CASCADE)
            conn.execute("DELETE FROM bestellungen WHERE id = ?", (b["id"],))


def bestellung_loeschen(bestellung_id: int):
    """Löscht eine spezifische Bestellung und passt die Statistik an, falls bezahlt."""
    with get_connection() as conn:
        # Daten der Bestellung holen, bevor sie weg ist
        b_data = conn.execute(
            "SELECT bezahlt, date(erstellt_am) as tag FROM bestellungen WHERE id = ?",
            (bestellung_id,)
        ).fetchone()
        
        if b_data:
            if b_data["bezahlt"] == 1:
                summe = conn.execute(
                    "SELECT SUM(menge * einzelpreis) FROM bestellpositionen WHERE bestellung_id = ?",
                    (bestellung_id,)
                ).fetchone()[0] or 0
                
                # Von Tages-Statistik abziehen
                conn.execute(
                    "UPDATE statistiken SET umsatz = MAX(0, umsatz - ?) WHERE datum = ?",
                    (summe, b_data["tag"])
                )
            
            # Bestellung löschen
            conn.execute("DELETE FROM bestellungen WHERE id = ?", (bestellung_id,))
