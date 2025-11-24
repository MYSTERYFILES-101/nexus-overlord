"""
NEXUS OVERLORD v2.0 - Qualitätsprüfung
Gemini 3 Pro prüft generierte Aufträge auf Qualität
"""

import json
import re
from typing import Dict, Any
from app.services.openrouter import get_client


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
- 1-4: Schlecht (❌ kritische Probleme)
- 5-7: Mittel (⚠️ Verbesserungen nötig)
- 8-10: Gut (✅ akzeptabel)

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


def pruefen_auftraege(auftraege_data: dict, phasen_data: dict, enterprise_plan: str) -> Dict[str, Any]:
    """
    Prüft Aufträge mit Gemini 3 Pro
    
    Args:
        auftraege_data: Auftrags-Struktur aus Auftrag 3.2
        phasen_data: Phasen-Struktur aus Auftrag 3.1
        enterprise_plan: Original Enterprise-Plan
        
    Returns:
        dict: Qualitäts-Bewertung mit Feedback
        
    Raises:
        Exception: Bei API-Fehler oder JSON-Parse-Fehler
    """
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
    response = client.call_gemini([
        {"role": "user", "content": prompt}
    ], temperature=0.7, timeout=90)
    
    # JSON aus Response extrahieren
    parsed = extract_json(response)
    
    # Validierung
    validate_qualitaet(parsed)
    
    return parsed


def extract_json(response: str) -> Dict[str, Any]:
    """
    Extrahiert JSON aus verschiedenen Response-Formaten
    (Gleiche Logik wie in anderen Generatoren)
    """
    # 1. JSON in Code-Block (```json ... ```)
    if "```json" in response:
        try:
            json_str = response.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (IndexError, json.JSONDecodeError):
            pass
    
    # 2. JSON in allgemeinem Code-Block (``` ... ```)
    if "```" in response:
        try:
            json_str = response.split("```")[1].split("```")[0].strip()
            json_str = re.sub(r'^[a-z]+\n', '', json_str)
            return json.loads(json_str)
        except (IndexError, json.JSONDecodeError):
            pass
    
    # 3. Direktes JSON
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # 4. JSON im Text finden
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValueError(
        f"Konnte kein valides JSON in Response finden.\n"
        f"Response (erste 500 Zeichen):\n{response[:500]}"
    )


def validate_qualitaet(data: Dict[str, Any]) -> None:
    """
    Validiert die Qualitäts-Struktur
    
    Args:
        data: Zu validierende Qualitäts-Daten
        
    Raises:
        ValueError: Bei invalider Struktur
    """
    # Required keys
    required_top = ["gesamt_bewertung", "gesamt_kommentar", "kategorien", "fazit"]
    for field in required_top:
        if field not in data:
            raise ValueError(f"Fehlendes Feld: '{field}'")
    
    # Gesamtbewertung muss 1-10 sein
    if not (1 <= data["gesamt_bewertung"] <= 10):
        raise ValueError(f"gesamt_bewertung muss zwischen 1 und 10 liegen, ist {data['gesamt_bewertung']}")
    
    # Kategorien muss Liste sein
    if not isinstance(data["kategorien"], list):
        raise ValueError("'kategorien' muss eine Liste sein")
    
    if len(data["kategorien"]) != 7:
        raise ValueError(f"Es müssen genau 7 Kategorien sein, sind aber {len(data['kategorien'])}")
    
    # Validiere jede Kategorie
    expected_categories = ["Vollständigkeit", "Reihenfolge", "Klarheit", "Dateien", "Regelwerk", "Lücken", "Duplikate"]
    
    for i, kategorie in enumerate(data["kategorien"]):
        # Required fields
        required_kat = ["name", "bewertung", "status", "kommentar"]
        for field in required_kat:
            if field not in kategorie:
                raise ValueError(f"Kategorie {i+1} fehlt Feld: '{field}'")
        
        # Name muss einer der erwarteten sein
        if kategorie["name"] not in expected_categories:
            raise ValueError(f"Unerwarteter Kategorie-Name: '{kategorie['name']}' (erwartet: {expected_categories})")
        
        # Bewertung muss 1-10 sein
        if not (1 <= kategorie["bewertung"] <= 10):
            raise ValueError(f"Kategorie {kategorie['name']}: bewertung muss 1-10 sein, ist {kategorie['bewertung']}")
        
        # Status muss valid sein
        if kategorie["status"] not in ["gut", "mittel", "schlecht"]:
            raise ValueError(f"Kategorie {kategorie['name']}: Ungültiger status '{kategorie['status']}'")
    
    # Verbesserungen muss Liste sein (optional)
    if "verbesserungen" in data and not isinstance(data["verbesserungen"], list):
        raise ValueError("'verbesserungen' muss Liste sein")
    
    # Warnungen muss Liste sein (optional)
    if "warnungen" in data and not isinstance(data["warnungen"], list):
        raise ValueError("'warnungen' muss Liste sein")


def get_status_icon(status: str) -> str:
    """
    Gibt Icon für Status zurück
    
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
    Gibt CSS-Klasse für Status zurück
    
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
