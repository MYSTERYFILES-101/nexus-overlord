"""
NEXUS OVERLORD v2.0 - Qualitätsprüfung

Gemini 3 Pro prüft generierte Aufträge auf Qualität.

Prüfungskategorien:
    - Vollständigkeit: Deckt der Plan alles ab?
    - Reihenfolge: Sind Abhängigkeiten korrekt?
    - Klarheit: Sind Schritte verständlich?
    - Dateien: Sind Pfade und Aktionen korrekt?
    - Regelwerk: Ist das Format konsistent?
    - Lücken: Fehlt etwas Wichtiges?
    - Duplikate: Gibt es Überschneidungen?
"""

import json
import logging
from typing import Any

from app.services.openrouter import get_client
from app.utils.json_extractor import extract_json

# Logger konfigurieren
logger = logging.getLogger(__name__)


# Prompt-Template für Qualitätsprüfung
QUALITAET_PROMPT = """Du bist ein erfahrener QA-Manager und Software-Architekt. Prüfe die folgenden Aufträge auf Vollständigkeit und Qualität.

ENTERPRISE-PLAN (Original):
{enterprise_plan}

PHASEN-STRUKTUR:
{phasen_json}

GENERIERTE AUFTRÄGE:
{auftraege_json}

AUFGABE:
Prüfe die Aufträge kritisch auf folgende Kategorien:

1. **Vollständigkeit** (1-10)
   - Decken die Aufträge den gesamten Enterprise-Plan ab?
   - Sind alle Features/Komponenten berücksichtigt?
   - Fehlt etwas Wichtiges?

2. **Reihenfolge** (1-10)
   - Sind Abhängigkeiten korrekt berücksichtigt?
   - Macht die Sequenz Sinn?
   - Kann man so tatsächlich arbeiten?

3. **Klarheit** (1-10)
   - Sind die Schritte verständlich?
   - Kann ein Entwickler die Aufträge ausführen?
   - Sind technische Details ausreichend?

4. **Dateien** (1-10)
   - Sind alle benötigten Dateien genannt?
   - Sind die Pfade korrekt?
   - Sind die Aktionen (neu/ändern) richtig?

5. **Regelwerk** (1-10)
   - Ist das Übergabe-Format konsistent?
   - Sind Commit-Messages einheitlich?
   - Sind die Pflichten klar definiert?

6. **Lücken** (1-10)
   - Fehlen wichtige Aspekte?
   - Sind Tests/Dokumentation berücksichtigt?
   - Gibt es unklare Bereiche?

7. **Duplikate** (1-10)
   - Gibt es unnötige Überschneidungen?
   - Wiederholen sich Aufgaben?
   - Ist alles einzigartig?

BEWERTUNGS-SKALA:
- 1-4: Schlecht (kritische Probleme)
- 5-7: Mittel (Verbesserungen nötig)
- 8-10: Gut (akzeptabel)

AUSGABE als JSON (NUR JSON, kein anderer Text):
{{
    "gesamt_bewertung": 8,
    "gesamt_kommentar": "Die Aufträge sind gut strukturiert und decken den Enterprise-Plan weitgehend ab. Einige Details könnten präziser sein.",
    "kategorien": [
        {{
            "name": "Vollständigkeit",
            "bewertung": 9,
            "status": "gut",
            "kommentar": "Alle Aspekte des Plans sind abgedeckt. Keine wichtigen Features fehlen."
        }},
        {{
            "name": "Reihenfolge",
            "bewertung": 8,
            "status": "gut",
            "kommentar": "Abhängigkeiten sind korrekt. Setup kommt zuerst, Tests am Ende."
        }},
        {{
            "name": "Klarheit",
            "bewertung": 7,
            "status": "mittel",
            "kommentar": "Die meisten Schritte sind klar. Einige könnten detaillierter sein."
        }},
        {{
            "name": "Dateien",
            "bewertung": 8,
            "status": "gut",
            "kommentar": "Dateipfade sind konsistent und realistisch."
        }},
        {{
            "name": "Regelwerk",
            "bewertung": 9,
            "status": "gut",
            "kommentar": "Übergabe-Format ist einheitlich über alle Aufträge."
        }},
        {{
            "name": "Lücken",
            "bewertung": 8,
            "status": "gut",
            "kommentar": "Keine kritischen Lücken. Tests und Docs sind erwähnt."
        }},
        {{
            "name": "Duplikate",
            "bewertung": 9,
            "status": "gut",
            "kommentar": "Keine unnötigen Wiederholungen gefunden."
        }}
    ],
    "verbesserungen": [
        {{
            "auftrag": "2.3",
            "typ": "empfehlung",
            "text": "Schritt 2 könnte konkreter sein: Welche Felder genau im Formular?"
        }},
        {{
            "auftrag": "3.1",
            "typ": "empfehlung",
            "text": "Technische Details: Welche Test-Library wird verwendet?"
        }}
    ],
    "warnungen": [],
    "fazit": "Die Aufträge sind gut vorbereitet und bereit für die Umsetzung. Kleinere Detailverbesserungen sind optional."
}}

WICHTIG:
- Sei kritisch aber konstruktiv
- Bei Bewertung < 7: Gib konkrete Verbesserungen an
- Bei kritischen Problemen: Füge Warnungen hinzu
- status MUSS "gut", "mittel" oder "schlecht" sein
- Gesamtbewertung ist der Durchschnitt der Kategorien (gerundet)
"""


def pruefen_auftraege(
    auftraege_data: dict[str, Any],
    phasen_data: dict[str, Any],
    enterprise_plan: str
) -> dict[str, Any]:
    """
    Prüft Aufträge mit Gemini 3 Pro auf Qualität.

    Args:
        auftraege_data: Auftrags-Struktur aus dem Aufträge-Generator
        phasen_data: Phasen-Struktur aus dem Phasen-Generator
        enterprise_plan: Original Enterprise-Plan

    Returns:
        dict: Qualitäts-Bewertung mit:
            - gesamt_bewertung: Gesamtnote (1-10)
            - gesamt_kommentar: Zusammenfassung
            - kategorien: Liste der 7 Kategorien mit Bewertungen
            - verbesserungen: Konkrete Verbesserungsvorschläge
            - warnungen: Kritische Warnungen
            - fazit: Abschließendes Fazit

    Raises:
        ValueError: Bei ungültiger JSON-Antwort oder Validierungsfehler
        Exception: Bei API-Fehler
    """
    logger.info("Starte Qualitätsprüfung")

    client = get_client()

    # Daten als JSON formatieren
    phasen_json = json.dumps(phasen_data, indent=2, ensure_ascii=False)
    auftraege_json = json.dumps(auftraege_data, indent=2, ensure_ascii=False)

    # Prompt mit Daten füllen
    prompt = QUALITAET_PROMPT.format(
        enterprise_plan=enterprise_plan,
        phasen_json=phasen_json,
        auftraege_json=auftraege_json
    )

    # Gemini 3 Pro aufrufen
    logger.debug("Rufe Gemini 3 Pro auf")
    response = client.call_gemini([
        {"role": "user", "content": prompt}
    ], temperature=0.7, timeout=90)

    logger.debug(f"Gemini-Antwort erhalten ({len(response)} Zeichen)")

    # JSON aus Response extrahieren
    parsed = extract_json(response)

    if not parsed or "kategorien" not in parsed:
        logger.error("Keine gültige Qualitätsbewertung in der Antwort gefunden")
        raise ValueError(
            "Konnte keine gültige Qualitätsbewertung aus der KI-Antwort extrahieren.\n"
            f"Antwort (erste 500 Zeichen):\n{response[:500]}"
        )

    # Validierung
    validate_qualitaet(parsed)

    logger.info(f"Qualitätsprüfung abgeschlossen: Gesamtbewertung {parsed.get('gesamt_bewertung', '?')}/10")
    return parsed


def validate_qualitaet(data: dict[str, Any]) -> None:
    """
    Validiert die Qualitäts-Struktur.

    Args:
        data: Zu validierende Qualitäts-Daten

    Raises:
        ValueError: Bei ungültiger Struktur
    """
    # Required keys - mit Standardwerten falls fehlend
    if "gesamt_bewertung" not in data:
        # Berechne aus Kategorien falls vorhanden
        if "kategorien" in data and data["kategorien"]:
            bewertungen = [k.get("bewertung", 5) for k in data["kategorien"]]
            data["gesamt_bewertung"] = round(sum(bewertungen) / len(bewertungen))
            logger.warning("gesamt_bewertung berechnet aus Kategorien")
        else:
            data["gesamt_bewertung"] = 5
            logger.warning("gesamt_bewertung fehlt, setze auf 5")

    if "gesamt_kommentar" not in data:
        data["gesamt_kommentar"] = "Keine Bewertung verfügbar"
        logger.warning("gesamt_kommentar fehlt")

    if "kategorien" not in data:
        data["kategorien"] = []
        logger.warning("kategorien fehlt")

    if "fazit" not in data:
        data["fazit"] = "Keine Bewertung verfügbar"
        logger.warning("fazit fehlt")

    # Gesamtbewertung muss 1-10 sein
    if not (1 <= data["gesamt_bewertung"] <= 10):
        data["gesamt_bewertung"] = max(1, min(10, data["gesamt_bewertung"]))
        logger.warning(f"gesamt_bewertung korrigiert auf {data['gesamt_bewertung']}")

    # Kategorien validieren
    expected_categories = ["Vollständigkeit", "Reihenfolge", "Klarheit", "Dateien", "Regelwerk", "Lücken", "Duplikate"]

    for i, kategorie in enumerate(data.get("kategorien", [])):
        # Required fields für Kategorie
        if "name" not in kategorie:
            kategorie["name"] = expected_categories[i] if i < len(expected_categories) else f"Kategorie {i+1}"
            logger.warning(f"Kategorie {i+1}: name fehlt")

        if "bewertung" not in kategorie:
            kategorie["bewertung"] = 5
            logger.warning(f"Kategorie {kategorie['name']}: bewertung fehlt")

        if "status" not in kategorie:
            bewertung = kategorie.get("bewertung", 5)
            if bewertung >= 8:
                kategorie["status"] = "gut"
            elif bewertung >= 5:
                kategorie["status"] = "mittel"
            else:
                kategorie["status"] = "schlecht"
            logger.warning(f"Kategorie {kategorie['name']}: status berechnet")

        if "kommentar" not in kategorie:
            kategorie["kommentar"] = "Keine Details verfügbar"
            logger.warning(f"Kategorie {kategorie['name']}: kommentar fehlt")

        # Bewertung muss 1-10 sein
        if not (1 <= kategorie["bewertung"] <= 10):
            kategorie["bewertung"] = max(1, min(10, kategorie["bewertung"]))

        # Status muss valid sein
        if kategorie["status"] not in ["gut", "mittel", "schlecht"]:
            bewertung = kategorie.get("bewertung", 5)
            if bewertung >= 8:
                kategorie["status"] = "gut"
            elif bewertung >= 5:
                kategorie["status"] = "mittel"
            else:
                kategorie["status"] = "schlecht"

    # Optional: verbesserungen und warnungen als leere Listen initialisieren
    if "verbesserungen" not in data:
        data["verbesserungen"] = []

    if "warnungen" not in data:
        data["warnungen"] = []

    logger.debug("Qualitäts-Validierung erfolgreich")


def get_status_icon(status: str) -> str:
    """
    Gibt Icon für Status zurück.

    Args:
        status: "gut", "mittel" oder "schlecht"

    Returns:
        str: Icon (Emoji)
    """
    icons = {
        "gut": "✅",
        "mittel": "⚠️",
        "schlecht": "❌"
    }
    return icons.get(status, "❓")


def get_status_color(status: str) -> str:
    """
    Gibt CSS-Klasse für Status zurück.

    Args:
        status: "gut", "mittel" oder "schlecht"

    Returns:
        str: CSS-Klasse
    """
    colors = {
        "gut": "status-gut",
        "mittel": "status-mittel",
        "schlecht": "status-schlecht"
    }
    return colors.get(status, "status-unknown")


def format_qualitaet_for_display(data: dict[str, Any]) -> str:
    """
    Formatiert Qualitätsbewertung für die Anzeige (Markdown).

    Args:
        data: Qualitäts-Daten

    Returns:
        str: Markdown-formatierte Qualitätsbewertung
    """
    lines = []
    lines.append(f"# Qualitätsprüfung\n")
    lines.append(f"**Gesamtbewertung:** {data.get('gesamt_bewertung', '?')}/10\n")
    lines.append(f"\n{data.get('gesamt_kommentar', '')}\n")
    lines.append("---\n")

    # Kategorien
    lines.append("## Kategorien\n")
    for kategorie in data.get("kategorien", []):
        icon = get_status_icon(kategorie.get("status", ""))
        lines.append(f"### {icon} {kategorie.get('name', '?')} ({kategorie.get('bewertung', '?')}/10)\n")
        lines.append(f"{kategorie.get('kommentar', '')}\n\n")

    # Verbesserungen
    if data.get("verbesserungen"):
        lines.append("## Verbesserungsvorschläge\n")
        for verb in data["verbesserungen"]:
            lines.append(f"- **Auftrag {verb.get('auftrag', '?')}:** {verb.get('text', '')}\n")
        lines.append("\n")

    # Warnungen
    if data.get("warnungen"):
        lines.append("## ⚠️ Warnungen\n")
        for warn in data["warnungen"]:
            lines.append(f"- {warn}\n")
        lines.append("\n")

    # Fazit
    lines.append("## Fazit\n")
    lines.append(f"{data.get('fazit', 'Keine Bewertung verfügbar')}\n")

    return "\n".join(lines)
