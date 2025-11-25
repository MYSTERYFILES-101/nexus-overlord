"""
NEXUS OVERLORD v2.0 - Aufträge Generator

Opus 4.5 erstellt konkrete Aufträge pro Phase mit Regelwerk.

Jeder Auftrag enthält:
    - Phase-Nummer und Auftrags-Nummer (z.B. 1.1, 1.2, 2.1)
    - Name und Beschreibung
    - Konkrete Schritte
    - Betroffene Dateien
    - Technische Details
    - Erfolgs-Kriterien
    - Regelwerk (Commit-Message, Übergabe-Pfad, Pflichten)
"""

import json
import logging
import re
from typing import Any

from app.services.openrouter import get_client
from app.utils.json_extractor import extract_json

# Logger konfigurieren
logger = logging.getLogger(__name__)


# Prompt-Template für Auftrags-Generierung
AUFTRAEGE_PROMPT = """Du bist ein erfahrener Software-Entwickler und Projekt-Manager. Erstelle für jede Phase konkrete Aufträge, die Claude Code als KI-Entwickler ausführen kann.

KONTEXT:
Du planst Aufträge für ein Software-Projekt. Claude Code wird diese Aufträge nacheinander abarbeiten.

ENTERPRISE-PLAN:
{enterprise_plan}

PHASEN:
{phasen_json}

AUFGABE:
Für jede Phase erstelle 2-5 konkrete, ausführbare Aufträge mit:

1. **Auftragsnummer**: Format "X.Y" (Phase.Auftrag, z.B. "1.1", "1.2", "2.1")
2. **Name**: Kurzer, prägnanter Name (max 4 Wörter)
3. **Beschreibung**: Was soll gemacht werden (1-2 Sätze)
4. **Schritte**: 3-6 konkrete Schritte zum Ausführen
5. **Dateien**: Welche Dateien werden erstellt/geändert
6. **Technische Details**: Frameworks, Libraries, Patterns
7. **Erfolgs-Kriterien**: Wie wird Erfolg gemessen
8. **Regelwerk**: Anweisungen für Claude Code

WICHTIG:
- Aufträge müssen in logischer Reihenfolge sein
- Jeder Auftrag muss eigenständig ausführbar sein
- Erste Aufträge einer Phase: Setup/Grundlagen
- Letzte Aufträge einer Phase: Tests/Integration
- Realistische Schritte (nicht zu abstrakt)
- Konkrete Dateinamen und Pfade

AUSGABE als JSON (NUR JSON, kein anderer Text):
{{
    "auftraege": [
        {{
            "phase_nummer": 1,
            "auftrag_nummer": "1.1",
            "name": "Setup & Dependencies",
            "beschreibung": "Grundlegende Projektstruktur und Dependencies installieren",
            "schritte": [
                "requirements.txt erstellen mit benötigten Libraries",
                "Virtuelle Environment aktivieren",
                "Dependencies installieren (pip install -r requirements.txt)",
                "Basis-Ordnerstruktur erstellen"
            ],
            "dateien": [
                {{"pfad": "requirements.txt", "aktion": "neu"}},
                {{"pfad": "README.md", "aktion": "neu"}}
            ],
            "technische_details": [
                "Python 3.11+",
                "Flask Framework",
                "SQLite Database"
            ],
            "erfolgs_kriterien": [
                "requirements.txt existiert",
                "Alle Dependencies installiert",
                "Ordnerstruktur angelegt",
                "README mit Projekt-Übersicht"
            ],
            "regelwerk": {{
                "commit_message": "[1.1] Setup & Dependencies",
                "uebergabe_pfad": "/projekt/uebergaben/YYYY-MM-DD_HH-MM_auftrag-1-1.md",
                "pflichten": [
                    "GitHub Commit erstellen",
                    "GitHub Push durchführen",
                    "Übergabe-Datei schreiben mit Details",
                    "Status melden an User"
                ]
            }}
        }},
        {{
            "phase_nummer": 1,
            "auftrag_nummer": "1.2",
            "name": "Database Schema",
            "beschreibung": "SQLite Datenbank-Schema erstellen mit allen benötigten Tabellen",
            "schritte": [
                "SQL-Schema-Datei erstellen",
                "Tabellen mit Feldern definieren",
                "Indizes und Constraints festlegen",
                "Init-Script für DB-Setup"
            ],
            "dateien": [
                {{"pfad": "database/schema.sql", "aktion": "neu"}},
                {{"pfad": "database/init.py", "aktion": "neu"}}
            ],
            "technische_details": [
                "SQLite3",
                "Foreign Keys aktivieren",
                "Timestamps (created_at, updated_at)"
            ],
            "erfolgs_kriterien": [
                "Schema-Datei kompiliert ohne Fehler",
                "Alle Tabellen erstellt",
                "Indizes angelegt",
                "Init-Script läuft durch"
            ],
            "regelwerk": {{
                "commit_message": "[1.2] Database Schema",
                "uebergabe_pfad": "/projekt/uebergaben/YYYY-MM-DD_HH-MM_auftrag-1-2.md",
                "pflichten": [
                    "GitHub Commit erstellen",
                    "GitHub Push durchführen",
                    "Übergabe-Datei schreiben",
                    "Status melden"
                ]
            }}
        }}
    ],
    "gesamt_auftraege": 12,
    "geschaetzte_dauer": "10-15 Stunden",
    "hinweise": "Zusätzliche Hinweise zur Umsetzung"
}}

HINWEIS: Erstelle für JEDE Phase mindestens 2 und maximal 5 Aufträge. Passe die Anzahl an die Komplexität der Phase an.
"""


def generate_auftraege(phasen_data: dict[str, Any], enterprise_plan: str) -> dict[str, Any]:
    """
    Generiert Aufträge mit Opus 4.5.

    Args:
        phasen_data: Phasen-Struktur aus dem Phasen-Generator
        enterprise_plan: Original Enterprise-Plan

    Returns:
        dict: Auftrags-Struktur mit:
            - auftraege: Liste der Aufträge
            - gesamt_auftraege: Anzahl der Aufträge
            - geschaetzte_dauer: Geschätzte Gesamtdauer
            - hinweise: Zusätzliche Hinweise

    Raises:
        ValueError: Bei ungültiger JSON-Antwort oder Validierungsfehler
        Exception: Bei API-Fehler
    """
    logger.info("Starte Auftrags-Generierung")

    client = get_client()

    # Phasen als JSON formatieren
    phasen_json = json.dumps(phasen_data, indent=2, ensure_ascii=False)

    # Prompt mit Daten füllen
    prompt = AUFTRAEGE_PROMPT.format(
        enterprise_plan=enterprise_plan,
        phasen_json=phasen_json
    )

    # Opus 4.5 aufrufen
    logger.debug("Rufe Opus 4.5 auf")
    response = client.call_sonnet([
        {"role": "user", "content": prompt}
    ], temperature=0.7, timeout=120)

    logger.debug(f"Opus-Antwort erhalten ({len(response)} Zeichen)")

    # JSON aus Response extrahieren
    parsed = extract_json(response)

    if not parsed or "auftraege" not in parsed:
        logger.error("Keine gültigen Aufträge in der Antwort gefunden")
        raise ValueError(
            "Konnte keine gültigen Aufträge aus der KI-Antwort extrahieren.\n"
            f"Antwort (erste 500 Zeichen):\n{response[:500]}"
        )

    # Validierung
    validate_auftraege(parsed, phasen_data)

    logger.info(f"Auftrags-Generierung erfolgreich: {len(parsed['auftraege'])} Aufträge")
    return parsed


def validate_auftraege(data: dict[str, Any], phasen_data: dict[str, Any]) -> None:
    """
    Validiert die Auftrags-Struktur.

    Args:
        data: Zu validierende Auftrags-Daten
        phasen_data: Original Phasen-Daten zur Validierung

    Raises:
        ValueError: Bei ungültiger Struktur
    """
    # Required keys
    if "auftraege" not in data:
        raise ValueError("Fehlendes Feld: 'auftraege'")

    auftraege = data["auftraege"]

    if not isinstance(auftraege, list):
        raise ValueError("'auftraege' muss eine Liste sein")

    if len(auftraege) == 0:
        raise ValueError("Mindestens 1 Auftrag erforderlich")

    # Anzahl Phasen aus phasen_data
    anzahl_phasen = len(phasen_data.get("phasen", []))

    # Validiere jeden Auftrag
    for i, auftrag in enumerate(auftraege):
        # Required fields - mit Standardwerten falls fehlend
        required = ["phase_nummer", "auftrag_nummer", "name", "beschreibung",
                   "schritte", "dateien", "technische_details",
                   "erfolgs_kriterien", "regelwerk"]

        for field in required:
            if field not in auftrag:
                # Füge Standardwerte hinzu statt Fehler zu werfen
                if field == "schritte":
                    auftrag["schritte"] = []
                    logger.warning(f"Auftrag {i+1}: 'schritte' fehlt, setze auf []")
                elif field == "dateien":
                    auftrag["dateien"] = []
                    logger.warning(f"Auftrag {i+1}: 'dateien' fehlt, setze auf []")
                elif field == "technische_details":
                    auftrag["technische_details"] = []
                    logger.warning(f"Auftrag {i+1}: 'technische_details' fehlt, setze auf []")
                elif field == "erfolgs_kriterien":
                    auftrag["erfolgs_kriterien"] = []
                    logger.warning(f"Auftrag {i+1}: 'erfolgs_kriterien' fehlt, setze auf []")
                elif field == "regelwerk":
                    auftrag["regelwerk"] = {
                        "commit_message": f"[{auftrag.get('auftrag_nummer', i+1)}] {auftrag.get('name', 'Auftrag')}",
                        "uebergabe_pfad": "/projekt/uebergaben/",
                        "pflichten": ["Status melden"]
                    }
                    logger.warning(f"Auftrag {i+1}: 'regelwerk' fehlt, setze Standard")
                else:
                    raise ValueError(f"Auftrag {i+1} fehlt kritisches Feld: '{field}'")

        # Phase-Nummer muss valid sein
        if not (1 <= auftrag["phase_nummer"] <= max(anzahl_phasen, 10)):
            logger.warning(f"Auftrag {i+1}: Phase-Nummer {auftrag['phase_nummer']} korrigiert")
            auftrag["phase_nummer"] = min(auftrag["phase_nummer"], anzahl_phasen)

        # Auftragsnummer-Format prüfen (X.Y)
        if not re.match(r'^\d+\.\d+$', str(auftrag["auftrag_nummer"])):
            # Korrigiere das Format
            phase_nr = auftrag["phase_nummer"]
            auftrag_nr = i + 1
            auftrag["auftrag_nummer"] = f"{phase_nr}.{auftrag_nr}"
            logger.warning(f"Auftrag {i+1}: Format korrigiert zu '{auftrag['auftrag_nummer']}'")

        # Listen validieren
        if not isinstance(auftrag.get("schritte", []), list):
            auftrag["schritte"] = []

        if not isinstance(auftrag.get("dateien", []), list):
            auftrag["dateien"] = []

        # Regelwerk validieren
        if not isinstance(auftrag.get("regelwerk", {}), dict):
            auftrag["regelwerk"] = {
                "commit_message": f"[{auftrag['auftrag_nummer']}] {auftrag['name']}",
                "uebergabe_pfad": "/projekt/uebergaben/",
                "pflichten": ["Status melden"]
            }

    logger.debug("Auftrags-Validierung erfolgreich")


def format_auftraege_for_display(data: dict[str, Any]) -> str:
    """
    Formatiert Aufträge für die Anzeige (Markdown).

    Args:
        data: Auftrags-Daten

    Returns:
        str: Markdown-formatierte Aufträge
    """
    lines = []
    lines.append(f"# Auftrags-Übersicht ({data.get('gesamt_auftraege', len(data['auftraege']))} Aufträge)\n")
    lines.append(f"**Geschätzte Gesamtdauer:** {data.get('geschaetzte_dauer', 'N/A')}\n")

    if "hinweise" in data:
        lines.append(f"**Hinweise:** {data['hinweise']}\n")

    lines.append("---\n")

    # Gruppiere Aufträge nach Phase
    auftraege_by_phase: dict[int, list] = {}
    for auftrag in data["auftraege"]:
        phase_nr = auftrag["phase_nummer"]
        if phase_nr not in auftraege_by_phase:
            auftraege_by_phase[phase_nr] = []
        auftraege_by_phase[phase_nr].append(auftrag)

    # Sortiert ausgeben
    for phase_nr in sorted(auftraege_by_phase.keys()):
        lines.append(f"## Phase {phase_nr}\n")

        for auftrag in auftraege_by_phase[phase_nr]:
            lines.append(f"### Auftrag {auftrag['auftrag_nummer']}: {auftrag['name']}\n")
            lines.append(f"**Beschreibung:** {auftrag['beschreibung']}\n")

            if auftrag.get("schritte"):
                lines.append("**Schritte:**\n")
                for schritt in auftrag["schritte"]:
                    lines.append(f"- {schritt}\n")

            if auftrag.get("dateien"):
                lines.append("**Dateien:**\n")
                for datei in auftrag["dateien"]:
                    if isinstance(datei, dict):
                        lines.append(f"- `{datei.get('pfad', '?')}` ({datei.get('aktion', '?')})\n")
                    else:
                        lines.append(f"- `{datei}`\n")

            if auftrag.get("erfolgs_kriterien"):
                lines.append("**Erfolgs-Kriterien:**\n")
                for kriterium in auftrag["erfolgs_kriterien"]:
                    lines.append(f"- {kriterium}\n")

            lines.append("\n")

    return "\n".join(lines)
