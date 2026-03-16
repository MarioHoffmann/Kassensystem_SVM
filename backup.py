"""
Kassensystem – Automatisches Backup nach OneDrive
Läuft automatisch im Hintergrund wenn server.py gestartet wird.
Sichert die SQLite-Datenbank stündlich nach OneDrive.
"""

import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR


def backup_erstellen():
    """Kopiert die aktuelle Datenbank in den OneDrive-Backup-Ordner."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        zeitstempel = datetime.now().strftime("%Y-%m-%d_%H-%M")
        ziel = BACKUP_DIR / f"kassensystem_{zeitstempel}.db"
        shutil.copy2(DB_PATH, ziel)

        # Alte Backups aufräumen – nur die letzten 48 Stunden behalten
        alle_backups = sorted(BACKUP_DIR.glob("kassensystem_*.db"))
        while len(alle_backups) > 48:
            alle_backups.pop(0).unlink()

        print(f"✅ Backup erstellt: {ziel.name}")
    except Exception as e:
        print(f"⚠️  Backup fehlgeschlagen: {e}")


def backup_loop(intervall_sekunden: int = 3600):
    """Führt stündlich ein Backup durch (läuft im Hintergrund-Thread)."""
    while True:
        backup_erstellen()
        time.sleep(intervall_sekunden)


def starte_backup_service():
    """Startet den Backup-Service als Daemon-Thread."""
    t = threading.Thread(target=backup_loop, daemon=True)
    t.start()
    print(f"🔄 Backup-Service aktiv → {BACKUP_DIR}")
