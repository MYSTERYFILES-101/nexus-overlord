"""
NEXUS OVERLORD v2.0 - Database Service

SQLite Database Operations fuer alle Projekt-, Phasen-, Auftrags- und Chat-Daten.

Modul-Struktur:
    - Basis-Funktionen: get_db(), save_projekt(), get_projekt(), etc.
    - Phasen/Auftraege: save_phasen(), save_auftraege(), etc.
    - Fehler-Management: search_fehler(), save_fehler(), etc.
    - Analyse: get_projekt_analyse()
    - Uebergaben: save_uebergabe(), get_projekt_uebergaben(), etc.
    - Chat: get_chat_messages(), save_chat_message(), etc.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Any
import os
import json

# Logger konfigurieren
logger = logging.getLogger(__name__)

# Datenbank-Pfad
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'database',
    'nexus.db'
)


# ========================================
# BASIS-FUNKTIONEN
# ========================================

def get_db() -> sqlite3.Connection:
    """
    Erstellt eine Datenbankverbindung mit Row-Factory.

    Returns:
        sqlite3.Connection: Datenbankverbindung
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
        raise


def save_projekt(name: str, original_plan: str, enterprise_plan: str, bewertung: str) -> int:
    """
    Speichert ein neues Projekt in der Datenbank.

    Args:
        name: Projektname
        original_plan: Urspruenglicher Plan des Users
        enterprise_plan: Generierter Enterprise-Plan
        bewertung: KI-Bewertung

    Returns:
        int: Projekt-ID

    Raises:
        sqlite3.Error: Bei Datenbankfehlern
    """
    logger.info(f"Speichere neues Projekt: {name}")

    try:
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

        logger.info(f"Projekt gespeichert mit ID: {projekt_id}")
        return projekt_id

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern des Projekts '{name}': {e}")
        raise


def get_projekt(projekt_id: int) -> dict | None:
    """
    Laedt ein Projekt aus der Datenbank.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Projekt-Daten oder None wenn nicht gefunden
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
        projekt = cursor.fetchone()
        conn.close()
        return dict(projekt) if projekt else None

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden von Projekt {projekt_id}: {e}")
        return None


def get_all_projekte() -> list[dict]:
    """
    Laedt alle Projekte aus der Datenbank.

    Returns:
        list[dict]: Liste aller Projekte, sortiert nach Erstelldatum (neueste zuerst)
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projekte ORDER BY created_at DESC")
        projekte = cursor.fetchall()
        conn.close()
        return [dict(p) for p in projekte]

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden aller Projekte: {e}")
        return []


# ========================================
# PHASEN & AUFTRAeGE
# ========================================

def save_phasen(projekt_id: int, phasen_data: dict) -> list[tuple[int, int]]:
    """
    Speichert alle Phasen eines Projekts.

    Args:
        projekt_id: Projekt-ID
        phasen_data: Phasen-Daten aus dem Generator

    Returns:
        list[tuple[int, int]]: Liste von (phase_nummer, phase_id) Tupeln
    """
    logger.info(f"Speichere Phasen fuer Projekt {projekt_id}")

    try:
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

        logger.info(f"{len(phase_ids)} Phasen gespeichert fuer Projekt {projekt_id}")
        return phase_ids

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Phasen fuer Projekt {projekt_id}: {e}")
        raise


def save_auftraege(phase_id: int, auftraege: list[dict]) -> None:
    """
    Speichert alle Auftraege einer Phase.

    Args:
        phase_id: Phase-ID
        auftraege: Liste der Auftraege
    """
    logger.debug(f"Speichere {len(auftraege)} Auftraege fuer Phase {phase_id}")

    try:
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

        logger.debug(f"Auftraege fuer Phase {phase_id} gespeichert")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Auftraege fuer Phase {phase_id}: {e}")
        raise


def update_projekt_qualitaet(projekt_id: int, qualitaet_data: dict) -> None:
    """
    Aktualisiert ein Projekt mit der Qualitaetsbewertung.

    Args:
        projekt_id: Projekt-ID
        qualitaet_data: Qualitaetsdaten aus der Pruefung
    """
    logger.info(f"Aktualisiere Qualitaetsbewertung fuer Projekt {projekt_id}")

    try:
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

        logger.info(f"Qualitaetsbewertung fuer Projekt {projekt_id}: {qualitaet_data.get('gesamt_bewertung', 0)}/5")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren der Qualitaet fuer Projekt {projekt_id}: {e}")
        raise


def get_projekt_komplett(projekt_id: int) -> dict | None:
    """
    Laedt ein komplettes Projekt mit allen Phasen und Auftraegen.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Komplette Projektdaten inkl. Phasen und Auftraegen, oder None
    """
    logger.debug(f"Lade komplettes Projekt {projekt_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Projekt laden
        cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
        projekt_row = cursor.fetchone()
        if not projekt_row:
            conn.close()
            logger.warning(f"Projekt {projekt_id} nicht gefunden")
            return None

        projekt = dict(projekt_row)

        # Qualitaetsdetails parsen
        if projekt.get('qualitaet_details'):
            try:
                projekt['qualitaet_details'] = json.loads(projekt['qualitaet_details'])
            except json.JSONDecodeError:
                projekt['qualitaet_details'] = None

        # Phasen laden
        cursor.execute("SELECT * FROM phasen WHERE projekt_id = ? ORDER BY nummer", (projekt_id,))
        phasen = [dict(row) for row in cursor.fetchall()]

        # JSON-Felder fuer Phasen parsen und Auftraege laden
        for phase in phasen:
            # Abhaengigkeiten parsen
            if phase.get('abhaengigkeiten'):
                try:
                    phase['abhaengigkeiten'] = json.loads(phase['abhaengigkeiten'])
                except json.JSONDecodeError:
                    phase['abhaengigkeiten'] = []

            # Auftraege fuer diese Phase laden
            cursor.execute("SELECT * FROM auftraege WHERE phase_id = ? ORDER BY nummer", (phase['id'],))
            auftraege = [dict(row) for row in cursor.fetchall()]

            # JSON-Felder fuer Auftraege parsen
            for auftrag in auftraege:
                for field in ['schritte', 'dateien', 'technische_details', 'erfolgs_kriterien', 'regelwerk']:
                    if auftrag.get(field):
                        try:
                            auftrag[field] = json.loads(auftrag[field])
                        except json.JSONDecodeError:
                            auftrag[field] = [] if field != 'regelwerk' else {}

            phase['auftraege'] = auftraege

        projekt['phasen'] = phasen
        conn.close()

        logger.debug(f"Projekt {projekt_id} geladen mit {len(phasen)} Phasen")
        return projekt

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden von Projekt {projekt_id}: {e}")
        return None


def get_next_open_auftrag(projekt_id: int) -> dict | None:
    """
    Findet den naechsten offenen Auftrag eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Naechster offener Auftrag mit Phase-Info, oder None
    """
    try:
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

        # JSON-Felder parsen
        for field in ['schritte', 'dateien', 'technische_details', 'erfolgs_kriterien', 'regelwerk']:
            if auftrag.get(field):
                try:
                    auftrag[field] = json.loads(auftrag[field])
                except json.JSONDecodeError:
                    auftrag[field] = [] if field != 'regelwerk' else {}

        return auftrag

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Suchen des naechsten Auftrags fuer Projekt {projekt_id}: {e}")
        return None


def update_auftrag_status(auftrag_id: int, status: str) -> bool:
    """
    Aktualisiert den Status eines Auftrags.

    Args:
        auftrag_id: Auftrags-ID
        status: Neuer Status ('offen', 'in_arbeit', 'fertig', 'fehler')

    Returns:
        bool: True wenn erfolgreich
    """
    logger.debug(f"Aktualisiere Auftrag {auftrag_id} auf Status '{status}'")

    try:
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

        if affected > 0:
            logger.info(f"Auftrag {auftrag_id} Status geaendert auf '{status}'")
        return affected > 0

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren von Auftrag {auftrag_id}: {e}")
        return False


def get_projekt_stats(projekt_id: int) -> dict:
    """
    Ermittelt Statistiken fuer ein Projekt.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Statistiken ueber Phasen und Auftraege
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Phasen zaehlen
        cursor.execute("SELECT COUNT(*) FROM phasen WHERE projekt_id = ?", (projekt_id,))
        total_phasen = cursor.fetchone()[0]

        # Auftraege nach Status zaehlen
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

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Ermitteln der Stats fuer Projekt {projekt_id}: {e}")
        return {'total_phasen': 0, 'total_auftraege': 0, 'offen': 0, 'in_arbeit': 0, 'fertig': 0, 'fehler': 0}


# ========================================
# FEHLER-FUNKTIONEN (Erweitert v2.0)
# ========================================

def search_fehler(fehler_text: str) -> dict | None:
    """
    Sucht nach bekanntem Fehler in der Datenbank (Pattern-Matching).

    Args:
        fehler_text: Fehler-Text vom User

    Returns:
        dict: Gefundener Fehler oder None
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Bidirektionale Mustersuche
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
            logger.debug(f"Bekannter Fehler gefunden: ID {row['id']}")
            fehler = dict(row)
            # Tags parsen wenn vorhanden
            if fehler.get('tags'):
                try:
                    fehler['tags_list'] = json.loads(fehler['tags'])
                except json.JSONDecodeError:
                    fehler['tags_list'] = []
            return fehler
        return None

    except sqlite3.Error as e:
        logger.error(f"Fehler bei Fehlersuche: {e}")
        return None


def save_fehler(
    muster: str,
    kategorie: str,
    loesung: str,
    projekt_id: int | None = None,
    severity: str = "medium",
    tags: list[str] | None = None,
    stack_trace: str | None = None,
    fix_command: str | None = None
) -> int:
    """
    Speichert neuen Fehler in der Datenbank (erweitert).

    Args:
        muster: Fehler-Muster fuer zukuenftige Erkennung
        kategorie: Fehler-Kategorie (python, npm, permission, etc.)
        loesung: Loesung fuer den Fehler
        projekt_id: Optional - Verknuepftes Projekt
        severity: Schweregrad (critical, high, medium, low)
        tags: Optional - Tags als Liste
        stack_trace: Optional - Vollstaendiger Stack-Trace
        fix_command: Optional - Konkreter Fix-Befehl

    Returns:
        int: Fehler-ID
    """
    logger.info(f"Speichere neuen Fehler: Kategorie={kategorie}, Severity={severity}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        tags_json = json.dumps(tags) if tags else "[]"
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO fehler (
                muster, kategorie, loesung, erfolgsrate, anzahl,
                projekt_id, severity, status, tags, stack_trace,
                fix_command, similar_count, last_seen, created_at, updated_at
            )
            VALUES (?, ?, ?, 100, 1, ?, ?, 'aktiv', ?, ?, ?, 0, ?, ?, ?)
        """, (
            muster, kategorie, loesung,
            projekt_id, severity, tags_json, stack_trace,
            fix_command, now, now, now
        ))

        fehler_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Fehler gespeichert mit ID: {fehler_id}")
        return fehler_id

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern des Fehlers: {e}")
        return 0


def increment_fehler_count(fehler_id: int) -> None:
    """
    Erhoeht den Zaehler fuer einen bekannten Fehler und aktualisiert last_seen.

    Args:
        fehler_id: Fehler-ID
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fehler
            SET anzahl = anzahl + 1,
                last_seen = datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (fehler_id,))

        conn.commit()
        conn.close()

        logger.debug(f"Fehler {fehler_id} Zaehler erhoeht")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Erhoehen des Zaehlers fuer Fehler {fehler_id}: {e}")


def increment_similar_count(fehler_id: int) -> None:
    """
    Erhoeht den Similar-Counter fuer einen Fehler.

    Args:
        fehler_id: Fehler-ID
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fehler
            SET similar_count = similar_count + 1,
                updated_at = datetime('now')
            WHERE id = ?
        """, (fehler_id,))

        conn.commit()
        conn.close()

        logger.debug(f"Fehler {fehler_id} Similar-Count erhoeht")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Erhoehen des Similar-Counts fuer Fehler {fehler_id}: {e}")


def update_fehler_erfolgsrate(fehler_id: int, erfolg: bool) -> None:
    """
    Aktualisiert die Erfolgsrate eines Fehlers.

    Args:
        fehler_id: Fehler-ID
        erfolg: True wenn Loesung erfolgreich war
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Aktuelle Werte laden
        cursor.execute("SELECT anzahl, erfolgsrate FROM fehler WHERE id = ?", (fehler_id,))
        row = cursor.fetchone()

        if row:
            anzahl = row['anzahl']
            alte_rate = row['erfolgsrate']
            # Gleitender Durchschnitt
            neue_rate = ((alte_rate * (anzahl - 1)) + (100 if erfolg else 0)) / anzahl

            cursor.execute("""
                UPDATE fehler
                SET erfolgsrate = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (neue_rate, fehler_id))

            conn.commit()
            logger.debug(f"Fehler {fehler_id} Erfolgsrate aktualisiert: {neue_rate:.1f}%")

        conn.close()

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren der Erfolgsrate fuer Fehler {fehler_id}: {e}")


def update_fehler_status(fehler_id: int, status: str) -> bool:
    """
    Aktualisiert den Status eines Fehlers.

    Args:
        fehler_id: Fehler-ID
        status: Neuer Status ('aktiv', 'geloest', 'veraltet')

    Returns:
        bool: True wenn erfolgreich
    """
    if status not in ['aktiv', 'geloest', 'veraltet']:
        logger.warning(f"Ungueltiger Fehler-Status: {status}")
        return False

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fehler
            SET status = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (status, fehler_id))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        if affected > 0:
            logger.info(f"Fehler {fehler_id} Status geaendert auf '{status}'")
        return affected > 0

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren des Status fuer Fehler {fehler_id}: {e}")
        return False


def get_fehler_by_kategorie(kategorie: str, limit: int = 20) -> list[dict]:
    """
    Holt alle Fehler einer Kategorie.

    Args:
        kategorie: Fehler-Kategorie
        limit: Max Anzahl Ergebnisse

    Returns:
        list[dict]: Liste der Fehler
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM fehler
            WHERE kategorie = ?
            ORDER BY anzahl DESC, erfolgsrate DESC
            LIMIT ?
        """, (kategorie, limit))

        fehler = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Tags parsen
        for f in fehler:
            if f.get('tags'):
                try:
                    f['tags_list'] = json.loads(f['tags'])
                except json.JSONDecodeError:
                    f['tags_list'] = []

        return fehler

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden der Fehler fuer Kategorie {kategorie}: {e}")
        return []


def get_fehler_by_severity(severity: str, limit: int = 20) -> list[dict]:
    """
    Holt alle Fehler eines Severity-Levels.

    Args:
        severity: Severity-Level (critical, high, medium, low)
        limit: Max Anzahl Ergebnisse

    Returns:
        list[dict]: Liste der Fehler
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM fehler
            WHERE severity = ?
            ORDER BY anzahl DESC, last_seen DESC
            LIMIT ?
        """, (severity, limit))

        fehler = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return fehler

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden der Fehler fuer Severity {severity}: {e}")
        return []


def get_fehler_by_tags(tags: list[str], limit: int = 20) -> list[dict]:
    """
    Holt Fehler die bestimmte Tags enthalten.

    Args:
        tags: Liste von Tags zum Suchen
        limit: Max Anzahl Ergebnisse

    Returns:
        list[dict]: Liste der Fehler
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Baue LIKE-Bedingungen fuer jeden Tag
        conditions = " OR ".join(["tags LIKE ?" for _ in tags])
        params = [f'%"{tag}"%' for tag in tags]
        params.append(limit)

        cursor.execute(f"""
            SELECT * FROM fehler
            WHERE {conditions}
            ORDER BY anzahl DESC
            LIMIT ?
        """, params)

        fehler = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Tags parsen
        for f in fehler:
            if f.get('tags'):
                try:
                    f['tags_list'] = json.loads(f['tags'])
                except json.JSONDecodeError:
                    f['tags_list'] = []

        return fehler

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden der Fehler fuer Tags {tags}: {e}")
        return []


def get_fehler_stats() -> dict:
    """
    Gibt erweiterte Fehler-Statistiken zurueck.

    Returns:
        dict: Statistiken ueber Fehler
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Gesamt-Zahlen
        cursor.execute("SELECT COUNT(*) as total FROM fehler")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT AVG(erfolgsrate) as avg_rate FROM fehler")
        avg_rate = cursor.fetchone()['avg_rate'] or 0

        # Nach Kategorie
        cursor.execute("""
            SELECT kategorie, COUNT(*) as count
            FROM fehler
            GROUP BY kategorie
            ORDER BY count DESC
        """)
        kategorien = {row['kategorie']: row['count'] for row in cursor.fetchall()}

        # Nach Severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM fehler
            WHERE severity IS NOT NULL
            GROUP BY severity
        """)
        severities = {row['severity']: row['count'] for row in cursor.fetchall()}

        # Nach Status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM fehler
            WHERE status IS NOT NULL
            GROUP BY status
        """)
        statuses = {row['status']: row['count'] for row in cursor.fetchall()}

        # Aktive kritische Fehler
        cursor.execute("""
            SELECT COUNT(*) as count FROM fehler
            WHERE severity = 'critical' AND status = 'aktiv'
        """)
        critical_aktiv = cursor.fetchone()['count']

        # Letzte 7 Tage
        cursor.execute("""
            SELECT COUNT(*) as count FROM fehler
            WHERE created_at > datetime('now', '-7 days')
        """)
        letzte_7_tage = cursor.fetchone()['count']

        conn.close()

        return {
            'total': total,
            'avg_erfolgsrate': round(avg_rate, 1),
            'kategorien': kategorien,
            'severities': severities,
            'statuses': statuses,
            'critical_aktiv': critical_aktiv,
            'letzte_7_tage': letzte_7_tage
        }

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Ermitteln der Fehler-Stats: {e}")
        return {
            'total': 0, 'avg_erfolgsrate': 0, 'kategorien': {},
            'severities': {}, 'statuses': {}, 'critical_aktiv': 0, 'letzte_7_tage': 0
        }


def migrate_fehler_table() -> bool:
    """
    Migriert die Fehler-Tabelle auf die neue Struktur (v2.0).

    Fuegt neue Spalten hinzu falls sie nicht existieren.

    Returns:
        bool: True wenn Migration erfolgreich
    """
    logger.info("Starte Fehler-Tabellen Migration...")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Pruefe welche Spalten existieren
        cursor.execute("PRAGMA table_info(fehler)")
        existing_columns = {row['name'] for row in cursor.fetchall()}

        # Neue Spalten definieren (ohne CURRENT_TIMESTAMP wegen SQLite)
        new_columns = [
            ("projekt_id", "INTEGER"),
            ("severity", "TEXT DEFAULT 'medium'"),
            ("status", "TEXT DEFAULT 'aktiv'"),
            ("tags", "TEXT DEFAULT '[]'"),
            ("stack_trace", "TEXT"),
            ("fix_command", "TEXT"),
            ("similar_count", "INTEGER DEFAULT 0"),
            ("last_seen", "TEXT"),
            ("updated_at", "TEXT")
        ]

        # Fehlende Spalten hinzufuegen
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                logger.info(f"Fuege Spalte hinzu: {col_name}")
                cursor.execute(f"ALTER TABLE fehler ADD COLUMN {col_name} {col_type}")

        # Setze Default-Werte fuer bestehende Zeilen
        cursor.execute("""
            UPDATE fehler
            SET last_seen = created_at,
                updated_at = created_at
            WHERE last_seen IS NULL OR updated_at IS NULL
        """)

        # Index fuer neue Spalten
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fehler_severity ON fehler(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fehler_status ON fehler(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fehler_projekt ON fehler(projekt_id)")

        conn.commit()
        conn.close()

        logger.info("Fehler-Tabellen Migration abgeschlossen")
        return True

    except sqlite3.Error as e:
        logger.error(f"Fehler bei Migration: {e}")
        return False


# ========================================
# FUZZY-SEARCH FUNKTIONEN (Auftrag 5.2)
# ========================================

def calculate_similarity_score(
    fehler_text: str,
    db_fehler: dict,
    match_kategorie: bool = False
) -> float:
    """
    Berechnet Similarity-Score fuer einen Fehler.

    Scoring-System:
    - Text-Aehnlichkeit (rapidfuzz): 0-60 Punkte
    - Tag-Matching: 0-20 Punkte (2 pro Match, max 10 Tags)
    - Erfolgsrate-Bonus: 0-10 Punkte
    - Haeufigkeits-Bonus: 0-10 Punkte (log-skaliert)

    Args:
        fehler_text: Eingegebener Fehlertext
        db_fehler: Fehler-Dict aus Datenbank
        match_kategorie: True wenn Kategorie uebereinstimmt

    Returns:
        float: Score zwischen 0-100
    """
    from rapidfuzz import fuzz
    import math
    import json

    score = 0.0

    # 1. Text-Aehnlichkeit mit rapidfuzz (max 60 Punkte)
    muster = db_fehler.get('muster', '')
    if muster:
        # Token Set Ratio ist tolerant gegenueber Wortstellung
        text_score = fuzz.token_set_ratio(fehler_text.lower(), muster.lower())
        score += (text_score / 100) * 60

    # 2. Tag-Matching (max 20 Punkte, 2 pro Match)
    db_tags = db_fehler.get('tags_list', [])
    if not db_tags and db_fehler.get('tags'):
        try:
            db_tags = json.loads(db_fehler['tags'])
        except (json.JSONDecodeError, TypeError):
            db_tags = []

    # Extrahiere Tags aus dem Fehlertext
    from app.utils.fehler_helper import extract_tags, detect_category
    input_kategorie = detect_category(fehler_text)
    input_tags = extract_tags(fehler_text, input_kategorie)

    matching_tags = len(set(input_tags) & set(db_tags))
    score += min(matching_tags * 2, 20)

    # 3. Erfolgsrate-Bonus (max 10 Punkte)
    erfolgsrate = db_fehler.get('erfolgsrate', 0) or 0
    score += (erfolgsrate / 100) * 10

    # 4. Haeufigkeits-Bonus (max 10 Punkte, logarithmisch)
    anzahl = db_fehler.get('anzahl', 1) or 1
    # log2(anzahl + 1) * 2, max 10
    freq_score = min(math.log2(anzahl + 1) * 2, 10)
    score += freq_score

    # 5. Kategorie-Bonus (implizit durch bessere Filterung)
    if match_kategorie:
        score *= 1.1  # 10% Bonus bei Kategorie-Match

    return min(score, 100)


def search_similar_fehler(
    fehler_text: str,
    kategorie: str | None = None,
    limit: int = 3,
    min_score: float = 30.0
) -> list[tuple[dict, float]]:
    """
    Sucht aehnliche Fehler mit Fuzzy-Matching und Scoring.

    Args:
        fehler_text: Der zu suchende Fehlertext
        kategorie: Optional - Kategorie-Filter
        limit: Max. Anzahl Ergebnisse (default 3)
        min_score: Minimaler Score fuer Ergebnisse (default 30)

    Returns:
        list: Liste von (fehler_dict, score) Tupeln, sortiert nach Score
    """
    from rapidfuzz import fuzz
    import json

    logger.debug(f"Suche aehnliche Fehler fuer: {fehler_text[:100]}...")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Hole alle Fehler (oder gefiltert nach Kategorie)
        if kategorie:
            cursor.execute("""
                SELECT id, muster, kategorie, loesung, anzahl, erfolgsrate,
                       projekt_id, severity, status, tags, stack_trace,
                       fix_command, similar_count, last_seen
                FROM fehler
                WHERE kategorie = ? AND status != 'veraltet'
                ORDER BY anzahl DESC
            """, (kategorie,))
        else:
            cursor.execute("""
                SELECT id, muster, kategorie, loesung, anzahl, erfolgsrate,
                       projekt_id, severity, status, tags, stack_trace,
                       fix_command, similar_count, last_seen
                FROM fehler
                WHERE status != 'veraltet'
                ORDER BY anzahl DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            logger.debug("Keine Fehler in Datenbank gefunden")
            return []

        # Score fuer jeden Fehler berechnen
        scored_results = []
        for row in rows:
            fehler = dict(row)

            # Tags parsen
            try:
                fehler['tags_list'] = json.loads(fehler.get('tags', '[]'))
            except (json.JSONDecodeError, TypeError):
                fehler['tags_list'] = []

            # Score berechnen
            match_kat = kategorie and fehler.get('kategorie') == kategorie
            score = calculate_similarity_score(fehler_text, fehler, match_kat)

            if score >= min_score:
                scored_results.append((fehler, score))

        # Nach Score sortieren (absteigend)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Limit anwenden
        results = scored_results[:limit]

        logger.info(f"Gefunden: {len(results)} aehnliche Fehler (min_score={min_score})")
        return results

    except Exception as e:
        logger.error(f"Fehler bei Fuzzy-Search: {e}")
        return []


def get_best_match(fehler_text: str, kategorie: str | None = None) -> dict | None:
    """
    Findet den besten Match fuer einen Fehlertext.

    Args:
        fehler_text: Der zu suchende Fehlertext
        kategorie: Optional - Kategorie-Filter

    Returns:
        dict | None: Bester Fehler-Match mit Score, oder None
    """
    results = search_similar_fehler(fehler_text, kategorie, limit=1, min_score=50.0)

    if results:
        fehler, score = results[0]
        fehler['match_score'] = score
        return fehler

    return None


# ========================================
# ANALYSE-FUNKTIONEN
# ========================================

def get_projekt_analyse(projekt_id: int) -> dict | None:
    """
    Sammelt alle Daten fuer Projekt-Analyse.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Komplette Projekt-Daten fuer Analyse, oder None
    """
    logger.debug(f"Sammle Analyse-Daten fuer Projekt {projekt_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Projekt-Info
        cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
        projekt_row = cursor.fetchone()
        if not projekt_row:
            conn.close()
            logger.warning(f"Projekt {projekt_id} nicht gefunden fuer Analyse")
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

        # Aktueller Auftrag (in_arbeit oder naechster offener)
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

        # Letzte erledigte Auftraege
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

    except sqlite3.Error as e:
        logger.error(f"Fehler bei Projekt-Analyse fuer {projekt_id}: {e}")
        return None


# ========================================
# UeBERGABEN-FUNKTIONEN
# ========================================

def get_projekt_uebergaben(projekt_id: int) -> list[dict]:
    """
    Holt alle Uebergaben eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        list[dict]: Liste der Uebergaben mit Auftrag-Infos
    """
    try:
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

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden der Uebergaben fuer Projekt {projekt_id}: {e}")
        return []


def save_uebergabe(projekt_id: int, auftrag_id: int | None, datei_pfad: str, datei_name: str) -> int:
    """
    Speichert eine neue Uebergabe.

    Args:
        projekt_id: Projekt-ID
        auftrag_id: Auftrag-ID (kann None sein)
        datei_pfad: Pfad zur Datei
        datei_name: Original-Dateiname

    Returns:
        int: ID der neuen Uebergabe
    """
    logger.info(f"Speichere Uebergabe fuer Projekt {projekt_id}: {datei_name}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO uebergaben (projekt_id, auftrag_id, datei_pfad, datei_name, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (projekt_id, auftrag_id if auftrag_id else None, datei_pfad, datei_name))

        uebergabe_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Uebergabe gespeichert mit ID: {uebergabe_id}")
        return uebergabe_id

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Uebergabe: {e}")
        return 0


def get_uebergabe(uebergabe_id: int) -> dict | None:
    """
    Holt eine einzelne Uebergabe.

    Args:
        uebergabe_id: Uebergabe-ID

    Returns:
        dict: Uebergabe-Daten oder None
    """
    try:
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

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden der Uebergabe {uebergabe_id}: {e}")
        return None


def delete_uebergabe(uebergabe_id: int) -> bool:
    """
    Loescht eine Uebergabe.

    Args:
        uebergabe_id: Uebergabe-ID

    Returns:
        bool: True wenn erfolgreich
    """
    logger.info(f"Loesche Uebergabe {uebergabe_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Dateipfad fuer physisches Loeschen holen
        cursor.execute("SELECT datei_pfad FROM uebergaben WHERE id = ?", (uebergabe_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            logger.warning(f"Uebergabe {uebergabe_id} nicht gefunden")
            return False

        datei_pfad = row['datei_pfad']

        # Aus DB loeschen
        cursor.execute("DELETE FROM uebergaben WHERE id = ?", (uebergabe_id,))
        conn.commit()
        conn.close()

        # Physische Datei loeschen
        try:
            if os.path.exists(datei_pfad):
                os.remove(datei_pfad)
                logger.debug(f"Datei geloescht: {datei_pfad}")
        except OSError as e:
            logger.warning(f"Konnte Datei nicht loeschen: {datei_pfad} - {e}")

        return True

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Loeschen der Uebergabe {uebergabe_id}: {e}")
        return False


def get_current_auftrag_for_projekt(projekt_id: int) -> dict | None:
    """
    Holt den aktuell in Arbeit befindlichen Auftrag eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Auftrag-Daten oder None
    """
    try:
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

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden des aktuellen Auftrags fuer Projekt {projekt_id}: {e}")
        return None


# ========================================
# CHAT-FUNKTIONEN
# ========================================

def get_chat_messages(projekt_id: int, limit: int = 50) -> list[dict]:
    """
    Holt Chat-Nachrichten eines Projekts.

    Args:
        projekt_id: Projekt-ID
        limit: Max Anzahl Nachrichten

    Returns:
        list[dict]: Chat-Nachrichten sortiert nach Zeit (aelteste zuerst)
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                cm.id,
                cm.projekt_id,
                cm.auftrag_id,
                cm.typ,
                cm.inhalt,
                cm.created_at,
                a.nummer as auftrag_nummer,
                a.name as auftrag_name,
                p.nummer as phase_nummer
            FROM chat_messages cm
            LEFT JOIN auftraege a ON cm.auftrag_id = a.id
            LEFT JOIN phasen p ON a.phase_id = p.id
            WHERE cm.projekt_id = ?
            ORDER BY cm.created_at ASC
            LIMIT ?
        """, (projekt_id, limit))

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Laden der Chat-Nachrichten fuer Projekt {projekt_id}: {e}")
        return []


def save_chat_message(projekt_id: int, typ: str, inhalt: str, auftrag_id: int | None = None) -> int:
    """
    Speichert eine Chat-Nachricht.

    Args:
        projekt_id: Projekt-ID
        typ: Nachrichtentyp (USER, AUFTRAG, FEHLER, ANALYSE, SYSTEM, RUECKMELDUNG)
        inhalt: Nachrichteninhalt
        auftrag_id: Optional - Auftrag-ID fuer Verknuepfung

    Returns:
        int: ID der neuen Nachricht
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chat_messages (projekt_id, auftrag_id, typ, inhalt, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (projekt_id, auftrag_id, typ, inhalt))

        message_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.debug(f"Chat-Nachricht gespeichert: Typ={typ}, Projekt={projekt_id}")
        return message_id

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Chat-Nachricht: {e}")
        return 0


def delete_chat_messages(projekt_id: int) -> bool:
    """
    Loescht alle Chat-Nachrichten eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        bool: True wenn erfolgreich
    """
    logger.info(f"Loesche alle Chat-Nachrichten fuer Projekt {projekt_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chat_messages WHERE projekt_id = ?", (projekt_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"{deleted} Chat-Nachrichten geloescht fuer Projekt {projekt_id}")
        return True

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Loeschen der Chat-Nachrichten fuer Projekt {projekt_id}: {e}")
        return False


def get_chat_message_count(projekt_id: int) -> int:
    """
    Zaehlt Chat-Nachrichten eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        int: Anzahl Nachrichten
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM chat_messages WHERE projekt_id = ?", (projekt_id,))
        count = cursor.fetchone()['count']
        conn.close()
        return count

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Zaehlen der Chat-Nachrichten fuer Projekt {projekt_id}: {e}")
        return 0
