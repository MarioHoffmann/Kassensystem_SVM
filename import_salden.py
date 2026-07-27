"""
Hilfsskript zum Importieren von Altsalden aus den Screenshots.
Führe dieses Skript auf PythonAnywhere mit 'python import_salden.py' aus.
"""

import sys
import os
from datetime import datetime

# Falls das Skript außerhalb des Projektordners gestartet wird, Pfad anpassen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection, get_vienna_now, init_db

# (Vorname, Nachname, Offener Betrag)
SALDEN = [
    ("Alkorin", "2026", 341.00),
    ("Johannes", "Bocha", 61.00),
    ("Felix", "Daum", 36.00),
    ("Christoph", "Deutinger", 49.00),
    ("Paz", "Eßl", 74.00),
    ("Nico", "Glanzer", 131.00),
    ("Alex", "Gschwandtner", 3.00),
    ("Erti", "Günday", 20.00),
    ("Daniel", "Hauer", 133.00),
    ("Mario", "Hoffmann", 30.20),
    ("Luki", "Holleis", 67.50),
    ("Jakob", "Junior", 119.00),
    ("Nico", "Kamerer", 63.50),
    ("Felix", "Kapo", 26.50),
    ("Jenny", "Katsch", 10.00),
    ("Fabian", "Kern", 98.00),
    ("Simon", "Kernöcker", 7.50),
    ("Philip", "Kruselburger", 24.50),
    ("Max", "Langmann", 82.50),
    ("Laurec", "Maurmair", 10.00),
    ("Johannes", "Meißl", 56.50),
    ("Simon", "Mungo", 52.50),
    ("Dominic", "Muttenthaler", 42.50),
    ("Damian", "Niedermeier", 12.50),
    ("Paz", "Rainer", 31.00),
    ("Tobi", "Richter", 15.00),
    ("Patrick", "Schatti", 10.00),
    ("Andreas", "Schweiger", 73.00),
    ("Paz", "Schweiger", 24.50),
    ("Sebastian", "Schweiger", 27.00),
    ("Gabor", "Szücs", 30.00),
    ("Tschalla", "Tschalla", 118.50),
    ("Jonas", "Wagenhofer", 3.50),
    ("Andi", "Windhofer", 3.00),
    ("Cem Peter", "Zoller", 6.50),
    ("Jamie", "Zoller", 19.50)
]

def main():
    print("Starte Import der Altsalden...")
    
    # Sicherstellen, dass die DB und Systemprodukte initialisiert sind
    init_db()
    
    erstellt_am = get_vienna_now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection() as conn:
        # Sicherstellen, dass das Systemprodukt 'Altsaldo' existiert
        conn.execute(
            "INSERT OR IGNORE INTO produkte (id, name, preis, kategorie_id) VALUES (9997, 'Altsaldo', 0.0, 9999)"
        )
        
        erfolgreich = 0
        uebersprungen = 0
        
        for vorname, nachname, betrag in SALDEN:
            # 1. Person suchen oder anlegen
            person_row = conn.execute(
                "SELECT id FROM personen WHERE LOWER(vorname) = LOWER(?) AND LOWER(nachname) = LOWER(?)",
                (vorname, nachname)
            ).fetchone()
            
            if person_row:
                person_id = person_row["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO personen (vorname, nachname) VALUES (?, ?)",
                    (vorname, nachname)
                )
                person_id = cur.lastrowid
                print(f"Neue Person angelegt: {nachname}, {vorname}")
            
            # 2. Prüfen, ob für diese Person bereits ein unbezahlter Altsaldo existiert, um Duplikate zu vermeiden
            bereits_da = conn.execute(
                """SELECT bp.id FROM bestellpositionen bp
                   JOIN bestellungen b ON bp.bestellung_id = b.id
                   WHERE b.person_id = ?
                     AND bp.produkt_id = 9997
                     AND b.abgeschlossen = 1
                     AND b.bezahlt = 0""",
                (person_id,)
            ).fetchone()
            
            if bereits_da:
                print(f"Altsaldo für {nachname}, {vorname} existiert bereits. Überspringe.")
                uebersprungen += 1
                continue
                
            # 3. Bestellung anlegen (abgeschlossen = 1, bezahlt = 0)
            cur_bestellung = conn.execute(
                """INSERT INTO bestellungen (person_id, abgeschlossen, bezahlt, erstellt_am)
                   VALUES (?, 1, 0, ?)""",
                (person_id, erstellt_am)
            )
            bestellung_id = cur_bestellung.lastrowid
            
            # 4. Position hinzufügen mit dem tatsächlichen Saldo als Einzelpreis
            conn.execute(
                """INSERT INTO bestellpositionen (bestellung_id, produkt_id, menge, einzelpreis)
                   VALUES (?, 9997, 1, ?)""",
                (bestellung_id, betrag)
            )
            print(f"Altsaldo von {betrag:.2f} € für {nachname}, {vorname} eingetragen.")
            erfolgreich += 1
            
        conn.commit()
        
    print("\n--- IMPORT ABGESCHLOSSEN ---")
    print(f"Erfolgreich importiert: {erfolgreich}")
    print(f"Übersprungen (bereits vorhanden): {uebersprungen}")

if __name__ == "__main__":
    main()
