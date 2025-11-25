"""
NEXUS OVERLORD v2.0 - Fehler Analyzer (Auftrag 4.3 + 5.1 + 5.2 + 5.3)

Analysiert Fehler mit Gemini 3 Pro und erstellt Loesungs-Auftraege mit Opus 4.5.
Erweitert mit automatischer Kategorisierung, Severity-Erkennung und Tags.
Auftrag 5.2: Fuzzy-Matching mit rapidfuzz fuer intelligente Fehlersuche.
Auftrag 5.3: Intelligentes Merging - Duplikate vermeiden, Learning-Loop.
"""

import json
import logging
import re

from app.services.openrouter import get_client
from app.services.database import (
    search_fehler, save_fehler, increment_fehler_count,
    increment_similar_count, search_similar_fehler, get_best_match,
    save_or_merge_fehler, update_fehler_feedback
)
from app.utils.fehler_helper import (
    detect_category, detect_severity, extract_tags,
    detect_fix_command, analyze_fehler as helper_analyze
)

# Logger
logger = logging.getLogger(__name__)


def analyze_fehler(fehler_text: str, projekt_name: str = "NEXUS OVERLORD", projekt_id: int | None = None) -> dict:
    """
    Analysiert einen Fehler und gibt Loesung zurueck.

    Workflow:
    1. Automatische Kategorisierung und Severity-Erkennung
    2. Pruefe Fehler-Datenbank nach bekanntem Muster
    3. Falls bekannt -> Loesung aus DB + Similar-Count erhoehen
    4. Falls neu -> Gemini 3 Pro analysiert, Opus 4.5 erstellt Loesungs-Auftrag
    5. Speichere mit erweiterten Metadaten (Severity, Tags, Stack-Trace)

    Args:
        fehler_text: Fehler-Text vom User
        projekt_name: Name des Projekts
        projekt_id: Optional - Projekt-ID fuer Verknuepfung

    Returns:
        dict: Erweiterte Fehler-Analyse mit Severity, Tags, etc.
    """
    logger.info(f"Analysiere Fehler fuer Projekt: {projekt_name}")

    # 0. Automatische Vor-Analyse mit Helper
    auto_analyse = helper_analyze(fehler_text, projekt_id)
    kategorie = auto_analyse['kategorie']
    severity = auto_analyse['severity']
    tags = auto_analyse['tags']
    fix_command = auto_analyse['fix_command']

    logger.debug(f"Auto-Analyse: Kategorie={kategorie}, Severity={severity}, Tags={tags}")

    # 1. Fuzzy-Search in Fehler-Datenbank (Auftrag 5.2)
    similar_fehler = search_similar_fehler(fehler_text, kategorie, limit=3, min_score=30.0)
    best_match = get_best_match(fehler_text, kategorie)

    if best_match and best_match.get('match_score', 0) >= 70.0:
        # Hohe Uebereinstimmung gefunden (>= 70%)
        logger.info(f"Best Match gefunden: ID {best_match['id']} (Score: {best_match['match_score']:.1f})")
        increment_fehler_count(best_match['id'])

        # Wenn aehnlicher aber nicht exakt gleicher Fehler
        if best_match.get('muster') and best_match['muster'] not in fehler_text:
            increment_similar_count(best_match['id'])

        return {
            'bekannt': True,
            'match_score': best_match.get('match_score', 0),
            'kategorie': best_match.get('kategorie', kategorie),
            'severity': best_match.get('severity', severity),
            'status': best_match.get('status', 'aktiv'),
            'tags': best_match.get('tags_list', tags),
            'ursache': f"Bekannter Fehler (#{best_match['id']}) - Match: {best_match.get('match_score', 0):.0f}%",
            'loesung': best_match['loesung'],
            'fix_command': best_match.get('fix_command', fix_command),
            'auftrag': _create_quick_auftrag(best_match),
            'fehler_id': best_match['id'],
            'erfolgsrate': best_match.get('erfolgsrate', 0),
            'anzahl': best_match.get('anzahl', 1),
            'similar_count': best_match.get('similar_count', 0),
            'similar_fehler': [(f, s) for f, s in similar_fehler if f['id'] != best_match['id']][:2]
        }

    # 1b. Fallback auf exakte Suche (alte Methode)
    bekannter_fehler = search_fehler(fehler_text)
    if bekannter_fehler:
        logger.info(f"Exakter Match gefunden: ID {bekannter_fehler['id']}")
        increment_fehler_count(bekannter_fehler['id'])

        return {
            'bekannt': True,
            'match_score': 100.0,
            'kategorie': bekannter_fehler.get('kategorie', kategorie),
            'severity': bekannter_fehler.get('severity', severity),
            'status': bekannter_fehler.get('status', 'aktiv'),
            'tags': bekannter_fehler.get('tags_list', tags),
            'ursache': f"Bekannter Fehler (#{bekannter_fehler['id']}) - Exakter Match",
            'loesung': bekannter_fehler['loesung'],
            'fix_command': bekannter_fehler.get('fix_command', fix_command),
            'auftrag': _create_quick_auftrag(bekannter_fehler),
            'fehler_id': bekannter_fehler['id'],
            'erfolgsrate': bekannter_fehler.get('erfolgsrate', 0),
            'anzahl': bekannter_fehler.get('anzahl', 1),
            'similar_count': bekannter_fehler.get('similar_count', 0),
            'similar_fehler': similar_fehler[:2]
        }

    # 2. Neuer Fehler -> KI-Analyse
    try:
        logger.info("Neuer Fehler - starte KI-Analyse")

        # Gemini 3 Pro analysiert den Fehler
        ki_analyse = _analyze_with_gemini(fehler_text)

        # Kombiniere KI-Analyse mit Auto-Analyse
        final_kategorie = ki_analyse.get('kategorie', kategorie)
        final_severity = detect_severity(fehler_text, final_kategorie)

        # Opus 4.5 erstellt Loesungs-Auftrag
        auftrag = _create_auftrag_with_opus(fehler_text, ki_analyse, projekt_name)

        # Fehler in Datenbank speichern ODER mit aehnlichem mergen (Auftrag 5.3)
        merge_result = save_or_merge_fehler(
            muster=ki_analyse.get('muster', fehler_text[:100]),
            kategorie=final_kategorie,
            loesung=ki_analyse.get('loesung', 'Keine Loesung gefunden'),
            projekt_id=projekt_id,
            severity=final_severity,
            tags=tags,
            stack_trace=fehler_text if len(fehler_text) > 200 else None,
            fix_command=ki_analyse.get('fix_command', fix_command)
        )

        fehler_id = merge_result['fehler_id']
        was_merged = merge_result['merged']

        logger.info(f"Fehler {'gemerged' if was_merged else 'erstellt'} mit ID: {fehler_id}")

        return {
            'bekannt': was_merged,  # Wenn gemerged, dann war es quasi bekannt
            'match_score': merge_result.get('match_score', 0),
            'merged': was_merged,
            'merge_action': merge_result.get('action', 'unknown'),
            'kategorie': final_kategorie,
            'severity': final_severity,
            'status': 'aktiv',
            'tags': tags,
            'ursache': ki_analyse.get('ursache', 'Unbekannt'),
            'loesung': ki_analyse.get('loesung', 'Keine Loesung gefunden'),
            'fix_command': ki_analyse.get('fix_command', fix_command),
            'auftrag': auftrag,
            'fehler_id': fehler_id,
            'erfolgsrate': 100 if not was_merged else 50,  # Bei Merge: neutrale Rate
            'anzahl': 1,
            'similar_count': 0,
            'similar_fehler': similar_fehler[:3]  # Zeige aehnliche Fehler als Referenz
        }

    except Exception as e:
        logger.error(f"KI-Analyse fehlgeschlagen: {e}")

        # Fallback bei API-Fehler - nutze Auto-Analyse
        return {
            'bekannt': False,
            'match_score': 0,
            'kategorie': kategorie,
            'severity': severity,
            'status': 'aktiv',
            'tags': tags,
            'ursache': f'Analyse fehlgeschlagen: {str(e)}',
            'loesung': _get_fallback_loesung(fehler_text),
            'fix_command': fix_command,
            'auftrag': _get_fallback_auftrag(fehler_text, kategorie, severity),
            'fehler_id': None,
            'erfolgsrate': 0,
            'anzahl': 0,
            'similar_count': 0,
            'similar_fehler': similar_fehler[:3]  # Zeige aehnliche Fehler als Referenz
        }


def _analyze_with_gemini(fehler_text: str) -> dict:
    """
    Analysiert Fehler mit Gemini 3 Pro.

    Args:
        fehler_text: Fehler-Text

    Returns:
        dict: Analyse-Ergebnis mit Kategorie, Ursache, Loesung, Muster, Fix-Command
    """
    client = get_client()

    prompt = f"""Du bist ein Fehler-Analyst fuer Software-Entwicklung.

Analysiere diesen Fehler und gib zurueck:
1. Kategorie: python, npm, permission, database, network, dependency, config, git, docker, other
2. Ursache: Kurz und praezise (1-2 Saetze)
3. Loesung: Schritt fuer Schritt (nummeriert)
4. Muster: Fuer zukuenftige Erkennung (z.B. "ModuleNotFoundError", "EACCES")
5. Fix-Command: Konkreter Befehl falls moeglich (z.B. "pip install flask")

Fehler-Text:
{fehler_text}

Antworte NUR mit einem JSON-Objekt (keine Erklaerungen):
{{"kategorie": "...", "ursache": "...", "loesung": "...", "muster": "...", "fix_command": "..."}}"""

    messages = [{"role": "user", "content": prompt}]

    response = client.call_gemini(messages, temperature=0.3, timeout=30)

    # JSON aus Antwort extrahieren
    try:
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except json.JSONDecodeError:
        logger.warning("JSON-Parsing fehlgeschlagen, nutze Fallback")
        return {
            'kategorie': detect_category(fehler_text),
            'ursache': 'Konnte nicht automatisch analysiert werden',
            'loesung': response,
            'muster': fehler_text[:50],
            'fix_command': detect_fix_command(fehler_text)
        }


def _create_auftrag_with_opus(fehler_text: str, analyse: dict, projekt_name: str) -> str:
    """
    Erstellt Loesungs-Auftrag mit Opus 4.5.

    Args:
        fehler_text: Original Fehler-Text
        analyse: Analyse von Gemini
        projekt_name: Projektname

    Returns:
        str: Formatierter Loesungs-Auftrag
    """
    client = get_client()

    prompt = f"""Erstelle einen kurzen, praezisen Loesungs-Auftrag fuer Claude Code.

FEHLER:
{fehler_text[:1000]}

ANALYSE:
- Kategorie: {analyse.get('kategorie', 'unknown')}
- Ursache: {analyse.get('ursache', 'Unbekannt')}
- Loesung: {analyse.get('loesung', 'Keine')}
- Fix-Command: {analyse.get('fix_command', 'Keiner')}

Erstelle einen Auftrag im folgenden Format:

═══════════════════════════════════════════════════════════════
🔧 FEHLER-LOESUNG
═══════════════════════════════════════════════════════════════

📋 PROBLEM
[Kurze Beschreibung des Problems]

📋 LOESUNG
[Nummerierte Schritte zur Loesung]

📋 BEFEHLE
```bash
[Konkrete Befehle zum Ausfuehren]
```

═══════════════════════════════════════════════════════════════

Halte es kurz und praezise. Nur das Noetigste."""

    messages = [{"role": "user", "content": prompt}]

    response = client.call_sonnet(messages, temperature=0.3, timeout=30)

    return response


def _create_quick_auftrag(fehler: dict) -> str:
    """
    Erstellt schnellen Auftrag aus bekanntem Fehler.

    Args:
        fehler: Fehler aus Datenbank

    Returns:
        str: Formatierter Auftrag
    """
    severity_icon = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }.get(fehler.get('severity', 'medium'), '🟡')

    tags_str = ', '.join(fehler.get('tags_list', [])) if fehler.get('tags_list') else 'Keine'

    fix_cmd = fehler.get('fix_command', '')
    fix_section = f"""
📋 FIX-BEFEHL
```bash
{fix_cmd}
```
""" if fix_cmd else ""

    return f"""═══════════════════════════════════════════════════════════════
🔧 BEKANNTE LOESUNG (#{fehler['id']})
═══════════════════════════════════════════════════════════════

📋 KATEGORIE
{fehler.get('kategorie', 'Unbekannt')}

{severity_icon} SEVERITY
{fehler.get('severity', 'medium').upper()}

🏷️ TAGS
{tags_str}

📋 LOESUNG
{fehler['loesung']}
{fix_section}
📊 STATISTIK
- Erfolgsrate: {fehler.get('erfolgsrate', 0):.0f}%
- Bereits {fehler.get('anzahl', 1)}x aufgetreten
- Aehnliche Fehler: {fehler.get('similar_count', 0)}

═══════════════════════════════════════════════════════════════"""


def _get_fallback_loesung(fehler_text: str) -> str:
    """
    Generiert Fallback-Loesung basierend auf Fehler-Kategorie.

    Args:
        fehler_text: Fehlertext

    Returns:
        str: Fallback-Loesungsschritte
    """
    kategorie = detect_category(fehler_text)

    fallbacks = {
        'python': '1. Pruefe die Python-Version (python --version)\n2. Installiere fehlende Module (pip install <modul>)\n3. Pruefe Imports und Pfade',
        'npm': '1. Loesche node_modules und package-lock.json\n2. Fuehre npm install aus\n3. Pruefe Node.js Version (node --version)',
        'permission': '1. Pruefe Datei-Berechtigungen (ls -la)\n2. Nutze sudo falls noetig\n3. Pruefe Benutzer und Gruppe',
        'database': '1. Pruefe Datenbank-Verbindung\n2. Pruefe SQL-Syntax\n3. Pruefe ob Tabellen existieren',
        'network': '1. Pruefe Netzwerk-Verbindung\n2. Pruefe Firewall-Einstellungen\n3. Pruefe ob Service laeuft',
        'dependency': '1. Installiere fehlende Abhaengigkeit\n2. Pruefe Version der Abhaengigkeit\n3. Pruefe Kompatibilitaet',
        'config': '1. Pruefe .env Datei\n2. Pruefe Umgebungsvariablen\n3. Pruefe Konfigurationsdateien',
        'git': '1. Pruefe git status\n2. Loese Konflikte falls vorhanden\n3. Pruefe remote URL',
        'docker': '1. Pruefe Docker-Status (docker ps)\n2. Pruefe Logs (docker logs <container>)\n3. Pruefe Dockerfile',
        'other': '1. Analysiere den Fehler genauer\n2. Suche online nach der Fehlermeldung\n3. Pruefe die Dokumentation'
    }

    return fallbacks.get(kategorie, fallbacks['other'])


def _get_fallback_auftrag(fehler_text: str, kategorie: str, severity: str) -> str:
    """
    Generiert Fallback-Auftrag mit erweiterten Informationen.

    Args:
        fehler_text: Fehlertext
        kategorie: Erkannte Kategorie
        severity: Erkannte Severity

    Returns:
        str: Formatierter Fallback-Auftrag
    """
    severity_icon = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }.get(severity, '🟡')

    fix_command = detect_fix_command(fehler_text, kategorie)
    fix_section = f"""
📋 MOEGLICHER FIX
```bash
{fix_command}
```
""" if fix_command else ""

    return f"""═══════════════════════════════════════════════════════════════
🔧 FEHLER-ANALYSE (Fallback)
═══════════════════════════════════════════════════════════════

📋 KATEGORIE
{kategorie}

{severity_icon} SEVERITY
{severity.upper()}

📋 EMPFOHLENE SCHRITTE
{_get_fallback_loesung(fehler_text)}
{fix_section}
📋 FEHLER-TEXT
{fehler_text[:500]}{'...' if len(fehler_text) > 500 else ''}

⚠️ Hinweis: KI-Analyse war nicht moeglich. Bitte manuell pruefen.

═══════════════════════════════════════════════════════════════"""
