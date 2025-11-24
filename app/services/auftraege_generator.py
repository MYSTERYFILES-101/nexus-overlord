"""
NEXUS OVERLORD v2.0 - Aufträge Generator
Sonnet 4.5 erstellt konkrete Aufträge pro Phase mit Regelwerk
"""

import json
import re
from typing import Dict, Any
from app.services.openrouter import get_client


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


def generate_auftraege(phasen_data: dict, enterprise_plan: str) -> Dict[str, Any]:
    """
    Generiert Aufträge mit Sonnet 4.5
    
    Args:
        phasen_data: Phasen-Struktur aus Auftrag 3.1
        enterprise_plan: Original Enterprise-Plan
        
    Returns:
        dict: Auftrags-Struktur mit Metadaten
        
    Raises:
        Exception: Bei API-Fehler oder JSON-Parse-Fehler
    """
    client = get_client()
    
    # Phasen als JSON formatieren
    phasen_json = json.dumps(phasen_data, indent=2, ensure_ascii=False)
    
    # Prompt mit Daten füllen
    prompt = AUFTRAEGE_PROMPT.format(
        enterprise_plan=enterprise_plan,
        phasen_json=phasen_json
    )
    
    # Sonnet 4.5 aufrufen
    response = client.call_sonnet([
        {"role": "user", "content": prompt}
    ], temperature=0.7, timeout=120)  # Längerer Timeout für komplexe Aufträge
    
    # JSON aus Response extrahieren
    parsed = extract_json(response)
    
    # Validierung
    validate_auftraege(parsed, phasen_data)
    
    return parsed


def extract_json(response: str) -> Dict[str, Any]:
    """
    Extrahiert JSON aus verschiedenen Response-Formaten
    (Gleiche Logik wie in phasen_generator.py)
    
    Args:
        response: API-Response
        
    Returns:
        dict: Geparste JSON-Struktur
        
    Raises:
        ValueError: Wenn kein valides JSON gefunden wurde
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


def validate_auftraege(data: Dict[str, Any], phasen_data: dict) -> None:
    """
    Validiert die Auftrags-Struktur
    
    Args:
        data: Zu validierende Auftrags-Daten
        phasen_data: Original Phasen-Daten zur Validierung
        
    Raises:
        ValueError: Bei invalider Struktur
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
        # Required fields
        required = ["phase_nummer", "auftrag_nummer", "name", "beschreibung", 
                   "schritte", "dateien", "technische_details", 
                   "erfolgs_kriterien", "regelwerk"]
        
        for field in required:
            if field not in auftrag:
                raise ValueError(f"Auftrag {i+1} fehlt Feld: '{field}'")
        
        # Phase-Nummer muss valid sein
        if not (1 <= auftrag["phase_nummer"] <= anzahl_phasen):
            raise ValueError(
                f"Auftrag {i+1}: Ungültige phase_nummer {auftrag['phase_nummer']} "
                f"(muss zwischen 1 und {anzahl_phasen} liegen)"
            )
        
        # Auftragsnummer-Format prüfen (X.Y)
        if not re.match(r'^\d+\.\d+$', auftrag["auftrag_nummer"]):
            raise ValueError(
                f"Auftrag {i+1}: Ungültiges Format für auftrag_nummer: '{auftrag['auftrag_nummer']}' "
                f"(erwartet: 'X.Y' wie '1.1')"
            )
        
        # Schritte muss Liste sein
        if not isinstance(auftrag["schritte"], list) or len(auftrag["schritte"]) == 0:
            raise ValueError(f"Auftrag {i+1}: 'schritte' muss nicht-leere Liste sein")
        
        # Dateien muss Liste sein
        if not isinstance(auftrag["dateien"], list):
            raise ValueError(f"Auftrag {i+1}: 'dateien' muss Liste sein")
        
        # Regelwerk muss Dict sein mit required keys
        if not isinstance(auftrag["regelwerk"], dict):
            raise ValueError(f"Auftrag {i+1}: 'regelwerk' muss Dict sein")
        
        regelwerk_required = ["commit_message", "uebergabe_pfad", "pflichten"]
        for field in regelwerk_required:
            if field not in auftrag["regelwerk"]:
                raise ValueError(f"Auftrag {i+1}: regelwerk fehlt Feld '{field}'")


def format_auftraege_for_display(data: Dict[str, Any]) -> str:
    """
    Formatiert Aufträge für die Anzeige (Markdown)
    
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
    auftraege_by_phase = {}
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
            
            lines.append("**Schritte:**\n")
            for schritt in auftrag["schritte"]:
                lines.append(f"- {schritt}\n")
            
            lines.append("**Dateien:**\n")
            for datei in auftrag["dateien"]:
                lines.append(f"- `{datei['pfad']}` ({datei['aktion']})\n")
            
            lines.append("**Erfolgs-Kriterien:**\n")
            for kriterium in auftrag["erfolgs_kriterien"]:
                lines.append(f"- {kriterium}\n")
            
            lines.append("\n")
    
    return "\n".join(lines)
