"""
NEXUS OVERLORD v2.0 - Phasen Generator
Gemini 3 Pro analysiert Enterprise-Plan und teilt in Phasen ein
"""

import json
import re
from typing import Dict, Any
from app.services.openrouter import get_client


PHASEN_PROMPT = """Du bist ein erfahrener Projekt-Stratege. Analysiere den folgenden Enterprise-Plan und teile ihn in 5-8 logische Phasen ein.

ENTERPRISE-PLAN:
{enterprise_plan}

AUFGABE:
1. Identifiziere die Hauptkomponenten des Projekts
2. Gruppiere zusammengehörige Aufgaben
3. Erkenne Abhängigkeiten (was muss zuerst fertig sein?)
4. Setze Prioritäten (hoch/mittel/niedrig)
5. Schätze realistische Dauer pro Phase

WICHTIG:
- Erstelle 5-8 Phasen (nicht mehr, nicht weniger)
- Jede Phase sollte logisch abgeschlossen sein
- Abhängigkeiten sind Phase-Nummern (z.B. [1, 2] = hängt von Phase 1 und 2 ab)
- Priorität: "hoch" für kritische, "mittel" für wichtige, "niedrig" für optionale Phasen

AUSGABE als JSON (NUR JSON, kein anderer Text):
{{
    "phasen": [
        {{
            "nummer": 1,
            "name": "Kurzer prägnanter Name",
            "beschreibung": "Detaillierte Beschreibung was in dieser Phase gemacht wird",
            "abhaengigkeiten": [],
            "prioritaet": "hoch",
            "geschaetzte_dauer": "2-3 Stunden"
        }},
        {{
            "nummer": 2,
            "name": "Nächste Phase",
            "beschreibung": "Was wird hier gemacht",
            "abhaengigkeiten": [1],
            "prioritaet": "mittel",
            "geschaetzte_dauer": "3-4 Stunden"
        }}
    ],
    "gesamt_phasen": 6,
    "gesamt_dauer": "15-20 Stunden",
    "hinweise": "Zusätzliche strategische Empfehlungen für die Umsetzung"
}}
"""


def generate_phasen(enterprise_plan: str) -> Dict[str, Any]:
    """
    Generiert Phasen-Einteilung mit Gemini 3 Pro
    
    Args:
        enterprise_plan: Der zu analysierende Enterprise-Plan
        
    Returns:
        dict: Phasen-Struktur mit Metadaten
        
    Raises:
        Exception: Bei API-Fehler oder JSON-Parse-Fehler
    """
    client = get_client()
    
    # Prompt mit Enterprise-Plan füllen
    prompt = PHASEN_PROMPT.format(enterprise_plan=enterprise_plan)
    
    # Gemini 3 Pro aufrufen
    response = client.call_gemini([
        {"role": "user", "content": prompt}
    ], temperature=0.7, timeout=90)
    
    # JSON aus Response extrahieren
    parsed = extract_json(response)
    
    # Validierung
    validate_phasen(parsed)
    
    return parsed


def extract_json(response: str) -> Dict[str, Any]:
    """
    Extrahiert JSON aus verschiedenen Response-Formaten
    
    Args:
        response: API-Response (kann JSON in Code-Block enthalten)
        
    Returns:
        dict: Geparste JSON-Struktur
        
    Raises:
        ValueError: Wenn kein valides JSON gefunden wurde
    """
    # Versuche verschiedene Extraktionsmethoden
    
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
            # Entferne evtl. Sprach-Marker (json, javascript, etc.)
            json_str = re.sub(r'^[a-z]+\n', '', json_str)
            return json.loads(json_str)
        except (IndexError, json.JSONDecodeError):
            pass
    
    # 3. Direktes JSON (ohne Code-Block)
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # 4. JSON im Text finden (suche nach { ... })
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Wenn nichts funktioniert: Fehler
    raise ValueError(
        f"Konnte kein valides JSON in Response finden.\n"
        f"Response (erste 500 Zeichen):\n{response[:500]}"
    )


def validate_phasen(data: Dict[str, Any]) -> None:
    """
    Validiert die Phasen-Struktur
    
    Args:
        data: Zu validierende Phasen-Daten
        
    Raises:
        ValueError: Bei invalider Struktur
    """
    # Required keys
    if "phasen" not in data:
        raise ValueError("Fehlendes Feld: 'phasen'")
    
    phasen = data["phasen"]
    
    if not isinstance(phasen, list):
        raise ValueError("'phasen' muss eine Liste sein")
    
    if len(phasen) < 5 or len(phasen) > 8:
        raise ValueError(f"Anzahl Phasen muss zwischen 5 und 8 liegen, ist aber {len(phasen)}")
    
    # Validiere jede Phase
    for i, phase in enumerate(phasen):
        # Required fields
        required = ["nummer", "name", "beschreibung", "abhaengigkeiten", "prioritaet"]
        for field in required:
            if field not in phase:
                raise ValueError(f"Phase {i+1} fehlt Feld: '{field}'")
        
        # Nummer muss i+1 sein (sequentiell)
        if phase["nummer"] != i + 1:
            raise ValueError(f"Phase-Nummern müssen sequentiell sein (erwartet {i+1}, ist {phase['nummer']})")
        
        # Priorität muss valid sein
        if phase["prioritaet"] not in ["hoch", "mittel", "niedrig"]:
            raise ValueError(f"Ungültige Priorität in Phase {i+1}: {phase['prioritaet']}")
        
        # Abhängigkeiten müssen Liste sein
        if not isinstance(phase["abhaengigkeiten"], list):
            raise ValueError(f"'abhaengigkeiten' in Phase {i+1} muss Liste sein")


def format_phasen_for_display(data: Dict[str, Any]) -> str:
    """
    Formatiert Phasen-Daten für die Anzeige (Markdown)
    
    Args:
        data: Phasen-Daten
        
    Returns:
        str: Markdown-formatierte Phasen
    """
    lines = []
    lines.append(f"# Phasen-Übersicht ({data.get('gesamt_phasen', len(data['phasen']))} Phasen)\n")
    lines.append(f"**Geschätzte Gesamtdauer:** {data.get('gesamt_dauer', 'N/A')}\n")
    
    if "hinweise" in data:
        lines.append(f"**Strategische Hinweise:** {data['hinweise']}\n")
    
    lines.append("---\n")
    
    for phase in data["phasen"]:
        lines.append(f"## Phase {phase['nummer']}: {phase['name']}\n")
        lines.append(f"**Beschreibung:** {phase['beschreibung']}\n")
        lines.append(f"**Priorität:** {phase['prioritaet'].upper()}\n")
        lines.append(f"**Dauer:** {phase.get('geschaetzte_dauer', 'N/A')}\n")
        
        if phase["abhaengigkeiten"]:
            deps = ", ".join([f"Phase {d}" for d in phase["abhaengigkeiten"]])
            lines.append(f"**Abhängigkeiten:** {deps}\n")
        else:
            lines.append("**Abhängigkeiten:** Keine\n")
        
        lines.append("\n")
    
    return "\n".join(lines)
