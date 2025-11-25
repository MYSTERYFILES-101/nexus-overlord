"""
NEXUS OVERLORD v2.0 - Phasen Routes

Kachel 2: Phasen und Aufträge generieren, Qualitätsprüfung.
"""

import logging

import markdown2
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Logger
logger = logging.getLogger(__name__)

phasen_bp = Blueprint('phasen', __name__)


@phasen_bp.route('/projekt/<int:projekt_id>/phasen', methods=['GET', 'POST'])
def projekt_phasen_view(projekt_id: int):
    """Kachel 2: Phasen & Aufträge generieren (Phase 3)."""
    from app.services.database import get_projekt
    from app.services.phasen_generator import generate_phasen

    projekt = get_projekt(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden', 'error')
        return redirect(url_for('home.index'))

    if request.method == 'POST':
        enterprise_plan = projekt['enterprise_plan']

        try:
            phasen_data = generate_phasen(enterprise_plan)
            session['phasen_data'] = phasen_data
            session['projekt_id'] = projekt_id

            flash('Phasen erfolgreich generiert!', 'success')
            return redirect(url_for('phasen.projekt_phasen_ergebnis', projekt_id=projekt_id))

        except Exception as e:
            logger.error(f"Phasen-Generierung fehlgeschlagen: {e}")
            flash(f'Fehler bei Phasen-Generierung: {str(e)}', 'error')
            return redirect(url_for('phasen.projekt_phasen_view', projekt_id=projekt_id))

    return render_template('projekt_phasen.html', projekt=projekt)


@phasen_bp.route('/projekt/<int:projekt_id>/phasen/ergebnis')
def projekt_phasen_ergebnis(projekt_id: int):
    """Zeigt generierte Phasen an (Auftrag 3.1)."""
    from app.services.database import get_projekt
    from app.services.phasen_generator import format_phasen_for_display

    projekt = get_projekt(projekt_id)
    phasen_data = session.get('phasen_data')

    if not phasen_data:
        flash('Keine Phasen gefunden. Bitte erst generieren.', 'error')
        return redirect(url_for('phasen.projekt_phasen_view', projekt_id=projekt_id))

    phasen_markdown = format_phasen_for_display(phasen_data)
    phasen_html = markdown2.markdown(phasen_markdown, extras=['fenced-code-blocks', 'tables'])

    return render_template('projekt_phasen_ergebnis.html',
                          projekt=projekt,
                          phasen_data=phasen_data,
                          phasen_html=phasen_html)


@phasen_bp.route('/projekt/phasen')
def projekt_phasen():
    """Legacy route - redirect to projekt with ID from session."""
    projekt_id = session.get('projekt_id')
    if projekt_id:
        return redirect(url_for('phasen.projekt_phasen_view', projekt_id=projekt_id))
    else:
        flash('Kein aktives Projekt gefunden', 'error')
        return redirect(url_for('home.index'))


@phasen_bp.route('/projekt/<int:projekt_id>/auftraege/generieren', methods=['POST'])
def auftraege_generieren(projekt_id: int):
    """Generiert Aufträge mit Opus 4.5 (Auftrag 3.2)."""
    from app.services.database import get_projekt
    from app.services.auftraege_generator import generate_auftraege

    projekt = get_projekt(projekt_id)
    phasen_data = session.get('phasen_data')

    if not projekt:
        flash('Projekt nicht gefunden', 'error')
        return redirect(url_for('home.index'))

    if not phasen_data:
        flash('Erst Phasen generieren!', 'error')
        return redirect(url_for('phasen.projekt_phasen_view', projekt_id=projekt_id))

    try:
        auftraege_data = generate_auftraege(phasen_data, projekt['enterprise_plan'])
        session['auftraege_data'] = auftraege_data
        session['projekt_id'] = projekt_id

        flash('Aufträge erfolgreich generiert!', 'success')
        return redirect(url_for('phasen.auftraege_anzeigen', projekt_id=projekt_id))

    except Exception as e:
        logger.error(f"Auftrags-Generierung fehlgeschlagen: {e}")
        flash(f'Fehler bei Auftrags-Generierung: {str(e)}', 'error')
        return redirect(url_for('phasen.projekt_phasen_ergebnis', projekt_id=projekt_id))


@phasen_bp.route('/projekt/<int:projekt_id>/auftraege')
def auftraege_anzeigen(projekt_id: int):
    """Zeigt generierte Aufträge an (Auftrag 3.2)."""
    from app.services.database import get_projekt

    projekt = get_projekt(projekt_id)
    auftraege_data = session.get('auftraege_data')
    phasen_data = session.get('phasen_data')

    if not auftraege_data:
        flash('Keine Aufträge gefunden. Bitte erst generieren.', 'error')
        return redirect(url_for('phasen.projekt_phasen_ergebnis', projekt_id=projekt_id))

    # Gruppiere Aufträge nach Phase
    auftraege_by_phase = {}
    for auftrag in auftraege_data.get('auftraege', []):
        phase_nr = auftrag['phase_nummer']
        if phase_nr not in auftraege_by_phase:
            auftraege_by_phase[phase_nr] = []
        auftraege_by_phase[phase_nr].append(auftrag)

    # Phasen-Namen
    phasen_namen = {}
    if phasen_data and 'phasen' in phasen_data:
        for phase in phasen_data['phasen']:
            phasen_namen[phase['nummer']] = phase['name']

    return render_template('projekt_auftraege.html',
                          projekt=projekt,
                          auftraege_data=auftraege_data,
                          auftraege_by_phase=auftraege_by_phase,
                          phasen_namen=phasen_namen)


@phasen_bp.route('/projekt/<int:projekt_id>/auftraege/pruefen', methods=['POST'])
def auftraege_pruefen(projekt_id: int):
    """Prüft Aufträge mit Gemini 3 Pro (Auftrag 3.3)."""
    from app.services.database import get_projekt
    from app.services.qualitaetspruefung import pruefen_auftraege

    projekt = get_projekt(projekt_id)
    phasen_data = session.get('phasen_data')
    auftraege_data = session.get('auftraege_data')

    if not projekt:
        flash('Projekt nicht gefunden', 'error')
        return redirect(url_for('home.index'))

    if not phasen_data or not auftraege_data:
        flash('Erst Phasen und Aufträge generieren!', 'error')
        return redirect(url_for('phasen.projekt_phasen_view', projekt_id=projekt_id))

    try:
        qualitaet_data = pruefen_auftraege(auftraege_data, phasen_data, projekt['enterprise_plan'])
        session['qualitaet_data'] = qualitaet_data
        session['projekt_id'] = projekt_id

        flash('Qualitätsprüfung abgeschlossen!', 'success')
        return redirect(url_for('phasen.qualitaet_anzeigen', projekt_id=projekt_id))

    except Exception as e:
        logger.error(f"Qualitätsprüfung fehlgeschlagen: {e}")
        flash(f'Fehler bei Qualitätsprüfung: {str(e)}', 'error')
        return redirect(url_for('phasen.auftraege_anzeigen', projekt_id=projekt_id))


@phasen_bp.route('/projekt/<int:projekt_id>/auftraege/qualitaet')
def qualitaet_anzeigen(projekt_id: int):
    """Zeigt Qualitäts-Bewertung an (Auftrag 3.3)."""
    from app.services.database import get_projekt
    from app.services.qualitaetspruefung import get_status_icon, get_status_color

    projekt = get_projekt(projekt_id)
    qualitaet_data = session.get('qualitaet_data')

    if not qualitaet_data:
        flash('Keine Qualitätsprüfung gefunden. Bitte erst prüfen.', 'error')
        return redirect(url_for('phasen.auftraege_anzeigen', projekt_id=projekt_id))

    for kategorie in qualitaet_data.get('kategorien', []):
        kategorie['icon'] = get_status_icon(kategorie.get('status', ''))
        kategorie['color_class'] = get_status_color(kategorie.get('status', ''))

    return render_template('projekt_qualitaet.html',
                          projekt=projekt,
                          qualitaet=qualitaet_data)


@phasen_bp.route('/projekt/<int:projekt_id>/abschliessen', methods=['POST'])
def projekt_abschliessen(projekt_id: int):
    """Speichert alle generierten Daten in DB (Auftrag 3.4)."""
    from app.services.database import save_phasen, save_auftraege, update_projekt_qualitaet

    phasen_data = session.get('phasen_data')
    auftraege_data = session.get('auftraege_data')
    qualitaet_data = session.get('qualitaet_data')

    if not phasen_data or not auftraege_data or not qualitaet_data:
        flash('Nicht alle Daten vorhanden. Bitte Workflow komplett durchlaufen.', 'error')
        return redirect(url_for('home.index'))

    try:
        # 1. Phasen speichern
        phase_ids = save_phasen(projekt_id, phasen_data)

        # 2. Aufträge pro Phase speichern
        for phase_nr, phase_id in phase_ids:
            phase_auftraege = [a for a in auftraege_data.get('auftraege', [])
                              if a['phase_nummer'] == phase_nr]
            if phase_auftraege:
                save_auftraege(phase_id, phase_auftraege)

        # 3. Qualität speichern
        update_projekt_qualitaet(projekt_id, qualitaet_data)

        # 4. Session aufräumen
        session.pop('phasen_data', None)
        session.pop('auftraege_data', None)
        session.pop('qualitaet_data', None)
        session.pop('projekt_id', None)

        flash('Projekt erfolgreich gespeichert! Status: BEREIT', 'success')
        return redirect(url_for('projekt.projekt_uebersicht', projekt_id=projekt_id))

    except Exception as e:
        logger.error(f"Fehler beim Abschließen: {e}")
        flash(f'Fehler beim Speichern: {str(e)}', 'error')
        return redirect(url_for('phasen.qualitaet_anzeigen', projekt_id=projekt_id))
