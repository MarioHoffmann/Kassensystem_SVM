"""
Kassensystem – Zentrale Konfiguration
"""

from pathlib import Path

# Pfade
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "kassensystem.db"
BACKUP_DIR = Path.home() / "OneDrive" / "Kassensystem-Backups"

# App
APP_TITLE = "SVM Kantine"

# Passwörter
APP_PIN                  = "kantine2026"
PRODUKT_PASSWORT         = "12345"
STATISTIK_PASSWORT       = "admin1"
PERSON_LOESCHEN_PASSWORT = "admin1"
