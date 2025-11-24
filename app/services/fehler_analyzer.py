"""
NEXUS OVERLORD v2.0 - Fehler Analyzer (Auftrag 4.3)
Analysiert Fehler mit Gemini 3 Pro und erstellt Lösungs-Aufträge mit Opus 4.5
"""

import json
import re
from app.services.openrouter import get_client
from app.services.database import search_fehler, save_fehler, increment_fehler_count


def analyze_fehler(fehler_text: str, projekt_name: str = "NEXUS OVERLORD") -> dict:
    """
    Analysiert einen Fehler und gibt Lösung zurück.

    Workflow:
    1. Prüfe Fehler-Datenbank nach bekanntem Muster
    2. Falls bekannt → Lösung aus DB
    3. Falls neu → Gemini 3 Pro analysiert, Opus 4.5 erstellt Lösungs-Auftrag

    Args:
        fehler_text: Fehler-Text vom User
        projekt_name: Name des Projekts

    Returns:
        dict: {
            'bekannt': bool,
            'kategorie': str,
            'ursache': str,
            'loesung': str,
            'auftrag': str,
            'fehler_id': int
        }
    """

    # 1. Prüfe Fehler-Datenbank
    bekannter_fehler = search_fehler(fehler_text)

    if bekannter_fehler:
        # Bekannter Fehler gefunden!
        increment_fehler_count(bekannter_fehler['id'])

        return {
            'bekannt': True,
            'kategorie': bekannter_fehler.get('kategorie', 'unknown'),
            'ursache': f"Bekannter Fehler (#{bekannter_fehler['id']})",
            'loesung': bekannter_fehler['loesung'],
            'auftrag': _create_quick_auftrag(bekannter_fehler),
            'fehler_id': bekannter_fehler['id'],
            'erfolgsrate': bekannter_fehler.get('erfolgsrate', 0),
            'anzahl': bekannter_fehler.get('anzahl', 1)
        }

    # 2. Neuer Fehler → KI-Analyse
    try:
        # Gemini 3 Pro analysiert den Fehler
        analyse = _analyze_with_gemini(fehler_text)

        # Opus 4.5 erstellt Lösungs-Auftrag
        auftrag = _create_auftrag_with_opus(fehler_text, analyse, projekt_name)

        # Fehler in Datenbank speichern
        fehler_id = save_fehler(
            muster=analyse.get('muster', fehler_text[:100]),
            kategorie=analyse.get('kategorie', 'unknown'),
            loesung=analyse.get('loesung', 'Keine Lösung gefunden')
        )

        return {
            'bekannt': False,
            'kategorie': analyse.get('kategorie', 'unknown'),
            'ursache': analyse.get('ursache', 'Unbekannt'),
            'loesung': analyse.get('loesung', 'Keine Lösung gefunden'),
            'auftrag': auftrag,
            'fehler_id': fehler_id,
            'erfolgsrate': 100,
            'anzahl': 1
        }

    except Exception as e:
        # Fallback bei API-Fehler
        return {
            'bekannt': False,
            'kategorie': 'error',
            'ursache': f'Analyse fehlgeschlagen: {str(e)}',
            'loesung': _get_fallback_loesung(fehler_text),
            'auftrag': _get_fallback_auftrag(fehler_text),
            'fehler_id': None,
            'erfolgsrate': 0,
            'anzahl': 0
        }


def _analyze_with_gemini(fehler_text: str) -> dict:
    """
    Analysiert Fehler mit Gemini 3 Pro

    Args:
        fehler_text: Fehler-Text

    Returns:
        dict: Analyse-Ergebnis
    """
    client = get_client()

    prompt = f"""Du bist ein Fehler-Analyst für Software-Entwicklung.

Analysiere diesen Fehler und gib zurück:
1. Kategorie (python, npm, permission, database, network, syntax, config, etc.)
2. Ursache (kurz und präzise)
3. Lösung (Schritt für Schritt)
4. Muster (für zukünftige Erkennung, z.B. "ModuleNotFoundError", "EACCES", etc.)

Fehler-Text:
{fehler_text}

Antworte NUR mit einem JSON-Objekt (keine Erklärungen):
{{"kategorie": "...", "ursache": "...", "loesung": "...", "muster": "..."}}"""

    messages = [{"role": "user", "content": prompt}]

    response = client.call_gemini(messages, temperature=0.3, timeout=30)

    # JSON aus Antwort extrahieren
    try:
        # Versuche JSON zu parsen
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except json.JSONDecodeError:
        # Fallback: Manuell parsen
        return {
            'kategorie': _extract_kategorie(fehler_text),
            'ursache': 'Konnte nicht automatisch analysiert werden',
            'loesung': response,
            'muster': fehler_text[:50]
        }


def _create_auftrag_with_opus(fehler_text: str, analyse: dict, projekt_name: str) -> str:
    """
    Erstellt Lösungs-Auftrag mit Opus 4.5

    Args:
        fehler_text: Original Fehler-Text
        analyse: Analyse von Gemini
        projekt_name: Projektname

    Returns:
        str: Formatierter Lösungs-Auftrag
    """
    client = get_client()

    prompt = f"""Erstelle einen kurzen, präzisen Lösungs-Auftrag für Claude Code.

FEHLER:
{fehler_text}

ANALYSE:
- Kategorie: {analyse.get('kategorie', 'unknown')}
- Ursache: {analyse.get('ursache', 'Unbekannt')}
- Lösung: {analyse.get('loesung', 'Keine')}

Erstelle einen Auftrag im folgenden Format:

═══════════════════════════════════════════════════════════════
🔧 FEHLER-LÖSUNG
═══════════════════════════════════════════════════════════════

📋 PROBLEM
[Kurze Beschreibung des Problems]

📋 LÖSUNG
[Nummerierte Schritte zur Lösung]

📋 BEFEHLE
```bash
[Konkrete Befehle zum Ausführen]
```

═══════════════════════════════════════════════════════════════

Halte es kurz und präzise. Nur das Nötigste."""

    messages = [{"role": "user", "content": prompt}]

    response = client.call_sonnet(messages, temperature=0.3, timeout=30)

    return response


def _create_quick_auftrag(fehler: dict) -> str:
    """
    Erstellt schnellen Auftrag aus bekanntem Fehler

    Args:
        fehler: Fehler aus Datenbank

    Returns:
        str: Formatierter Auftrag
    """
    return f"""═══════════════════════════════════════════════════════════════
🔧 BEKANNTE LÖSUNG (#{fehler['id']})
═══════════════════════════════════════════════════════════════

📋 KATEGORIE
{fehler.get('kategorie', 'Unbekannt')}

📋 LÖSUNG
{fehler['loesung']}

📊 STATISTIK
- Erfolgsrate: {fehler.get('erfolgsrate', 0):.0f}%
- Bereits {fehler.get('anzahl', 1)}x aufgetreten

═══════════════════════════════════════════════════════════════"""


def _extract_kategorie(fehler_text: str) -> str:
    """
    Extrahiert Kategorie aus Fehler-Text (Fallback)
    """
    text_lower = fehler_text.lower()

    if any(x in text_lower for x in ['python', 'traceback', 'importerror', 'modulenotfound']):
        return 'python'
    elif any(x in text_lower for x in ['npm', 'node', 'package.json', 'enoent']):
        return 'npm'
    elif any(x in text_lower for x in ['permission', 'eacces', 'denied', 'sudo']):
        return 'permission'
    elif any(x in text_lower for x in ['sql', 'database', 'sqlite', 'mysql']):
        return 'database'
    elif any(x in text_lower for x in ['network', 'connection', 'timeout', 'refused']):
        return 'network'
    elif any(x in text_lower for x in ['syntax', 'unexpected', 'parse']):
        return 'syntax'
    elif any(x in text_lower for x in ['config', 'env', 'environment']):
        return 'config'
    elif any(x in text_lower for x in ['git', 'commit', 'merge', 'push']):
        return 'git'
    else:
        return 'unknown'


def _get_fallback_loesung(fehler_text: str) -> str:
    """
    Generiert Fallback-Lösung basierend auf Fehler-Kategorie
    """
    kategorie = _extract_kategorie(fehler_text)

    fallbacks = {
        'python': '1. Prüfe die Python-Version (python --version)\n2. Installiere fehlende Module (pip install <modul>)\n3. Prüfe Imports und Pfade',
        'npm': '1. Lösche node_modules und package-lock.json\n2. Führe npm install aus\n3. Prüfe Node.js Version (node --version)',
        'permission': '1. Prüfe Datei-Berechtigungen (ls -la)\n2. Nutze sudo falls nötig\n3. Prüfe Benutzer und Gruppe',
        'database': '1. Prüfe Datenbank-Verbindung\n2. Prüfe SQL-Syntax\n3. Prüfe ob Tabellen existieren',
        'network': '1. Prüfe Netzwerk-Verbindung\n2. Prüfe Firewall-Einstellungen\n3. Prüfe ob Service läuft',
        'syntax': '1. Prüfe Syntax des Codes\n2. Suche nach fehlenden Klammern/Anführungszeichen\n3. Prüfe Einrückung (bei Python)',
        'config': '1. Prüfe .env Datei\n2. Prüfe Umgebungsvariablen\n3. Prüfe Konfigurationsdateien',
        'git': '1. Prüfe git status\n2. Löse Konflikte falls vorhanden\n3. Prüfe remote URL'
    }

    return fallbacks.get(kategorie, '1. Analysiere den Fehler genauer\n2. Suche online nach der Fehlermeldung\n3. Prüfe die Dokumentation')


def _get_fallback_auftrag(fehler_text: str) -> str:
    """
    Generiert Fallback-Auftrag
    """
    kategorie = _extract_kategorie(fehler_text)

    return f"""═══════════════════════════════════════════════════════════════
🔧 FEHLER-ANALYSE (Fallback)
═══════════════════════════════════════════════════════════════

📋 KATEGORIE
{kategorie}

📋 EMPFOHLENE SCHRITTE
{_get_fallback_loesung(fehler_text)}

📋 FEHLER-TEXT
{fehler_text[:500]}{'...' if len(fehler_text) > 500 else ''}

⚠️ Hinweis: KI-Analyse war nicht möglich. Bitte manuell prüfen.

═══════════════════════════════════════════════════════════════"""
