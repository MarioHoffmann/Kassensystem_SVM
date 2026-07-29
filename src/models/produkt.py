"""
Kassensystem – Datenmodell Kategorien & Produkte (SQLite)
"""

import sqlite3
from database import get_connection


class KategorieError(Exception):
    pass


class ProduktError(Exception):
    pass


# ─────────────────────────────────── Kategorien ──────────────────────────────

def alle_kategorien() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM kategorien WHERE id != 9999 AND archiviert = 0 ORDER BY sort_order ASC, name ASC").fetchall()
    return [dict(r) for r in rows]


def kategorie_anlegen(name: str) -> int:
    name = name.strip()
    if not name:
        raise KategorieError("Kategoriename darf nicht leer sein.")
    try:
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO kategorien (name) VALUES (?)", (name,))
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise KategorieError(f"Kategorie '{name}' existiert bereits.")


def kategorie_bearbeiten(kategorie_id: int, name: str):
    name = name.strip()
    if not name:
        raise KategorieError("Kategoriename darf nicht leer sein.")
    try:
        with get_connection() as conn:
            conn.execute("UPDATE kategorien SET name = ? WHERE id = ?", (name, kategorie_id))
    except sqlite3.IntegrityError:
        raise KategorieError(f"Kategorie '{name}' existiert bereits.")


def kategorie_loeschen(kategorie_id: int):
    with get_connection() as conn:
        # Kategorie und alle darin enthaltenen Produkte als archiviert markieren
        conn.execute("UPDATE kategorien SET archiviert = 1 WHERE id = ?", (kategorie_id,))
        conn.execute("UPDATE produkte SET archiviert = 1 WHERE kategorie_id = ?", (kategorie_id,))


# ─────────────────────────────────── Produkte ────────────────────────────────

def produkte_der_kategorie(kategorie_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.id, p.name, p.preis, k.name AS kategorie
               FROM produkte p JOIN kategorien k ON p.kategorie_id = k.id
               WHERE p.kategorie_id = ? AND p.archiviert = 0
               ORDER BY p.sort_order ASC, p.name ASC""",
            (kategorie_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def alle_produkte() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.id, p.name, p.preis, k.name AS kategorie, p.kategorie_id
               FROM produkte p JOIN kategorien k ON p.kategorie_id = k.id
               WHERE p.kategorie_id != 9999 AND p.archiviert = 0
               ORDER BY k.sort_order ASC, k.name ASC, p.sort_order ASC, p.name ASC"""
        ).fetchall()
    return [dict(r) for r in rows]


def produkt_anlegen(name: str, preis: float, kategorie_id: int) -> int:
    name = name.strip()
    if not name:
        raise ProduktError("Produktname darf nicht leer sein.")
    if preis < 0:
        raise ProduktError("Preis darf nicht negativ sein.")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO produkte (name, preis, kategorie_id) VALUES (?, ?, ?)",
            (name, preis, kategorie_id)
        )
    return cur.lastrowid


def produkt_bearbeiten(produkt_id: int, name: str, preis: float, kategorie_id: int):
    name = name.strip()
    if not name:
        raise ProduktError("Produktname darf nicht leer sein.")
    if preis < 0:
        raise ProduktError("Preis darf nicht negativ sein.")
    with get_connection() as conn:
        conn.execute(
            "UPDATE produkte SET name=?, preis=?, kategorie_id=? WHERE id=?",
            (name, preis, kategorie_id, produkt_id)
        )


def produkt_loeschen(produkt_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE produkte SET archiviert = 1 WHERE id = ?", (produkt_id,))


def kategorien_reihenfolge_speichern(ids: list[int]):
    with get_connection() as conn:
        for idx, kid in enumerate(ids):
            conn.execute("UPDATE kategorien SET sort_order = ? WHERE id = ?", (idx, kid))


def produkte_reihenfolge_speichern(ids: list[int]):
    with get_connection() as conn:
        for idx, pid in enumerate(ids):
            conn.execute("UPDATE produkte SET sort_order = ? WHERE id = ?", (idx, pid))
