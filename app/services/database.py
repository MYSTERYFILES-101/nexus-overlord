"""
NEXUS OVERLORD v2.0 - Database Service
SQLite Database Operations
"""

import sqlite3
from datetime import datetime
import os
import json


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'nexus.db')


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_projekt(name, original_plan, enterprise_plan, bewertung):
    """
    Save project to database

    Args:
        name: Project name
        original_plan: User's original project plan
        enterprise_plan: Generated enterprise plan
        bewertung: AI evaluation

    Returns:
        int: project_id
    """
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO projekte (name, original_plan, enterprise_plan, bewertung, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'erstellt', ?, ?)
    """, (name, original_plan, enterprise_plan, bewertung, now, now))

    projekt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return projekt_id


def get_projekt(projekt_id):
    """
    Get project by ID

    Args:
        projekt_id: Project ID

    Returns:
        dict: Project data or None
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
    projekt = cursor.fetchone()
    conn.close()
    return dict(projekt) if projekt else None


def get_all_projekte():
    """Get all projects"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projekte ORDER BY created_at DESC")
    projekte = cursor.fetchall()
    conn.close()
    return [dict(p) for p in projekte]


def save_phasen(projekt_id: int, phasen_data: dict) -> list:
    """
    Save all phases to database

    Args:
        projekt_id: Project ID
        phasen_data: Phases data from generation

    Returns:
        list: List of tuples (phase_nummer, phase_id)
    """
    conn = get_db()
    cursor = conn.cursor()
    phase_ids = []

    for phase in phasen_data.get('phasen', []):
        cursor.execute("""
            INSERT INTO phasen (projekt_id, nummer, name, beschreibung,
                               abhaengigkeiten, prioritaet, geschaetzte_dauer, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'offen', datetime('now'))
        """, (
            projekt_id,
            phase['nummer'],
            phase['name'],
            phase.get('beschreibung', ''),
            json.dumps(phase.get('abhaengigkeiten', [])),
            phase.get('prioritaet', 'mittel'),
            phase.get('geschaetzte_dauer', '')
        ))
        phase_ids.append((phase['nummer'], cursor.lastrowid))

    conn.commit()
    conn.close()
    return phase_ids


def save_auftraege(phase_id: int, auftraege: list) -> None:
    """
    Save all tasks for a phase

    Args:
        phase_id: Phase ID
        auftraege: List of tasks
    """
    conn = get_db()
    cursor = conn.cursor()

    for auftrag in auftraege:
        cursor.execute("""
            INSERT INTO auftraege (phase_id, nummer, name, beschreibung,
                                  schritte, dateien, technische_details,
                                  erfolgs_kriterien, regelwerk, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'offen', datetime('now'))
        """, (
            phase_id,
            auftrag['auftrag_nummer'],
            auftrag['name'],
            auftrag.get('beschreibung', ''),
            json.dumps(auftrag.get('schritte', [])),
            json.dumps(auftrag.get('dateien', [])),
            json.dumps(auftrag.get('technische_details', [])),
            json.dumps(auftrag.get('erfolgs_kriterien', [])),
            json.dumps(auftrag.get('regelwerk', {}))
        ))

    conn.commit()
    conn.close()


def update_projekt_qualitaet(projekt_id: int, qualitaet_data: dict) -> None:
    """
    Update project with quality assessment

    Args:
        projekt_id: Project ID
        qualitaet_data: Quality data from assessment
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE projekte
        SET qualitaet_bewertung = ?,
            qualitaet_details = ?,
            status = 'bereit',
            updated_at = datetime('now')
        WHERE id = ?
    """, (
        qualitaet_data.get('gesamt_bewertung', 0),
        json.dumps(qualitaet_data),
        projekt_id
    ))

    conn.commit()
    conn.close()


def get_projekt_komplett(projekt_id: int) -> dict:
    """
    Load complete project with all phases and tasks

    Args:
        projekt_id: Project ID

    Returns:
        dict: Complete project data including phases and tasks
    """
    conn = get_db()
    cursor = conn.cursor()

    # Load project
    cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
    projekt_row = cursor.fetchone()
    if not projekt_row:
        conn.close()
        return None

    projekt = dict(projekt_row)

    # Parse quality details if present
    if projekt.get('qualitaet_details'):
        try:
            projekt['qualitaet_details'] = json.loads(projekt['qualitaet_details'])
        except:
            projekt['qualitaet_details'] = None

    # Load phases
    cursor.execute("SELECT * FROM phasen WHERE projekt_id = ? ORDER BY nummer", (projekt_id,))
    phasen = [dict(row) for row in cursor.fetchall()]

    # Parse JSON fields for phases and load tasks
    for phase in phasen:
        # Parse dependencies
        if phase.get('abhaengigkeiten'):
            try:
                phase['abhaengigkeiten'] = json.loads(phase['abhaengigkeiten'])
            except:
                phase['abhaengigkeiten'] = []

        # Load tasks for this phase
        cursor.execute("SELECT * FROM auftraege WHERE phase_id = ? ORDER BY nummer", (phase['id'],))
        auftraege = [dict(row) for row in cursor.fetchall()]

        # Parse JSON fields for tasks
        for auftrag in auftraege:
            for field in ['schritte', 'dateien', 'technische_details', 'erfolgs_kriterien', 'regelwerk']:
                if auftrag.get(field):
                    try:
                        auftrag[field] = json.loads(auftrag[field])
                    except:
                        auftrag[field] = [] if field != 'regelwerk' else {}

        phase['auftraege'] = auftraege

    projekt['phasen'] = phasen
    conn.close()
    return projekt


def get_next_open_auftrag(projekt_id: int) -> dict:
    """
    Find the next open task for a project (Auftrag 4.2)

    Args:
        projekt_id: Project ID

    Returns:
        dict: Next open task with phase info, or None if no open tasks
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, p.name as phase_name, p.nummer as phase_nummer,
               (SELECT COUNT(*) FROM phasen WHERE projekt_id = ?) as total_phasen
        FROM auftraege a
        JOIN phasen p ON a.phase_id = p.id
        WHERE p.projekt_id = ?
        AND a.status = 'offen'
        ORDER BY p.nummer, a.nummer
        LIMIT 1
    """, (projekt_id, projekt_id))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    auftrag = dict(row)

    # Parse JSON fields
    for field in ['schritte', 'dateien', 'technische_details', 'erfolgs_kriterien', 'regelwerk']:
        if auftrag.get(field):
            try:
                auftrag[field] = json.loads(auftrag[field])
            except:
                auftrag[field] = [] if field != 'regelwerk' else {}

    return auftrag


def update_auftrag_status(auftrag_id: int, status: str) -> bool:
    """
    Update task status (Auftrag 4.2)

    Args:
        auftrag_id: Task ID
        status: New status ('offen', 'in_arbeit', 'fertig', 'fehler')

    Returns:
        bool: True if successful
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE auftraege
        SET status = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (status, auftrag_id))

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def get_projekt_stats(projekt_id: int) -> dict:
    """
    Get project statistics (Auftrag 4.2)

    Returns:
        dict: Statistics about phases and tasks
    """
    conn = get_db()
    cursor = conn.cursor()

    # Count phases
    cursor.execute("SELECT COUNT(*) FROM phasen WHERE projekt_id = ?", (projekt_id,))
    total_phasen = cursor.fetchone()[0]

    # Count tasks by status
    cursor.execute("""
        SELECT a.status, COUNT(*) as count
        FROM auftraege a
        JOIN phasen p ON a.phase_id = p.id
        WHERE p.projekt_id = ?
        GROUP BY a.status
    """, (projekt_id,))

    stats = {
        'total_phasen': total_phasen,
        'total_auftraege': 0,
        'offen': 0,
        'in_arbeit': 0,
        'fertig': 0,
        'fehler': 0
    }

    for row in cursor.fetchall():
        stats[row['status']] = row['count']
        stats['total_auftraege'] += row['count']

    conn.close()
    return stats


# ========================================
# FEHLER-FUNKTIONEN (Auftrag 4.3)
# ========================================

def search_fehler(fehler_text: str) -> dict:
    """
    Sucht nach bekanntem Fehler in der Datenbank (Pattern-Matching)

    Args:
        fehler_text: Fehler-Text vom User

    Returns:
        dict: Gefundener Fehler oder None
    """
    conn = get_db()
    cursor = conn.cursor()

    # Suche nach Muster im Fehler-Text (bidirektional)
    cursor.execute("""
        SELECT * FROM fehler
        WHERE ? LIKE '%' || muster || '%'
        OR muster LIKE '%' || ? || '%'
        ORDER BY erfolgsrate DESC, anzahl DESC
        LIMIT 1
    """, (fehler_text, fehler_text))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def save_fehler(muster: str, kategorie: str, loesung: str) -> int:
    """
    Speichert neuen Fehler in der Datenbank

    Args:
        muster: Fehler-Muster für zukünftige Erkennung
        kategorie: Fehler-Kategorie (python, npm, permission, etc.)
        loesung: Lösung für den Fehler

    Returns:
        int: Fehler-ID
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO fehler (muster, kategorie, loesung, erfolgsrate, anzahl, created_at)
        VALUES (?, ?, ?, 100, 1, datetime('now'))
    """, (muster, kategorie, loesung))

    fehler_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return fehler_id


def increment_fehler_count(fehler_id: int) -> None:
    """
    Erhöht den Zähler für einen bekannten Fehler

    Args:
        fehler_id: Fehler-ID
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE fehler
        SET anzahl = anzahl + 1
        WHERE id = ?
    """, (fehler_id,))

    conn.commit()
    conn.close()


def update_fehler_erfolgsrate(fehler_id: int, erfolg: bool) -> None:
    """
    Aktualisiert die Erfolgsrate eines Fehlers

    Args:
        fehler_id: Fehler-ID
        erfolg: True wenn Lösung erfolgreich war
    """
    conn = get_db()
    cursor = conn.cursor()

    # Berechne neue Erfolgsrate basierend auf Anzahl
    cursor.execute("SELECT anzahl, erfolgsrate FROM fehler WHERE id = ?", (fehler_id,))
    row = cursor.fetchone()

    if row:
        anzahl = row['anzahl']
        alte_rate = row['erfolgsrate']
        # Gleitender Durchschnitt
        neue_rate = ((alte_rate * (anzahl - 1)) + (100 if erfolg else 0)) / anzahl

        cursor.execute("""
            UPDATE fehler
            SET erfolgsrate = ?
            WHERE id = ?
        """, (neue_rate, fehler_id))

        conn.commit()

    conn.close()


def get_fehler_stats() -> dict:
    """
    Gibt Fehler-Statistiken zurück

    Returns:
        dict: Statistiken über Fehler
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM fehler")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT AVG(erfolgsrate) as avg_rate FROM fehler")
    avg_rate = cursor.fetchone()['avg_rate'] or 0

    cursor.execute("""
        SELECT kategorie, COUNT(*) as count
        FROM fehler
        GROUP BY kategorie
        ORDER BY count DESC
    """)
    kategorien = {row['kategorie']: row['count'] for row in cursor.fetchall()}

    conn.close()

    return {
        'total': total,
        'avg_erfolgsrate': round(avg_rate, 1),
        'kategorien': kategorien
    }


# ========================================
# ANALYSE-FUNKTIONEN (Auftrag 4.4)
# ========================================

def get_projekt_analyse(projekt_id: int) -> dict:
    """
    Sammelt alle Daten für Projekt-Analyse

    Args:
        projekt_id: Project ID

    Returns:
        dict: Komplette Projekt-Daten für Analyse
    """
    conn = get_db()
    cursor = conn.cursor()

    # Projekt-Info
    cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
    projekt_row = cursor.fetchone()
    if not projekt_row:
        conn.close()
        return None

    projekt = dict(projekt_row)

    # Phasen mit Statistik
    cursor.execute("""
        SELECT p.*,
               COUNT(a.id) as total_auftraege,
               SUM(CASE WHEN a.status = 'fertig' THEN 1 ELSE 0 END) as erledigte,
               SUM(CASE WHEN a.status = 'in_arbeit' THEN 1 ELSE 0 END) as in_arbeit,
               SUM(CASE WHEN a.status = 'offen' THEN 1 ELSE 0 END) as offene
        FROM phasen p
        LEFT JOIN auftraege a ON p.id = a.phase_id
        WHERE p.projekt_id = ?
        GROUP BY p.id
        ORDER BY p.nummer
    """, (projekt_id,))
    phasen = [dict(row) for row in cursor.fetchall()]

    # Gesamt-Statistik berechnen
    total_auftraege = sum(p.get('total_auftraege', 0) or 0 for p in phasen)
    erledigte_auftraege = sum(p.get('erledigte', 0) or 0 for p in phasen)
    in_arbeit_auftraege = sum(p.get('in_arbeit', 0) or 0 for p in phasen)

    # Fortschritt berechnen
    fortschritt = 0
    if total_auftraege > 0:
        fortschritt = round((erledigte_auftraege / total_auftraege) * 100)

    # Aktueller Auftrag (in_arbeit oder nächster offener)
    cursor.execute("""
        SELECT a.*, p.name as phase_name, p.nummer as phase_nummer
        FROM auftraege a
        JOIN phasen p ON a.phase_id = p.id
        WHERE p.projekt_id = ?
        AND a.status IN ('in_arbeit', 'offen')
        ORDER BY
            CASE WHEN a.status = 'in_arbeit' THEN 0 ELSE 1 END,
            p.nummer, a.nummer
        LIMIT 1
    """, (projekt_id,))
    aktueller_auftrag_row = cursor.fetchone()
    aktueller_auftrag = dict(aktueller_auftrag_row) if aktueller_auftrag_row else None

    # Aktuelle Phase ermitteln
    aktuelle_phase = None
    for phase in phasen:
        if phase.get('offene', 0) > 0 or phase.get('in_arbeit', 0) > 0:
            aktuelle_phase = phase
            break
    if not aktuelle_phase and phasen:
        aktuelle_phase = phasen[-1]

    # Letzte erledigte Aufträge (für "Zuletzt erledigt")
    cursor.execute("""
        SELECT a.name, a.nummer, p.name as phase_name, p.nummer as phase_nummer
        FROM auftraege a
        JOIN phasen p ON a.phase_id = p.id
        WHERE p.projekt_id = ?
        AND a.status = 'fertig'
        ORDER BY a.updated_at DESC
        LIMIT 3
    """, (projekt_id,))
    letzte_erledigte = [dict(row) for row in cursor.fetchall()]

    # Offene Fehler (letzte 7 Tage)
    cursor.execute("""
        SELECT COUNT(*) as anzahl FROM fehler
        WHERE created_at > datetime('now', '-7 days')
    """)
    offene_fehler = cursor.fetchone()['anzahl']

    conn.close()

    return {
        'projekt': projekt,
        'phasen': phasen,
        'total_phasen': len(phasen),
        'total_auftraege': total_auftraege,
        'erledigte_auftraege': erledigte_auftraege,
        'in_arbeit_auftraege': in_arbeit_auftraege,
        'offene_auftraege': total_auftraege - erledigte_auftraege - in_arbeit_auftraege,
        'fortschritt': fortschritt,
        'aktuelle_phase': aktuelle_phase,
        'aktueller_auftrag': aktueller_auftrag,
        'letzte_erledigte': letzte_erledigte,
        'offene_fehler': offene_fehler
    }


# ========================================
# ÜBERGABEN-FUNKTIONEN (Auftrag 4.5)
# ========================================

def get_projekt_uebergaben(projekt_id: int) -> list:
    """
    Holt alle Übergaben eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        list: Liste der Übergaben mit Auftrag-Infos
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.datei_pfad,
            u.datei_name,
            u.created_at,
            u.auftrag_id,
            u.projekt_id,
            a.nummer as auftrag_nummer,
            a.name as auftrag_name,
            p.nummer as phase_nummer,
            p.name as phase_name
        FROM uebergaben u
        LEFT JOIN auftraege a ON u.auftrag_id = a.id
        LEFT JOIN phasen p ON a.phase_id = p.id
        WHERE u.projekt_id = ? OR p.projekt_id = ?
        ORDER BY u.created_at DESC
    """, (projekt_id, projekt_id))

    uebergaben = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return uebergaben


def save_uebergabe(projekt_id: int, auftrag_id: int, datei_pfad: str, datei_name: str) -> int:
    """
    Speichert eine neue Übergabe.

    Args:
        projekt_id: Projekt-ID
        auftrag_id: Auftrag-ID (kann None sein)
        datei_pfad: Pfad zur Datei
        datei_name: Original-Dateiname

    Returns:
        int: ID der neuen Übergabe
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO uebergaben (projekt_id, auftrag_id, datei_pfad, datei_name, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (projekt_id, auftrag_id if auftrag_id else None, datei_pfad, datei_name))

    uebergabe_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return uebergabe_id


def get_uebergabe(uebergabe_id: int) -> dict:
    """
    Holt eine einzelne Übergabe.

    Args:
        uebergabe_id: Übergabe-ID

    Returns:
        dict: Übergabe-Daten oder None
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.datei_pfad,
            u.datei_name,
            u.created_at,
            u.auftrag_id,
            u.projekt_id,
            a.nummer as auftrag_nummer,
            a.name as auftrag_name,
            p.nummer as phase_nummer
        FROM uebergaben u
        LEFT JOIN auftraege a ON u.auftrag_id = a.id
        LEFT JOIN phasen p ON a.phase_id = p.id
        WHERE u.id = ?
    """, (uebergabe_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_uebergabe(uebergabe_id: int) -> bool:
    """
    Löscht eine Übergabe.

    Args:
        uebergabe_id: Übergabe-ID

    Returns:
        bool: True wenn erfolgreich
    """
    conn = get_db()
    cursor = conn.cursor()

    # Erst den Dateipfad holen für physisches Löschen
    cursor.execute("SELECT datei_pfad FROM uebergaben WHERE id = ?", (uebergabe_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    datei_pfad = row['datei_pfad']

    # Aus DB löschen
    cursor.execute("DELETE FROM uebergaben WHERE id = ?", (uebergabe_id,))
    conn.commit()
    conn.close()

    # Physische Datei löschen (falls vorhanden)
    try:
        if os.path.exists(datei_pfad):
            os.remove(datei_pfad)
    except Exception:
        pass  # Ignorieren wenn Datei nicht gelöscht werden kann

    return True


def get_current_auftrag_for_projekt(projekt_id: int) -> dict:
    """
    Holt den aktuell in Arbeit befindlichen Auftrag eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Auftrag-Daten oder None
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.nummer, a.name, p.nummer as phase_nummer
        FROM auftraege a
        JOIN phasen p ON a.phase_id = p.id
        WHERE p.projekt_id = ?
        AND a.status = 'in_arbeit'
        ORDER BY p.nummer, a.nummer
        LIMIT 1
    """, (projekt_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
