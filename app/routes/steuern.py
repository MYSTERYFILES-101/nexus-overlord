"""
NEXUS OVERLORD v2.0 - Steuern Routes

Kachel 3: Projekt steuern mit 5 Buttons (Auftrag, Fehler, Analyse, etc.)
"""

import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

# Logger
logger = logging.getLogger(__name__)

steuern_bp = Blueprint('steuern', __name__)


@steuern_bp.route('/projekt/<int:projekt_id>/steuern')
def projekt_steuern(projekt_id: int):
    """
    Kachel 3: Projekt steuern - Hauptarbeitsbereich (Auftrag 4.1).

    Layout mit Sidebar (Projekte + Phasen) und Chat-Bereich.
    """
    from app.services.database import get_all_projekte, get_projekt_komplett

    projekte = get_all_projekte()
    projekt = get_projekt_komplett(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden', 'error')
        return redirect(url_for('projekt.projekt_liste'))

    # Aktuelle Phase ermitteln
    aktuelle_phase = None
    for phase in projekt.get('phasen', []):
        if phase.get('status') != 'fertig':
            aktuelle_phase = phase
            break
    if not aktuelle_phase and projekt.get('phasen'):
        aktuelle_phase = projekt['phasen'][-1]

    return render_template('projekt_steuern.html',
                          projekt=projekt,
                          projekte=projekte,
                          aktuelle_phase=aktuelle_phase)


@steuern_bp.route('/projekt/<int:projekt_id>/auftrag', methods=['POST'])
def projekt_auftrag(projekt_id: int):
    """
    Holt naechsten offenen Auftrag (Auftrag 4.2).

    Wird per HTMX aufgerufen.
    """
    from app.services.database import (
        get_projekt, get_next_open_auftrag,
        update_auftrag_status, save_chat_message
    )
    from app.services.auftrag_formatierer import format_auftrag_for_claude, get_no_auftraege_message

    projekt = get_projekt(projekt_id)
    if not projekt:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Projekt nicht gefunden.')

    auftrag = get_next_open_auftrag(projekt_id)

    if not auftrag:
        msg = get_no_auftraege_message()
        save_chat_message(projekt_id, 'SYSTEM', msg)
        return render_template('partials/chat_message.html',
                             message_type='info',
                             content=msg)

    formatted_auftrag = format_auftrag_for_claude(auftrag, projekt)
    update_auftrag_status(auftrag['id'], 'in_arbeit')

    auftrag_name = f"{auftrag.get('phase_nummer', 1)}.{auftrag.get('nummer', 1)} - {auftrag.get('name', 'Auftrag')}"
    save_chat_message(projekt_id, 'AUFTRAG', f"Auftrag geladen: {auftrag_name}", auftrag['id'])

    return render_template('partials/chat_message.html',
                         message_type='auftrag',
                         auftrag_name=auftrag_name,
                         content=formatted_auftrag,
                         auftrag_id=auftrag['id'])


@steuern_bp.route('/projekt/<int:projekt_id>/auftrag/<int:auftrag_id>/status', methods=['POST'])
def auftrag_status_update(projekt_id: int, auftrag_id: int):
    """Aktualisiert den Status eines Auftrags (Auftrag 4.2)."""
    from app.services.database import update_auftrag_status

    status = request.form.get('status', 'fertig')

    if status not in ['offen', 'in_arbeit', 'fertig', 'fehler']:
        return jsonify({'success': False, 'error': 'Ungueltiger Status'}), 400

    success = update_auftrag_status(auftrag_id, status)

    if success:
        return jsonify({'success': True, 'status': status})
    else:
        return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404


@steuern_bp.route('/projekt/<int:projekt_id>/fehler', methods=['POST'])
def projekt_fehler(projekt_id: int):
    """
    Analysiert einen Fehler und gibt Loesung zurueck (Auftrag 4.3).

    Prueft DB nach bekannten Fehlern, sonst KI-Analyse.
    """
    from app.services.database import get_projekt, save_chat_message
    from app.services.fehler_analyzer import analyze_fehler

    projekt = get_projekt(projekt_id)
    if not projekt:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Projekt nicht gefunden.')

    fehler_text = request.form.get('fehler_text', '').strip()

    if not fehler_text:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Bitte gib einen Fehler-Text ein.')

    result = analyze_fehler(fehler_text, projekt.get('name', 'NEXUS OVERLORD'))
    save_chat_message(projekt_id, 'FEHLER', f"Fehler analysiert: {result['kategorie']}")

    return render_template('partials/fehler_response.html',
                         bekannt=result['bekannt'],
                         kategorie=result['kategorie'],
                         ursache=result['ursache'],
                         loesung=result['loesung'],
                         auftrag=result['auftrag'],
                         fehler_id=result.get('fehler_id'),
                         erfolgsrate=result.get('erfolgsrate', 0),
                         anzahl=result.get('anzahl', 0))


@steuern_bp.route('/projekt/<int:projekt_id>/fehler/<int:fehler_id>/feedback', methods=['POST'])
def fehler_feedback(projekt_id: int, fehler_id: int):
    """Feedback zur Fehler-Loesung (Auftrag 4.3)."""
    from app.services.database import update_fehler_erfolgsrate

    erfolg = request.form.get('erfolg', 'true').lower() == 'true'
    update_fehler_erfolgsrate(fehler_id, erfolg)

    return jsonify({'success': True, 'message': 'Feedback gespeichert'})


@steuern_bp.route('/projekt/<int:projekt_id>/analysieren', methods=['POST'])
def projekt_analysieren(projekt_id: int):
    """
    Analysiert den Projekt-Status (Auftrag 4.4).

    Gemini 3 Pro analysiert, Opus 4.5 erstellt Zusammenfassung.
    """
    from app.services.database import get_projekt, save_chat_message
    from app.services.projekt_analyzer import analyze_projekt

    projekt = get_projekt(projekt_id)
    if not projekt:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Projekt nicht gefunden.')

    result = analyze_projekt(projekt_id)

    if result['status'] == 'error':
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content=result.get('message', 'Analyse fehlgeschlagen'))

    fortschritt = result['daten'].get('fortschritt', 0)
    save_chat_message(projekt_id, 'ANALYSE', f"Projekt-Analyse: {fortschritt}% Fortschritt")

    return render_template('partials/analyse_response.html',
                         projekt_name=projekt.get('name', 'Unbekannt'),
                         zusammenfassung=result['zusammenfassung'],
                         daten=result['daten'])
