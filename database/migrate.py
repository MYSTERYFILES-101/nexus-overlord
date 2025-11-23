#!/usr/bin/env python3
"""
NEXUS OVERLORD v2.0 - Database Migration Script
Erstellt die SQLite-Datenbank mit allen Tabellen und fügt Test-Daten ein.
"""

import sqlite3
import os
from datetime import datetime

# Pfade
DB_PATH = os.path.join(os.path.dirname(__file__), 'nexus.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def create_database():
    """Erstellt die Datenbank und führt das Schema aus."""
    print("🔧 Erstelle Datenbank...")

    # Alte DB löschen falls vorhanden
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"   ✓ Alte Datenbank gelöscht: {DB_PATH}")

    # Neue DB erstellen
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Schema laden und ausführen
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()

    print(f"   ✓ Datenbank erstellt: {DB_PATH}")
    print(f"   ✓ Schema geladen: {SCHEMA_PATH}")

    return conn


def insert_test_data(conn):
    """Fügt Test-Daten in die Datenbank ein."""
    print("\n📋 Füge Test-Daten ein...")

    cursor = conn.cursor()

    # Test-Projekt
    cursor.execute("""
        INSERT INTO projekte (name, original_plan, enterprise_plan, bewertung, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        'NEXUS OVERLORD v2.0',
        'KI-Orchestrierungs-Tool für Projektplanung',
        'Enterprise Multi-Agent System mit 3 Kacheln, 5 Buttons, Fehler-DB und PDF Export',
        'Bewertung: 9/10 - Sehr gut durchdacht',
        'in_arbeit'
    ))
    projekt_id = cursor.lastrowid
    print(f"   ✓ Test-Projekt erstellt (ID: {projekt_id})")

    # Test-Phase
    cursor.execute("""
        INSERT INTO phasen (projekt_id, nummer, name, status)
        VALUES (?, ?, ?, ?)
    """, (projekt_id, 1, 'Basis-Struktur', 'in_arbeit'))
    phase_id = cursor.lastrowid
    print(f"   ✓ Test-Phase erstellt (ID: {phase_id})")

    # Test-Aufträge
    auftraege_data = [
        ('1.1', 'Datenbank neu', 'Neue Tabellen erstellen', 'in_arbeit'),
        ('1.2', 'Ordner-Struktur', 'Projektordner anlegen', 'offen'),
        ('1.3', 'Model-IDs korrigieren', 'Gemini 3 Pro + Sonnet 4.5', 'offen'),
        ('1.4', 'Startseite 3 Kacheln', 'Neues Layout', 'offen'),
    ]

    auftrag_ids = []
    for nummer, name, beschreibung, status in auftraege_data:
        cursor.execute("""
            INSERT INTO auftraege (phase_id, nummer, name, beschreibung, status)
            VALUES (?, ?, ?, ?, ?)
        """, (phase_id, nummer, name, beschreibung, status))
        auftrag_ids.append(cursor.lastrowid)

    print(f"   ✓ {len(auftraege_data)} Test-Aufträge erstellt")

    # Test-Rückmeldung
    cursor.execute("""
        INSERT INTO rueckmeldungen (auftrag_id, inhalt)
        VALUES (?, ?)
    """, (auftrag_ids[0], '✅ Datenbank erfolgreich erstellt mit 6 Tabellen'))
    print(f"   ✓ Test-Rückmeldung erstellt")

    # Test-Fehler in Datenbank
    fehler_data = [
        ('ModuleNotFoundError: No module named', 'python', 'pip install [modul-name]', 95, 3),
        ('EACCES: permission denied', 'permission', 'sudo chmod +x oder sudo ausführen', 90, 5),
        ('sqlite3.OperationalError: no such table', 'database', 'Migration ausführen: python migrate.py', 100, 2),
    ]

    for muster, kategorie, loesung, erfolgsrate, anzahl in fehler_data:
        cursor.execute("""
            INSERT INTO fehler (muster, kategorie, loesung, erfolgsrate, anzahl)
            VALUES (?, ?, ?, ?, ?)
        """, (muster, kategorie, loesung, erfolgsrate, anzahl))

    print(f"   ✓ {len(fehler_data)} Test-Fehler erstellt")

    # Test-Übergabe
    cursor.execute("""
        INSERT INTO uebergaben (auftrag_id, datei_pfad)
        VALUES (?, ?)
    """, (auftrag_ids[0], '/projekt/uebergaben/2025-11-23_22-34_auftrag-1-1.md'))
    print(f"   ✓ Test-Übergabe erstellt")

    conn.commit()
    print("\n✅ Alle Test-Daten erfolgreich eingefügt!")


def verify_database(conn):
    """Prüft ob die Datenbank korrekt erstellt wurde."""
    print("\n🔍 Prüfe Datenbank...")

    cursor = conn.cursor()

    # Tabellen prüfen
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tables = cursor.fetchall()

    print(f"\n   Tabellen ({len(tables)}):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   ✓ {table[0]:20s} ({count} Einträge)")

    # Foreign Keys prüfen
    cursor.execute("PRAGMA foreign_keys")
    fk_status = cursor.fetchone()[0]
    print(f"\n   Foreign Keys: {'✓ Aktiviert' if fk_status else '✗ Deaktiviert'}")

    # Beispiel-Abfrage: Projekt mit Phasen und Aufträgen
    cursor.execute("""
        SELECT
            p.name as projekt,
            ph.name as phase,
            a.nummer,
            a.name as auftrag,
            a.status
        FROM projekte p
        LEFT JOIN phasen ph ON ph.projekt_id = p.id
        LEFT JOIN auftraege a ON a.phase_id = ph.id
        ORDER BY ph.nummer, a.nummer
    """)

    results = cursor.fetchall()
    if results:
        print(f"\n   Beispiel-Abfrage (Projekt → Phasen → Aufträge):")
        for row in results:
            print(f"   {row[0]} → {row[1]} → {row[2]} {row[3]} ({row[4]})")

    print("\n✅ Datenbank-Prüfung erfolgreich!")


def main():
    """Hauptfunktion für die Migration."""
    print("=" * 60)
    print("NEXUS OVERLORD v2.0 - Database Migration")
    print("=" * 60)
    print()

    try:
        # Datenbank erstellen
        conn = create_database()

        # Test-Daten einfügen
        insert_test_data(conn)

        # Verifizieren
        verify_database(conn)

        # Schließen
        conn.close()

        print("\n" + "=" * 60)
        print("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 60)
        print(f"\nDatenbank: {DB_PATH}")
        print(f"Tabellen: 6 (projekte, phasen, auftraege, rueckmeldungen, fehler, uebergaben)")
        print(f"Test-Daten: ✓ Eingefügt")
        print(f"Foreign Keys: ✓ Aktiviert")

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
