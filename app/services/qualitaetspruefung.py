"""
NEXUS OVERLORD v2.0 - Qualitaetspruefung

Gemini 3 Pro prueft generierte Auftraege auf Qualitaet.

Pruefungskategorien:
    - Vollstaendigkeit: Deckt der Plan alles ab?
    - Reihenfolge: Sind Abhaengigkeiten korrekt?
    - Klarheit: Sind Schritte verstaendlich?
    - Dateien: Sind Pfade und Aktionen korrekt?
    - Regelwerk: Ist das Format konsistent?
    - Luecken: Fehlt etwas Wichtiges?
    - Duplikate: Gibt es Ueberschneidungen?
"""

import json
import logging
from typing import Any

from app.services.openrouter import get_client
from app.utils.json_extractor import extract_json

# Logger konfigurieren
logger = logging.getLogger(__name__)


# Prompt-Template fuer Qualitaetspruefung
QUALITAET_PROMPT = """Du bist ein erfahrener QA-Manager und Software-Architekt. Pruefe die folgenden Auftraege auf Vollstaendigkeit und Qualitaet.

ENTERPRISE-PLAN (Original):
{enterprise_plan}

PHASEN-STRUKTUR:
{phasen_json}

GENERIERTE AUFTRAeGE:
{auftraege_json}

AUFGABE:
Pruefe die Auftraege kritisch auf folgende Kategorien:

1. **Vollstaendigkeit** (1-10)
   - Decken die Auftraege den gesamten Enterprise-Plan ab?
   - Sind alle Features/Komponenten beruecksichtigt?
   - Fehlt etwas Wichtiges?

2. **Reihenfolge** (1-10)
   - Sind Abhaengigkeiten korrekt beruecksichtigt?
   - Macht die Sequenz Sinn?
   - Kann man so tatsaechlich arbeiten?

3. **Klarheit** (1-10)
   - Sind die Schritte verstaendlich?
   - Kann ein Entwickler die Auftraege ausfuehren?
   - Sind technische Details ausreichend?

4. **Dateien** (1-10)
   - Sind alle benoetigten Dateien genannt?
   - Sind die Pfade korrekt?
   - Sind die Aktionen (neu/aendern) richtig?

5. **Regelwerk** (1-10)
   - Ist das Uebergabe-Format konsistent?
   - Sind Commit-Messages einheitlich?
   - Sind die Pflichten klar definiert?

6. **Luecken** (1-10)
   - Fehlen wichtige Aspekte?
   - Sind Tests/Dokumentation beruecksichtigt?
   - Gibt es unklare Bereiche?

7. **Duplikate** (1-10)
   - Gibt es unnoetige Ueberschneidungen?
   - Wiederholen sich Aufgaben?
   - Ist alles einzigartig?

BEWERTUNGS-SKALA:
- 1-4: Schlecht (kritische Probleme)
- 5-7: Mittel (Verbesserungen noetig)
- 8-10: Gut (akzeptabel)

AUSGABE als JSON (NUR JSON, kein anderer Text):
{{
    "gesamt_bewertung": 8,
    "gesamt_kommentar": "Die Auftraege sind gut strukturiert und decken den Enterprise-Plan weitgehend ab. Einige Details koennten praeziser sein.",
    "kategorien": [
        {{
            "name": "Vollstaendigkeit",
            "bewertung": 9,
            "status": "gut",
            "kommentar": "Alle Aspekte des Plans sind abgedeckt. Keine wichtigen Features fehlen."
        }},
        {{
            "name": "Reihenfolge",
            "bewertung": 8,
            "status": "gut",
            "kommentar": "Abhaengigkeiten sind korrekt. Setup kommt zuerst, Tests am Ende."
        }},
        {{
            "name": "Klarheit",
            "bewertung": 7,
            "status": "mittel",
            "kommentar": "Die meisten Schritte sind klar. Einige koennten detaillierter sein."
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
            "kommentar": "Uebergabe-Format ist einheitlich ueber alle Auftraege."
        }},
        {{
            "name": "Luecken",
            "bewertung": 8,
            "status": "gut",
            "kommentar": "Keine kritischen Luecken. Tests und Docs sind erwaehnt."
        }},
        {{
            "name": "Duplikate",
            "bewertung": 9,
            "status": "gut",
            "kommentar": "Keine unnoetigen Wiederholungen gefunden."
        }}
    ],
    "verbesserungen": [
        {{
            "auftrag": "2.3",
            "typ": "empfehlung",
            "text": "Schritt 2 koennte konkreter sein: Welche Felder genau im Formular?"
        }},
        {{
            "auftrag": "3.1",
            "typ": "empfehlung",
            "text": "Technische Details: Welche Test-Library wird verwendet?"
        }}
    ],
    "warnungen": [],
    "fazit": "Die Auftraege sind gut vorbereitet und bereit fuer die Umsetzung. Kleinere Detailverbesserungen sind optional."
}}

WICHTIG:
- Sei kritisch aber konstruktiv
- Bei Bewertung < 7: Gib konkrete Verbesserungen an
- Bei kritischen Problemen: Fuege Warnungen hinzu
- status MUSS "gut", "mittel" oder "schlecht" sein
- Gesamtbewertung ist der Durchschnitt der Kategorien (gerundet)
"""


def pruefen_auftraege(
    auftraege_data: dict[str, Any],
    phasen_data: dict[str, Any],
    enterprise_plan: str
) -> dict[str, Any]:
    """
    Prueft Auftraege mit Gemini 3 Pro auf Qualitaet.

    Args:
        auftraege_data: Auftrags-Struktur aus dem Auftraege-Generator
        phasen_data: Phasen-Struktur aus dem Phasen-Generator
        enterprise_plan: Original Enterprise-Plan

    Returns:
        dict: Qualitaets-Bewertung mit:
            - gesamt_bewertung: Gesamtnote (1-10)
            - gesamt_kommentar: Zusammenfassung
            - kategorien: Liste der 7 Kategorien mit Bewertungen
            - verbesserungen: Konkrete Verbesserungsvorschlaege
            - warnungen: Kritische Warnungen
            - fazit: Abschliessendes Fazit

    Raises:
        ValueError: Bei ungueltiger JSON-Antwort oder Validierungsfehler
        Exception: Bei API-Fehler
    """
    logger.info("Starte Qualitaetspruefung")

    client = get_client()

    # Daten als JSON formatieren
    phasen_json = json.dumps(phasen_data, indent=2, ensure_ascii=False)
    auftraege_json = json.dumps(auftraege_data, indent=2, ensure_ascii=False)

    # Prompt mit Daten fuellen
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
        logger.error("Keine gueltige Qualitaetsbewertung in der Antwort gefunden")
        raise ValueError(
            "Konnte keine gueltige Qualitaetsbewertung aus der KI-Antwort extrahieren.\n"
            f"Antwort (erste 500 Zeichen):\n{response[:500]}"
        )

    # Validierung
    validate_qualitaet(parsed)

    logger.info(f"Qualitaetspruefung abgeschlossen: Gesamtbewertung {parsed.get('gesamt_bewertung', '?')}/10")
    return parsed


def validate_qualitaet(data: dict[str, Any]) -> None:
    """
    Validiert die Qualitaets-Struktur.

    Args:
        data: Zu validierende Qualitaets-Daten

    Raises:
        ValueError: Bei ungueltiger Struktur
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
        data["gesamt_kommentar"] = "Keine Bewertung verfuegbar"
        logger.warning("gesamt_kommentar fehlt")

    if "kategorien" not in data:
        data["kategorien"] = []
        logger.warning("kategorien fehlt")

    if "fazit" not in data:
        data["fazit"] = "Keine Bewertung verfuegbar"
        logger.warning("fazit fehlt")

    # Gesamtbewertung muss 1-10 sein
    if not (1 <= data["gesamt_bewertung"] <= 10):
        data["gesamt_bewertung"] = max(1, min(10, data["gesamt_bewertung"]))
        logger.warning(f"gesamt_bewertung korrigiert auf {data['gesamt_bewertung']}")

    # Kategorien validieren
    expected_categories = ["Vollstaendigkeit", "Reihenfolge", "Klarheit", "Dateien", "Regelwerk", "Luecken", "Duplikate"]

    for i, kategorie in enumerate(data.get("kategorien", [])):
        # Required fields fuer Kategorie
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
            kategorie["kommentar"] = "Keine Details verfuegbar"
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

    logger.debug("Qualitaets-Validierung erfolgreich")


def get_status_icon(status: str) -> str:
    """
    Gibt Icon fuer Status zurueck.

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
    Gibt CSS-Klasse fuer Status zurueck.

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
    Formatiert Qualitaetsbewertung fuer die Anzeige (Markdown).

    Args:
        data: Qualitaets-Daten

    Returns:
        str: Markdown-formatierte Qualitaetsbewertung
    """
    lines = []
    lines.append(f"# Qualitaetspruefung\n")
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
        lines.append("## Verbesserungsvorschlaege\n")
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
    lines.append(f"{data.get('fazit', 'Keine Bewertung verfuegbar')}\n")

    return "\n".join(lines)
