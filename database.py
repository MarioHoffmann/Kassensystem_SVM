"""
Kassensystem – Datenbankanbindung (SQLite, lokal)
"""

import datetime
import sqlite3
from pathlib import Path
from config import DB_PATH


def get_vienna_now() -> datetime.datetime:
    """Gibt das aktuelle Datum und Uhrzeit für die Zeitzone Europa/Wien (mit Sommer-/Winterzeit) zurück."""
    utc_now = datetime.datetime.utcnow()
    year = utc_now.year
    march_31 = datetime.datetime(year, 3, 31, 1, 0, 0)
    dst_start = march_31 - datetime.timedelta(days=(march_31.weekday() + 1) % 7)
    oct_31 = datetime.datetime(year, 10, 31, 1, 0, 0)
    dst_end = oct_31 - datetime.timedelta(days=(oct_31.weekday() + 1) % 7)
    
    if dst_start <= utc_now < dst_end:
        offset = 2
    else:
        offset = 1
    return utc_now + datetime.timedelta(hours=offset)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # stabiler bei mehreren Zugriffen
    conn.execute("PRAGMA foreign_keys=ON")
    return conn



def init_db():
    """Erstellt alle Tabellen wenn sie noch nicht existieren."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS personen (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                vorname  TEXT NOT NULL,
                nachname TEXT NOT NULL,
                UNIQUE(vorname, nachname)
            );

            CREATE TABLE IF NOT EXISTS kategorien (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS produkte (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                preis        REAL NOT NULL,
                kategorie_id INTEGER NOT NULL REFERENCES kategorien(id)
            );

            CREATE TABLE IF NOT EXISTS bestellungen (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id     INTEGER NOT NULL REFERENCES personen(id),
                erstellt_am   TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                abgeschlossen INTEGER NOT NULL DEFAULT 0,
                bezahlt       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS bestellpositionen (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                bestellung_id INTEGER NOT NULL REFERENCES bestellungen(id) ON DELETE CASCADE,
                produkt_id    INTEGER NOT NULL REFERENCES produkte(id),
                menge         INTEGER NOT NULL DEFAULT 1,
                einzelpreis   REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS statistiken (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                datum  TEXT NOT NULL UNIQUE,
                umsatz REAL NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO kategorien (id, name) VALUES (9999, 'System');
            INSERT OR IGNORE INTO produkte (id, name, preis, kategorie_id) VALUES (9999, 'Teilzahlung', 0.0, 9999);
            INSERT OR IGNORE INTO produkte (id, name, preis, kategorie_id) VALUES (9998, 'Trinkgeld', 0.0, 9999);
        """)
    print("SQLite-Datenbank bereit:", DB_PATH)
