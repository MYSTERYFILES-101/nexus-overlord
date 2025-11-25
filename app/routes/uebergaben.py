"""
NEXUS OVERLORD v2.0 - Übergaben Routes

Upload und Verwaltung von Übergabe-Dateien (Auftrag 4.5).
"""

import logging
import os
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Logger
logger = logging.getLogger(__name__)

uebergaben_bp = Blueprint('uebergaben', __name__)

# Konfiguration
ALLOWED_EXTENSIONS = {'md', 'txt', 'json', 'log', 'pdf', 'docx', 'doc'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB


def allowed_file(filename: str) -> bool:
    """
    Prüft ob Dateiendung erlaubt ist.

    Args:
        filename: Dateiname

    Returns:
        bool: True wenn erlaubt
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@uebergaben_bp.route('/projekt/<int:projekt_id>/uebergaben', methods=['GET'])
def uebergaben_liste(projekt_id: int):
    """Holt Liste aller Übergaben eines Projekts."""
    from app.services.database import get_projekt, get_projekt_uebergaben, get_current_auftrag_for_projekt

    projekt = get_projekt(projekt_id)
    if not projekt:
        return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404

    uebergaben = get_projekt_uebergaben(projekt_id)
    aktueller_auftrag = get_current_auftrag_for_projekt(projekt_id)

    return render_template('partials/uebergaben_modal.html',
                         projekt=projekt,
                         uebergaben=uebergaben,
                         aktueller_auftrag=aktueller_auftrag)


@uebergaben_bp.route('/projekt/<int:projekt_id>/uebergaben/upload', methods=['POST'])
def uebergabe_upload(projekt_id: int):
    """Lädt eine Übergabe-Datei hoch."""
    from app.services.database import get_projekt, save_uebergabe, get_current_auftrag_for_projekt

    projekt = get_projekt(projekt_id)
    if not projekt:
        return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Keine Datei hochgeladen'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Keine Datei ausgewählt'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Dateityp nicht erlaubt'}), 400

    # Dateigröße prüfen
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_CONTENT_LENGTH:
        return jsonify({'success': False, 'error': 'Datei zu groß. Max 5MB erlaubt.'}), 400

    aktueller_auftrag = get_current_auftrag_for_projekt(projekt_id)
    auftrag_id = aktueller_auftrag['id'] if aktueller_auftrag else None

    # Dateiname generieren
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    original_name = secure_filename(file.filename)

    if aktueller_auftrag:
        auftrag_suffix = f"auftrag-{aktueller_auftrag['phase_nummer']}-{aktueller_auftrag['nummer']}"
        filename = f"{timestamp}_{auftrag_suffix}_{original_name}"
    else:
        filename = f"{timestamp}_{original_name}"

    # Upload-Ordner
    upload_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'projekt', 'uebergaben'
    )
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, filename)

    try:
        file.save(filepath)
    except Exception as e:
        logger.error(f"Fehler beim Speichern: {e}")
        return jsonify({'success': False, 'error': f'Fehler beim Speichern: {str(e)}'}), 500

    uebergabe_id = save_uebergabe(projekt_id, auftrag_id, filepath, original_name)

    return jsonify({
        'success': True,
        'uebergabe_id': uebergabe_id,
        'filename': filename,
        'auftrag': f"{aktueller_auftrag['phase_nummer']}.{aktueller_auftrag['nummer']}" if aktueller_auftrag else None
    })


@uebergaben_bp.route('/projekt/<int:projekt_id>/uebergaben/<int:uebergabe_id>', methods=['GET'])
def uebergabe_anzeigen(projekt_id: int, uebergabe_id: int):
    """Zeigt Inhalt einer Übergabe an."""
    from app.services.database import get_uebergabe

    uebergabe = get_uebergabe(uebergabe_id)

    if not uebergabe:
        return jsonify({'success': False, 'error': 'Übergabe nicht gefunden'}), 404

    try:
        with open(uebergabe['datei_pfad'], 'r', encoding='utf-8') as f:
            inhalt = f.read()
    except FileNotFoundError:
        inhalt = '[Datei nicht gefunden]'
    except Exception as e:
        inhalt = f'[Fehler beim Lesen: {str(e)}]'

    return render_template('partials/uebergabe_inhalt.html',
                         uebergabe=uebergabe,
                         inhalt=inhalt)


@uebergaben_bp.route('/projekt/<int:projekt_id>/uebergaben/<int:uebergabe_id>/delete', methods=['POST'])
def uebergabe_loeschen(projekt_id: int, uebergabe_id: int):
    """Löscht eine Übergabe."""
    from app.services.database import delete_uebergabe

    success = delete_uebergabe(uebergabe_id)

    if success:
        return jsonify({'success': True, 'message': 'Übergabe gelöscht'})
    else:
        return jsonify({'success': False, 'error': 'Übergabe nicht gefunden'}), 404
