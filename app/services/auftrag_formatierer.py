"""
NEXUS OVERLORD v2.0 - Auftrag Formatierer (Auftrag 4.2)
Formatiert Auftraege fuer Claude Code mit Opus 4.5
"""

from app.services.openrouter import get_client
from datetime import datetime


def format_auftrag_for_claude(auftrag: dict, projekt: dict) -> str:
    """
    Formatiert einen Auftrag als Copy-Paste-fertig fuer Claude Code.

    Args:
        auftrag: Auftrag-Daten aus Datenbank
        projekt: Projekt-Daten

    Returns:
        str: Formatierter Auftrag-Text
    """

    # Basis-Informationen sammeln
    projekt_name = projekt.get('name', 'Unbekanntes Projekt')
    phase_nummer = auftrag.get('phase_nummer', 1)
    auftrag_nummer = auftrag.get('nummer', 1)
    total_phasen = auftrag.get('total_phasen', 7)

    # Schritte formatieren
    schritte = auftrag.get('schritte', [])
    schritte_text = ""
    if schritte:
        for i, schritt in enumerate(schritte, 1):
            schritte_text += f"{i}. {schritt}\n"
    else:
        schritte_text = "1. Auftrag analysieren\n2. Implementieren\n3. Testen"

    # Dateien formatieren
    dateien = auftrag.get('dateien', [])
    dateien_text = ""
    if dateien:
        for datei in dateien:
            if isinstance(datei, dict):
                pfad = datei.get('pfad', datei.get('path', ''))
                aktion = datei.get('aktion', datei.get('action', 'bearbeiten'))
                dateien_text += f"- {pfad} ({aktion})\n"
            else:
                dateien_text += f"- {datei}\n"

    # Technische Details formatieren
    tech_details = auftrag.get('technische_details', [])
    tech_text = ""
    if tech_details:
        for detail in tech_details:
            tech_text += f"- {detail}\n"

    # Erfolgs-Kriterien formatieren
    erfolg = auftrag.get('erfolgs_kriterien', [])
    erfolg_text = ""
    if erfolg:
        for kriterium in erfolg:
            erfolg_text += f"- [ ] {kriterium}\n"

    # Auftrag-Text zusammenbauen
    formatted = f"""═══════════════════════════════════════════════════════════════
🔷 NEXUS OVERLORD - AUFTRAG FUeR CLAUDE CODE
═══════════════════════════════════════════════════════════════

📌 PROJEKT-KONTEXT
- Projekt: {projekt_name}
- Repository: github.com/MYSTERYFILES-101/nexus-overlord
- Server: 116.203.191.160:5000
- Verzeichnis: /home/nexus/nexus-overlord

📌 AKTUELLER STAND
- Phase: {phase_nummer} von {total_phasen} - {auftrag.get('phase_name', 'Unbekannte Phase')}
- Auftrag: {phase_nummer}.{auftrag_nummer}

═══════════════════════════════════════════════════════════════

📋 AUFTRAG {phase_nummer}.{auftrag_nummer} - {auftrag.get('name', 'Unbenannter Auftrag').upper()}

📝 BESCHREIBUNG
{auftrag.get('beschreibung', 'Keine Beschreibung verfuegbar.')}

📝 SCHRITTE
{schritte_text}
"""

    if dateien_text:
        formatted += f"""📝 DATEIEN
{dateien_text}
"""

    if tech_text:
        formatted += f"""📝 TECHNISCHE DETAILS
{tech_text}
"""

    formatted += f"""═══════════════════════════════════════════════════════════════

⚠️ PFLICHTEN - NACH DIESEM AUFTRAG!

1. ✅ GITHUB PUSH
   git add .
   git commit -m "[{phase_nummer}.{auftrag_nummer}] {auftrag.get('name', 'Auftrag')}"
   git push origin main

2. ✅ UeBERGABE-DATEI SCHREIBEN
   Pfad: /projekt/uebergaben/{datetime.now().strftime('%Y-%m-%d')}_auftrag-{phase_nummer}-{auftrag_nummer}.md

3. ✅ STATUS MELDEN
   Format:
   "✅ AUFTRAG {phase_nummer}.{auftrag_nummer} ERLEDIGT
   - Gemacht: [Kurzbeschreibung]
   - GitHub: ✅ gepusht
   - Uebergabe: /projekt/uebergaben/...
   - Naechster: [Naechster Auftrag]"

4. ✅ SERVER DEPLOYMENT
   cd /home/nexus/nexus-overlord
   git pull origin main
   pkill -f "python.*main.py"
   source venv/bin/activate
   nohup python app/main.py > logs/server.log 2>&1 &

═══════════════════════════════════════════════════════════════

✅ ERFOLGS-KRITERIEN
{erfolg_text if erfolg_text else '- [ ] Auftrag vollstaendig umgesetzt\n- [ ] Keine Fehler beim Testen\n- [ ] GitHub gepusht\n- [ ] Server deployed'}

═══════════════════════════════════════════════════════════════"""

    return formatted


def format_auftrag_with_ai(auftrag: dict, projekt: dict) -> str:
    """
    Formatiert einen Auftrag mit Opus 4.5 fuer bessere Qualitaet.
    Fallback auf lokale Formatierung bei API-Fehlern.

    Args:
        auftrag: Auftrag-Daten aus Datenbank
        projekt: Projekt-Daten

    Returns:
        str: Formatierter Auftrag-Text
    """

    try:
        client = get_client()

        # Basis-Daten fuer den Prompt
        projekt_name = projekt.get('name', 'Unbekanntes Projekt')
        phase_nummer = auftrag.get('phase_nummer', 1)
        auftrag_nummer = auftrag.get('nummer', 1)
        total_phasen = auftrag.get('total_phasen', 7)

        prompt = f"""Du bist ein Auftrags-Formatierer fuer Claude Code.

Erstelle einen professionellen, copy-paste-fertigen Auftrag basierend auf diesen Daten:

PROJEKT: {projekt_name}
PHASE: {phase_nummer} von {total_phasen} - {auftrag.get('phase_name', '')}
AUFTRAG: {phase_nummer}.{auftrag_nummer} - {auftrag.get('name', '')}

BESCHREIBUNG:
{auftrag.get('beschreibung', 'Keine Beschreibung')}

SCHRITTE:
{auftrag.get('schritte', [])}

DATEIEN:
{auftrag.get('dateien', [])}

TECHNISCHE DETAILS:
{auftrag.get('technische_details', [])}

ERFOLGS-KRITERIEN:
{auftrag.get('erfolgs_kriterien', [])}

Formatiere den Auftrag im NEXUS OVERLORD Format mit:
- Header mit Projekt-Kontext
- Aktueller Stand (Phase X von Y)
- Auftrag-Details mit Beschreibung und Schritten
- Pflichten (GitHub Push, Uebergabe-Datei, Status melden, Server Deploy)
- Erfolgs-Kriterien als Checkliste

Verwende ═══ als Trennlinien und Emojis fuer Ueberschriften.
Der Output soll direkt in Claude Code eingefuegt werden koennen."""

        messages = [
            {"role": "user", "content": prompt}
        ]

        response = client.call_sonnet(messages, temperature=0.3, timeout=30)

        return response

    except Exception as e:
        # Fallback auf lokale Formatierung
        print(f"AI-Formatierung fehlgeschlagen: {e}, verwende lokale Formatierung")
        return format_auftrag_for_claude(auftrag, projekt)


def get_no_auftraege_message() -> str:
    """
    Gibt eine Nachricht zurueck wenn keine offenen Auftraege vorhanden sind.
    """
    return """🎉 ALLE AUFTRAeGE ERLEDIGT!

Es gibt keine offenen Auftraege mehr fuer dieses Projekt.

Moegliche naechste Schritte:
- Projekt als "fertig" markieren
- Neues Projekt erstellen
- Bestehende Auftraege ueberpruefen

Falls Auftraege als "in_arbeit" stehen, muessen diese erst abgeschlossen werden."""
