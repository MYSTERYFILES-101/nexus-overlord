"""
NEXUS OVERLORD v2.0 - Phasen Generator

Gemini 3 Pro analysiert Enterprise-Plan und teilt ihn in 5-8 logische Phasen ein.

Jede Phase enthaelt:
    - Nummer (sequentiell, 1-8)
    - Name (kurz und praegnant)
    - Beschreibung (detailliert)
    - Abhaengigkeiten (Referenzen auf vorherige Phasen)
    - Prioritaet (hoch/mittel/niedrig)
    - Geschaetzte Dauer
"""

import logging
from typing import Any

from app.services.openrouter import get_client
from app.utils.json_extractor import extract_json

# Logger konfigurieren
logger = logging.getLogger(__name__)


# Prompt-Template fuer Phasen-Generierung
PHASEN_PROMPT = """Du bist ein erfahrener Projekt-Stratege. Analysiere den folgenden Enterprise-Plan und teile ihn in 5-8 logische Phasen ein.

ENTERPRISE-PLAN:
{enterprise_plan}

AUFGABE:
1. Identifiziere die Hauptkomponenten des Projekts
2. Gruppiere zusammengehoerige Aufgaben
3. Erkenne Abhaengigkeiten (was muss zuerst fertig sein?)
4. Setze Prioritaeten (hoch/mittel/niedrig)
5. Schaetze realistische Dauer pro Phase

WICHTIG:
- Erstelle 5-8 Phasen (nicht mehr, nicht weniger)
- Jede Phase sollte logisch abgeschlossen sein
- Abhaengigkeiten sind Phase-Nummern (z.B. [1, 2] = haengt von Phase 1 und 2 ab)
- Prioritaet: "hoch" fuer kritische, "mittel" fuer wichtige, "niedrig" fuer optionale Phasen

AUSGABE als JSON (NUR JSON, kein anderer Text):
{{
    "phasen": [
        {{
            "nummer": 1,
            "name": "Kurzer praegnanter Name",
            "beschreibung": "Detaillierte Beschreibung was in dieser Phase gemacht wird",
            "abhaengigkeiten": [],
            "prioritaet": "hoch",
            "geschaetzte_dauer": "2-3 Stunden"
        }},
        {{
            "nummer": 2,
            "name": "Naechste Phase",
            "beschreibung": "Was wird hier gemacht",
            "abhaengigkeiten": [1],
            "prioritaet": "mittel",
            "geschaetzte_dauer": "3-4 Stunden"
        }}
    ],
    "gesamt_phasen": 6,
    "gesamt_dauer": "15-20 Stunden",
    "hinweise": "Zusaetzliche strategische Empfehlungen fuer die Umsetzung"
}}
"""


def generate_phasen(enterprise_plan: str) -> dict[str, Any]:
    """
    Generiert Phasen-Einteilung mit Gemini 3 Pro.

    Args:
        enterprise_plan: Der zu analysierende Enterprise-Plan

    Returns:
        dict: Phasen-Struktur mit:
            - phasen: Liste der Phasen
            - gesamt_phasen: Anzahl der Phasen
            - gesamt_dauer: Geschaetzte Gesamtdauer
            - hinweise: Strategische Empfehlungen

    Raises:
        ValueError: Bei ungueltiger JSON-Antwort oder Validierungsfehler
        Exception: Bei API-Fehler
    """
    logger.info("Starte Phasen-Generierung")

    client = get_client()

    # Prompt mit Enterprise-Plan fuellen
    prompt = PHASEN_PROMPT.format(enterprise_plan=enterprise_plan)

    # Gemini 3 Pro aufrufen
    logger.debug("Rufe Gemini 3 Pro auf")
    response = client.call_gemini([
        {"role": "user", "content": prompt}
    ], temperature=0.7, timeout=90)

    logger.debug(f"Gemini-Antwort erhalten ({len(response)} Zeichen)")

    # JSON aus Response extrahieren
    parsed = extract_json(response)

    if not parsed or "phasen" not in parsed:
        logger.error("Keine gueltigen Phasen in der Antwort gefunden")
        raise ValueError(
            "Konnte keine gueltigen Phasen aus der KI-Antwort extrahieren.\n"
            f"Antwort (erste 500 Zeichen):\n{response[:500]}"
        )

    # Validierung
    validate_phasen(parsed)

    logger.info(f"Phasen-Generierung erfolgreich: {len(parsed['phasen'])} Phasen")
    return parsed


def validate_phasen(data: dict[str, Any]) -> None:
    """
    Validiert die Phasen-Struktur.

    Args:
        data: Zu validierende Phasen-Daten

    Raises:
        ValueError: Bei ungueltiger Struktur
    """
    # Required keys
    if "phasen" not in data:
        raise ValueError("Fehlendes Feld: 'phasen'")

    phasen = data["phasen"]

    if not isinstance(phasen, list):
        raise ValueError("'phasen' muss eine Liste sein")

    if len(phasen) < 5 or len(phasen) > 8:
        logger.warning(f"Ungewoehnliche Phasen-Anzahl: {len(phasen)} (erwartet 5-8)")
        # Kein Fehler werfen, nur warnen - KI kann manchmal abweichen

    # Validiere jede Phase
    for i, phase in enumerate(phasen):
        # Required fields
        required = ["nummer", "name", "beschreibung", "abhaengigkeiten", "prioritaet"]
        for field in required:
            if field not in phase:
                # Fuege Standardwert hinzu statt Fehler zu werfen
                if field == "abhaengigkeiten":
                    phase["abhaengigkeiten"] = []
                elif field == "prioritaet":
                    phase["prioritaet"] = "mittel"
                elif field == "geschaetzte_dauer":
                    phase["geschaetzte_dauer"] = "N/A"
                else:
                    raise ValueError(f"Phase {i+1} fehlt Feld: '{field}'")

        # Korrigiere Nummer falls noetig
        if phase["nummer"] != i + 1:
            logger.warning(f"Phase-Nummer korrigiert: {phase['nummer']} -> {i+1}")
            phase["nummer"] = i + 1

        # Prioritaet validieren/korrigieren
        if phase["prioritaet"] not in ["hoch", "mittel", "niedrig"]:
            logger.warning(f"Ungueltige Prioritaet in Phase {i+1}: {phase['prioritaet']} -> 'mittel'")
            phase["prioritaet"] = "mittel"

        # Abhaengigkeiten muessen Liste sein
        if not isinstance(phase["abhaengigkeiten"], list):
            logger.warning(f"Abhaengigkeiten in Phase {i+1} korrigiert zu leerer Liste")
            phase["abhaengigkeiten"] = []

    logger.debug("Phasen-Validierung erfolgreich")


def format_phasen_for_display(data: dict[str, Any]) -> str:
    """
    Formatiert Phasen-Daten fuer die Anzeige (Markdown).

    Args:
        data: Phasen-Daten

    Returns:
        str: Markdown-formatierte Phasen
    """
    lines = []
    lines.append(f"# Phasen-Uebersicht ({data.get('gesamt_phasen', len(data['phasen']))} Phasen)\n")
    lines.append(f"**Geschaetzte Gesamtdauer:** {data.get('gesamt_dauer', 'N/A')}\n")

    if "hinweise" in data:
        lines.append(f"**Strategische Hinweise:** {data['hinweise']}\n")

    lines.append("---\n")

    for phase in data["phasen"]:
        lines.append(f"## Phase {phase['nummer']}: {phase['name']}\n")
        lines.append(f"**Beschreibung:** {phase['beschreibung']}\n")
        lines.append(f"**Prioritaet:** {phase['prioritaet'].upper()}\n")
        lines.append(f"**Dauer:** {phase.get('geschaetzte_dauer', 'N/A')}\n")

        if phase["abhaengigkeiten"]:
            deps = ", ".join([f"Phase {d}" for d in phase["abhaengigkeiten"]])
            lines.append(f"**Abhaengigkeiten:** {deps}\n")
        else:
            lines.append("**Abhaengigkeiten:** Keine\n")

        lines.append("\n")

    return "\n".join(lines)
