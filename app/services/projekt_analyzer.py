"""
NEXUS OVERLORD v2.0 - Projekt Analyzer (Auftrag 4.4)
Analysiert Projekt-Status mit Gemini 3 Pro und erstellt Zusammenfassung mit Opus 4.5
"""

from app.services.openrouter import get_client
from app.services.database import get_projekt_analyse


def analyze_projekt(projekt_id: int) -> dict:
    """
    Analysiert den kompletten Projekt-Status.

    Workflow:
    1. Alle Projekt-Daten aus DB sammeln
    2. Gemini 3 Pro: Analyse des Gesamtstatus
    3. Opus 4.5: Lesbare Zusammenfassung erstellen

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: {
            'status': 'success' | 'error',
            'daten': dict,        # Rohdaten aus DB
            'zusammenfassung': str  # Formatierte Zusammenfassung
        }
    """

    # 1. Daten aus DB sammeln
    daten = get_projekt_analyse(projekt_id)

    if not daten:
        return {
            'status': 'error',
            'message': 'Projekt nicht gefunden',
            'daten': None,
            'zusammenfassung': None
        }

    # 2. Zusammenfassung erstellen (lokal, ohne KI fuer Schnelligkeit)
    # KI-Analyse kann optional aktiviert werden
    zusammenfassung = _create_zusammenfassung(daten)

    return {
        'status': 'success',
        'daten': daten,
        'zusammenfassung': zusammenfassung
    }


def analyze_projekt_with_ai(projekt_id: int) -> dict:
    """
    Analysiert Projekt-Status mit KI (Gemini + Opus).
    Langsamer, aber detaillierter.

    Args:
        projekt_id: Projekt-ID

    Returns:
        dict: Analyse-Ergebnis
    """

    # Daten sammeln
    daten = get_projekt_analyse(projekt_id)

    if not daten:
        return {
            'status': 'error',
            'message': 'Projekt nicht gefunden',
            'daten': None,
            'zusammenfassung': None
        }

    try:
        client = get_client()

        # Gemini analysiert
        analyse = _analyze_with_gemini(client, daten)

        # Opus fasst zusammen
        zusammenfassung = _summarize_with_opus(client, daten, analyse)

        return {
            'status': 'success',
            'daten': daten,
            'analyse': analyse,
            'zusammenfassung': zusammenfassung
        }

    except Exception as e:
        # Fallback auf lokale Zusammenfassung
        return {
            'status': 'success',
            'daten': daten,
            'zusammenfassung': _create_zusammenfassung(daten),
            'error': str(e)
        }


def _create_zusammenfassung(daten: dict) -> str:
    """
    Erstellt lokale Zusammenfassung ohne KI (schnell).

    Args:
        daten: Projekt-Daten aus DB

    Returns:
        str: Formatierte Zusammenfassung
    """
    projekt = daten.get('projekt', {})
    aktuelle_phase = daten.get('aktuelle_phase', {})
    aktueller_auftrag = daten.get('aktueller_auftrag')
    fortschritt = daten.get('fortschritt', 0)
    total_auftraege = daten.get('total_auftraege', 0)
    erledigte = daten.get('erledigte_auftraege', 0)
    letzte_erledigte = daten.get('letzte_erledigte', [])
    offene_fehler = daten.get('offene_fehler', 0)
    total_phasen = daten.get('total_phasen', 0)

    # Progress-Bar erstellen
    filled = int(fortschritt / 10)
    empty = 10 - filled
    progress_bar = '█' * filled + '░' * empty

    # Zusammenfassung bauen
    zusammenfassung = f"""📍 AKTUELLER STAND

Projekt: {projekt.get('name', 'Unbekannt')}
Status: {projekt.get('status', 'Unbekannt').upper()}

Du bist in Phase {aktuelle_phase.get('nummer', '?')} von {total_phasen}: {aktuelle_phase.get('name', 'Unbekannte Phase')}
"""

    if aktueller_auftrag:
        zusammenfassung += f"Auftrag: {aktueller_auftrag.get('phase_nummer', '?')}.{aktueller_auftrag.get('nummer', '?')} - {aktueller_auftrag.get('name', 'Unbekannt')}\n"
        if aktueller_auftrag.get('status') == 'in_arbeit':
            zusammenfassung += "⚡ Status: IN ARBEIT\n"
    else:
        zusammenfassung += "Kein offener Auftrag gefunden.\n"

    zusammenfassung += f"""
───────────────────────────────

📊 FORTSCHRITT

[{progress_bar}] {fortschritt}%

{erledigte} von {total_auftraege} Auftraegen erledigt
"""

    # In Arbeit
    if daten.get('in_arbeit_auftraege', 0) > 0:
        zusammenfassung += f"🔄 {daten['in_arbeit_auftraege']} Auftrag(e) in Arbeit\n"

    # Zuletzt erledigt
    if letzte_erledigte:
        zusammenfassung += "\n───────────────────────────────\n\n✅ ZULETZT ERLEDIGT\n\n"
        for auftrag in letzte_erledigte[:3]:
            zusammenfassung += f"• {auftrag.get('phase_nummer', '?')}.{auftrag.get('nummer', '?')} - {auftrag.get('name', '')}\n"

    # Naechster Schritt
    zusammenfassung += "\n───────────────────────────────\n\n➡️ NAeCHSTER SCHRITT\n\n"

    if aktueller_auftrag:
        zusammenfassung += f"Arbeite an: {aktueller_auftrag.get('phase_nummer', '?')}.{aktueller_auftrag.get('nummer', '?')} - {aktueller_auftrag.get('name', 'Auftrag')}\n"

        beschreibung = aktueller_auftrag.get('beschreibung', '')
        if beschreibung:
            # Kurze Beschreibung (max 200 Zeichen)
            if len(beschreibung) > 200:
                beschreibung = beschreibung[:200] + '...'
            zusammenfassung += f"\n{beschreibung}\n"

        zusammenfassung += "\n💡 Tipp: Klicke auf 'Auftrag' um den vollstaendigen Auftrag zu laden.\n"
    else:
        if fortschritt >= 100:
            zusammenfassung += "🎉 Alle Auftraege erledigt! Das Projekt ist abgeschlossen.\n"
        else:
            zusammenfassung += "Kein offener Auftrag gefunden. Pruefe die Phasen-Uebersicht.\n"

    # Hinweise
    hinweise = []

    if offene_fehler > 0:
        hinweise.append(f"⚠️ {offene_fehler} Fehler in den letzten 7 Tagen gemeldet")

    if daten.get('in_arbeit_auftraege', 0) > 1:
        hinweise.append("⚠️ Mehrere Auftraege gleichzeitig in Arbeit - besser nacheinander abarbeiten")

    if fortschritt < 20 and total_auftraege > 0:
        hinweise.append("💪 Du bist am Anfang - ein Schritt nach dem anderen!")

    if fortschritt >= 80 and fortschritt < 100:
        hinweise.append("🎯 Fast geschafft! Nur noch wenige Auftraege.")

    if hinweise:
        zusammenfassung += "\n───────────────────────────────\n\n⚠️ HINWEISE\n\n"
        for hinweis in hinweise:
            zusammenfassung += f"{hinweis}\n"

    return zusammenfassung


def _analyze_with_gemini(client, daten: dict) -> str:
    """
    Gemini 3 Pro analysiert den Projekt-Status.
    """
    projekt = daten.get('projekt', {})
    phasen = daten.get('phasen', [])

    # Phasen-Liste formatieren
    phasen_text = ""
    for phase in phasen:
        status_icon = "✅" if phase.get('erledigte', 0) == phase.get('total_auftraege', 0) and phase.get('total_auftraege', 0) > 0 else "🔄" if phase.get('in_arbeit', 0) > 0 else "⏳"
        phasen_text += f"{status_icon} Phase {phase.get('nummer', '?')}: {phase.get('name', '')} - {phase.get('erledigte', 0)}/{phase.get('total_auftraege', 0)} erledigt\n"

    prompt = f"""Analysiere diesen Projekt-Status kurz und praezise:

Projekt: {projekt.get('name', 'Unbekannt')}
Status: {projekt.get('status', 'Unbekannt')}
Fortschritt: {daten.get('fortschritt', 0)}%

Phasen:
{phasen_text}

Erledigt: {daten.get('erledigte_auftraege', 0)}/{daten.get('total_auftraege', 0)} Auftraege
Offene Fehler: {daten.get('offene_fehler', 0)}

Gib eine kurze Einschaetzung (2-3 Saetze):
1. Wie gut laeuft das Projekt?
2. Gibt es Probleme oder Blockaden?
3. Empfehlung?"""

    messages = [{"role": "user", "content": prompt}]
    return client.call_gemini(messages, temperature=0.3, timeout=20)


def _summarize_with_opus(client, daten: dict, analyse: str) -> str:
    """
    Opus 4.5 erstellt lesbare Zusammenfassung.
    """
    prompt = f"""Erstelle eine kurze Status-Uebersicht basierend auf:

Analyse: {analyse}

Fortschritt: {daten.get('fortschritt', 0)}%
Aktuelle Phase: {daten.get('aktuelle_phase', {}).get('name', 'Unbekannt')}
Aktueller Auftrag: {daten.get('aktueller_auftrag', {}).get('name', 'Keiner') if daten.get('aktueller_auftrag') else 'Keiner'}

Formatiere als:
📍 AKTUELLER STAND
[Position im Projekt]

📊 FORTSCHRITT
[Progress-Bar und Zahlen]

➡️ NAeCHSTER SCHRITT
[Konkrete Empfehlung]

Halte es kurz und motivierend."""

    messages = [{"role": "user", "content": prompt}]
    return client.call_sonnet(messages, temperature=0.3, timeout=20)
