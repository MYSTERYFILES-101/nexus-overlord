"""
NEXUS OVERLORD v2.0 - Chat Routes

Chat-Funktionen fuer Projekt-Steuerung (Auftrag 4.6).
"""

import logging
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify

# Logger
logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/projekt/<int:projekt_id>/chat', methods=['GET'])
def chat_history(projekt_id: int):
    """Laedt Chat-Verlauf eines Projekts."""
    from app.services.database import get_projekt, get_chat_messages

    projekt = get_projekt(projekt_id)
    if not projekt:
        return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404

    messages = get_chat_messages(projekt_id, limit=100)

    return render_template('partials/chat_history.html',
                         messages=messages,
                         projekt=projekt)


@chat_bp.route('/projekt/<int:projekt_id>/chat', methods=['POST'])
def chat_send(projekt_id: int):
    """Sendet eine Chat-Nachricht."""
    from app.services.database import get_projekt, save_chat_message, get_current_auftrag_for_projekt

    projekt = get_projekt(projekt_id)
    if not projekt:
        return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404

    inhalt = request.form.get('inhalt', '').strip()
    typ = request.form.get('typ', 'USER').upper()

    if not inhalt:
        return jsonify({'success': False, 'error': 'Nachricht darf nicht leer sein'}), 400

    valid_types = ['USER', 'AUFTRAG', 'FEHLER', 'ANALYSE', 'SYSTEM', 'RUECKMELDUNG']
    if typ not in valid_types:
        typ = 'USER'

    aktueller_auftrag = get_current_auftrag_for_projekt(projekt_id)
    auftrag_id = aktueller_auftrag['id'] if aktueller_auftrag else None

    message_id = save_chat_message(projekt_id, typ, inhalt, auftrag_id)
    timestamp = datetime.now().strftime('%H:%M')

    return jsonify({
        'success': True,
        'message_id': message_id,
        'typ': typ,
        'inhalt': inhalt,
        'timestamp': timestamp
    })


@chat_bp.route('/projekt/<int:projekt_id>/chat/log', methods=['POST'])
def chat_log(projekt_id: int):
    """Loggt eine System-Nachricht im Chat (fuer Button-Aktionen)."""
    from app.services.database import save_chat_message

    inhalt = request.form.get('inhalt', '').strip()
    typ = request.form.get('typ', 'SYSTEM').upper()

    if not inhalt:
        return jsonify({'success': False, 'error': 'Inhalt fehlt'}), 400

    message_id = save_chat_message(projekt_id, typ, inhalt)

    return jsonify({'success': True, 'message_id': message_id})
