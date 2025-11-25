"""
NEXUS OVERLORD v2.0 - Database Service

SQLite Database Operations für alle Projekt-, Phasen-, Auftrags- und Chat-Daten.

Modul-Struktur:
    - Basis-Funktionen: get_db(), save_projekt(), get_projekt(), etc.
    - Phasen/Aufträge: save_phasen(), save_auftraege(), etc.
    - Fehler-Management: search_fehler(), save_fehler(), etc.
    - Analyse: get_projekt_analyse()
    - Übergaben: save_uebergabe(), get_projekt_uebergaben(), etc.
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
        original_plan: Ursprünglicher Plan des Users
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
    Lädt ein Projekt aus der Datenbank.

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
    Lädt alle Projekte aus der Datenbank.

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
# PHASEN & AUFTRÄGE
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
    logger.info(f"Speichere Phasen für Projekt {projekt_id}")

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

        logger.info(f"{len(phase_ids)} Phasen gespeichert für Projekt {projekt_id}")
        return phase_ids

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Phasen für Projekt {projekt_id}: {e}")
        raise


def save_auftraege(phase_id: int, auftraege: list[dict]) -> None:
    """
    Speichert alle Aufträge einer Phase.

    Args:
        phase_id: Phase-ID
        auftraege: Liste der Aufträge
    """
    logger.debug(f"Speichere {len(auftraege)} Aufträge für Phase {phase_id}")

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

        logger.debug(f"Aufträge für Phase {phase_id} gespeichert")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Aufträge für Phase {phase_id}: {e}")
        raise


def update_projekt_qualitaet(projekt_id: int, qualitaet_data: dict) -> None:
    """
    Aktualisiert ein Projekt mit der Qualitätsbewertung.

    Args:
        projekt_id: Projekt-ID
        qualitaet_data: Qualitätsdaten aus der Prüfung
    """
    logger.info(f"Aktualisiere Qualitätsbewertung für Projekt {projekt_id}")

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

        logger.info(f"Qualitätsbewertung für Projekt {projekt_id}: {qualitaet_data.get('gesamt_bewertung', 0)}/5")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren der Qualität für Projekt {projekt_id}: {e}")
        raise


def get_projekt_komplett(projekt_id: int) -> dict | None:
    """
    Lädt ein komplettes Projekt mit allen Phasen und Aufträgen.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Komplette Projektdaten inkl. Phasen und Aufträgen, oder None
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

        # Qualitätsdetails parsen
        if projekt.get('qualitaet_details'):
            try:
                projekt['qualitaet_details'] = json.loads(projekt['qualitaet_details'])
            except json.JSONDecodeError:
                projekt['qualitaet_details'] = None

        # Phasen laden
        cursor.execute("SELECT * FROM phasen WHERE projekt_id = ? ORDER BY nummer", (projekt_id,))
        phasen = [dict(row) for row in cursor.fetchall()]

        # JSON-Felder für Phasen parsen und Aufträge laden
        for phase in phasen:
            # Abhängigkeiten parsen
            if phase.get('abhaengigkeiten'):
                try:
                    phase['abhaengigkeiten'] = json.loads(phase['abhaengigkeiten'])
                except json.JSONDecodeError:
                    phase['abhaengigkeiten'] = []

            # Aufträge für diese Phase laden
            cursor.execute("SELECT * FROM auftraege WHERE phase_id = ? ORDER BY nummer", (phase['id'],))
            auftraege = [dict(row) for row in cursor.fetchall()]

            # JSON-Felder für Aufträge parsen
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
    Findet den nächsten offenen Auftrag eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Nächster offener Auftrag mit Phase-Info, oder None
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
        logger.error(f"Fehler beim Suchen des nächsten Auftrags für Projekt {projekt_id}: {e}")
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
            logger.info(f"Auftrag {auftrag_id} Status geändert auf '{status}'")
        return affected > 0

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren von Auftrag {auftrag_id}: {e}")
        return False


def get_projekt_stats(projekt_id: int) -> dict:
    """
    Ermittelt Statistiken für ein Projekt.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Statistiken über Phasen und Aufträge
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Phasen zählen
        cursor.execute("SELECT COUNT(*) FROM phasen WHERE projekt_id = ?", (projekt_id,))
        total_phasen = cursor.fetchone()[0]

        # Aufträge nach Status zählen
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
        logger.error(f"Fehler beim Ermitteln der Stats für Projekt {projekt_id}: {e}")
        return {'total_phasen': 0, 'total_auftraege': 0, 'offen': 0, 'in_arbeit': 0, 'fertig': 0, 'fehler': 0}


# ========================================
# FEHLER-FUNKTIONEN
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
            return dict(row)
        return None

    except sqlite3.Error as e:
        logger.error(f"Fehler bei Fehlersuche: {e}")
        return None


def save_fehler(muster: str, kategorie: str, loesung: str) -> int:
    """
    Speichert neuen Fehler in der Datenbank.

    Args:
        muster: Fehler-Muster für zukünftige Erkennung
        kategorie: Fehler-Kategorie (python, npm, permission, etc.)
        loesung: Lösung für den Fehler

    Returns:
        int: Fehler-ID
    """
    logger.info(f"Speichere neuen Fehler: Kategorie={kategorie}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO fehler (muster, kategorie, loesung, erfolgsrate, anzahl, created_at)
            VALUES (?, ?, ?, 100, 1, datetime('now'))
        """, (muster, kategorie, loesung))

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
    Erhöht den Zähler für einen bekannten Fehler.

    Args:
        fehler_id: Fehler-ID
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fehler
            SET anzahl = anzahl + 1
            WHERE id = ?
        """, (fehler_id,))

        conn.commit()
        conn.close()

        logger.debug(f"Fehler {fehler_id} Zähler erhöht")

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Erhöhen des Zählers für Fehler {fehler_id}: {e}")


def update_fehler_erfolgsrate(fehler_id: int, erfolg: bool) -> None:
    """
    Aktualisiert die Erfolgsrate eines Fehlers.

    Args:
        fehler_id: Fehler-ID
        erfolg: True wenn Lösung erfolgreich war
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
                SET erfolgsrate = ?
                WHERE id = ?
            """, (neue_rate, fehler_id))

            conn.commit()
            logger.debug(f"Fehler {fehler_id} Erfolgsrate aktualisiert: {neue_rate:.1f}%")

        conn.close()

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Aktualisieren der Erfolgsrate für Fehler {fehler_id}: {e}")


def get_fehler_stats() -> dict:
    """
    Gibt Fehler-Statistiken zurück.

    Returns:
        dict: Statistiken über Fehler
    """
    try:
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

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Ermitteln der Fehler-Stats: {e}")
        return {'total': 0, 'avg_erfolgsrate': 0, 'kategorien': {}}


# ========================================
# ANALYSE-FUNKTIONEN
# ========================================

def get_projekt_analyse(projekt_id: int) -> dict | None:
    """
    Sammelt alle Daten für Projekt-Analyse.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Komplette Projekt-Daten für Analyse, oder None
    """
    logger.debug(f"Sammle Analyse-Daten für Projekt {projekt_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Projekt-Info
        cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
        projekt_row = cursor.fetchone()
        if not projekt_row:
            conn.close()
            logger.warning(f"Projekt {projekt_id} nicht gefunden für Analyse")
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

        # Letzte erledigte Aufträge
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
        logger.error(f"Fehler bei Projekt-Analyse für {projekt_id}: {e}")
        return None


# ========================================
# ÜBERGABEN-FUNKTIONEN
# ========================================

def get_projekt_uebergaben(projekt_id: int) -> list[dict]:
    """
    Holt alle Übergaben eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        list[dict]: Liste der Übergaben mit Auftrag-Infos
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
        logger.error(f"Fehler beim Laden der Übergaben für Projekt {projekt_id}: {e}")
        return []


def save_uebergabe(projekt_id: int, auftrag_id: int | None, datei_pfad: str, datei_name: str) -> int:
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
    logger.info(f"Speichere Übergabe für Projekt {projekt_id}: {datei_name}")

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

        logger.info(f"Übergabe gespeichert mit ID: {uebergabe_id}")
        return uebergabe_id

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern der Übergabe: {e}")
        return 0


def get_uebergabe(uebergabe_id: int) -> dict | None:
    """
    Holt eine einzelne Übergabe.

    Args:
        uebergabe_id: Übergabe-ID

    Returns:
        dict: Übergabe-Daten oder None
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
        logger.error(f"Fehler beim Laden der Übergabe {uebergabe_id}: {e}")
        return None


def delete_uebergabe(uebergabe_id: int) -> bool:
    """
    Löscht eine Übergabe.

    Args:
        uebergabe_id: Übergabe-ID

    Returns:
        bool: True wenn erfolgreich
    """
    logger.info(f"Lösche Übergabe {uebergabe_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Dateipfad für physisches Löschen holen
        cursor.execute("SELECT datei_pfad FROM uebergaben WHERE id = ?", (uebergabe_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            logger.warning(f"Übergabe {uebergabe_id} nicht gefunden")
            return False

        datei_pfad = row['datei_pfad']

        # Aus DB löschen
        cursor.execute("DELETE FROM uebergaben WHERE id = ?", (uebergabe_id,))
        conn.commit()
        conn.close()

        # Physische Datei löschen
        try:
            if os.path.exists(datei_pfad):
                os.remove(datei_pfad)
                logger.debug(f"Datei gelöscht: {datei_pfad}")
        except OSError as e:
            logger.warning(f"Konnte Datei nicht löschen: {datei_pfad} - {e}")

        return True

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Löschen der Übergabe {uebergabe_id}: {e}")
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
        logger.error(f"Fehler beim Laden des aktuellen Auftrags für Projekt {projekt_id}: {e}")
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
        list[dict]: Chat-Nachrichten sortiert nach Zeit (älteste zuerst)
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
        logger.error(f"Fehler beim Laden der Chat-Nachrichten für Projekt {projekt_id}: {e}")
        return []


def save_chat_message(projekt_id: int, typ: str, inhalt: str, auftrag_id: int | None = None) -> int:
    """
    Speichert eine Chat-Nachricht.

    Args:
        projekt_id: Projekt-ID
        typ: Nachrichtentyp (USER, AUFTRAG, FEHLER, ANALYSE, SYSTEM, RUECKMELDUNG)
        inhalt: Nachrichteninhalt
        auftrag_id: Optional - Auftrag-ID für Verknüpfung

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
    Löscht alle Chat-Nachrichten eines Projekts.

    Args:
        projekt_id: Projekt-ID

    Returns:
        bool: True wenn erfolgreich
    """
    logger.info(f"Lösche alle Chat-Nachrichten für Projekt {projekt_id}")

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chat_messages WHERE projekt_id = ?", (projekt_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"{deleted} Chat-Nachrichten gelöscht für Projekt {projekt_id}")
        return True

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Löschen der Chat-Nachrichten für Projekt {projekt_id}: {e}")
        return False


def get_chat_message_count(projekt_id: int) -> int:
    """
    Zählt Chat-Nachrichten eines Projekts.

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
        logger.error(f"Fehler beim Zählen der Chat-Nachrichten für Projekt {projekt_id}: {e}")
        return 0
