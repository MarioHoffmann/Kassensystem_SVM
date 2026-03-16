"""
Kassensystem – Datenbankanbindung (SQLite, lokal)
"""

import sqlite3
from pathlib import Path
from config import DB_PATH


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
        """)
    print("SQLite-Datenbank bereit:", DB_PATH)
