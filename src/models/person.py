"""
Kassensystem – Datenmodell Person (SQLite)
"""

import sqlite3
from database import get_connection


class PersonError(Exception):
    pass


def alle_personen() -> list[dict]:
    """Gibt alle Personen alphabetisch sortiert zurück."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, vorname, nachname FROM personen ORDER BY nachname, vorname"
        ).fetchall()
    return [dict(r) for r in rows]


def person_anlegen(vorname: str, nachname: str) -> int:
    vorname  = vorname.strip()
    nachname = nachname.strip()
    if not vorname:
        raise PersonError("Vorname darf nicht leer sein.")
    if not nachname:
        raise PersonError("Nachname darf nicht leer sein.")
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO personen (vorname, nachname) VALUES (?, ?)",
                (vorname, nachname)
            )
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise PersonError(f"Person '{vorname} {nachname}' ist bereits vorhanden.")


def person_loeschen(person_id: int):
    with get_connection() as conn:
        # 1. Alle Bestellungen dieser Person finden
        bestellungen = conn.execute(
            "SELECT id, date(erstellt_am) as tag FROM bestellungen WHERE person_id = ?",
            (person_id,)
        ).fetchall()
        
        for b in bestellungen:
            # Summe dieser Bestellung berechnen
            summe = conn.execute(
                "SELECT SUM(menge * einzelpreis) FROM bestellpositionen WHERE bestellung_id = ?",
                (b["id"],)
            ).fetchone()[0] or 0
            
            # Von Tages-Statistik abziehen
            conn.execute(
                "UPDATE statistiken SET umsatz = MAX(0, umsatz - ?) WHERE datum = ?",
                (summe, b["tag"])
            )
            
            # Bestellung löschen (Positionen per CASCADE)
            conn.execute("DELETE FROM bestellungen WHERE id = ?", (b["id"],))

        # 2. Person endgültig löschen
        conn.execute("DELETE FROM personen WHERE id = ?", (person_id,))



def person_suchen(text: str) -> list[dict]:
    q = f"%{text.strip()}%"
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, vorname, nachname FROM personen
               WHERE vorname LIKE ? OR nachname LIKE ?
               ORDER BY nachname, vorname""",
            (q, q)
        ).fetchall()
    return [dict(r) for r in rows]
