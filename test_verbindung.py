"""
Schnell-Test: Supabase-Verbindung prüfen
Starte mit: python test_verbindung.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config import DATABASE_URL

if "[DEIN-PASSWORT]" in DATABASE_URL:
    print("❌ Passwort fehlt noch in der .env Datei!")
    print("   Öffne .env und ersetze [DEIN-PASSWORT] mit deinem Supabase-Datenbankpasswort.")
    sys.exit(1)

print("🔌 Verbinde mit Supabase...")
try:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    conn.close()
    print("✅ Verbindung erfolgreich!")
    print("   Starte jetzt den Server: python server.py")
except Exception as e:
    print(f"❌ Verbindungsfehler: {e}")
    print("\n   Prüfe:")
    print("   1. Ist das Passwort in .env korrekt?")
    print("   2. Supabase Dashboard → Settings → Database → Connection string")
