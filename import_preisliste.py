"""
Hilfsskript zum Importieren und Aktualisieren der SVM Preisliste.
Führe dieses Skript auf PythonAnywhere mit 'python import_preisliste.py' aus.
"""

import sys
import os

# Pfad anpassen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection, init_db

PREISLISTE = {
    "Getränke": [
        ("1/2 Bier", 4.50),
        ("1/3 Bier", 3.50),
        ("1/2 Spritzer", 5.00),
        ("1/4 Spritzer", 3.50),
        ("Limo", 3.00),
        ("Mineral", 2.50),
        ("Apfelsaft gespritzt", 3.00),
        ("Johannisbeere gespritzt", 3.00),
        ("Red Bull", 3.50),
        ("Kaffee", 2.80),
        ("Tee", 2.00)
    ],
    "Shots, Longdrinks": [
        ("Underberg", 3.00),
        ("Jägermeister", 3.00),
        ("Klopfer", 3.00),
        ("Schnäpse", 3.00),
        ("SVM-Shot", 3.00),
        ("Cola Rum", 3.50),
        ("Wodka Orange", 4.00),
        ("Rüscherl", 3.00),
        ("Gin Tonic", 4.00),
        ("Wodka Bull", 4.50),
        ("Barcadi Cola", 4.00)
    ],
    "Speisen": [
        ("Bosna", 5.50),
        ("Bosna scharf", 5.50),
        ("Leberkässemmel", 3.00),
        ("Pommes", 3.50)
    ],
    "Tabak": [
        ("Zigaretten", 8.00),
        ("Snus", 8.00)
    ]
}

def main():
    print("Starte Import/Aktualisierung der Preisliste...")
    init_db()
    
    with get_connection() as conn:
        for kat_name, produkte in PREISLISTE.items():
            # 1. Kategorie suchen oder anlegen
            kat_row = conn.execute(
                "SELECT id FROM kategorien WHERE LOWER(name) = LOWER(?)", (kat_name,)
            ).fetchone()
            
            if kat_row:
                kat_id = kat_row["id"]
                # Name korrigieren falls abweichende Schreibweise
                conn.execute("UPDATE kategorien SET name = ? WHERE id = ?", (kat_name, kat_id))
            else:
                cur = conn.execute("INSERT INTO kategorien (name) VALUES (?)", (kat_name,))
                kat_id = cur.lastrowid
                print(f"Kategorie erstellt: {kat_name}")
                
            # 2. Produkte in dieser Kategorie verarbeiten
            for prod_name, preis in produkte:
                prod_row = conn.execute(
                    "SELECT id, preis, kategorie_id FROM produkte WHERE LOWER(name) = LOWER(?)", (prod_name,)
                ).fetchone()
                
                if prod_row:
                    prod_id = prod_row["id"]
                    alt_preis = prod_row["preis"]
                    alt_kat = prod_row["kategorie_id"]
                    
                    if alt_preis != preis or alt_kat != kat_id:
                        conn.execute(
                            "UPDATE produkte SET name = ?, preis = ?, kategorie_id = ? WHERE id = ?",
                            (prod_name, preis, kat_id, prod_id)
                        )
                        print(f"Produkt aktualisiert: {prod_name} -> {preis:.2f} € (Kategorie ID: {kat_id})")
                    else:
                        # Nur Schreibweise korrigieren
                        conn.execute("UPDATE produkte SET name = ? WHERE id = ?", (prod_name, prod_id))
                else:
                    conn.execute(
                        "INSERT INTO produkte (name, preis, kategorie_id) VALUES (?, ?, ?)",
                        (prod_name, preis, kat_id)
                    )
                    print(f"Produkt neu angelegt: {prod_name} ({preis:.2f} €) in {kat_name}")
                    
        conn.commit()
    print("--- PREISLISTE ERFOLGREICH AKTUALISIERT ---")

if __name__ == "__main__":
    main()
