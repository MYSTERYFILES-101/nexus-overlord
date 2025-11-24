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
