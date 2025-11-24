"""
NEXUS OVERLORD v2.0 - Main Entry Point
Flask Web Application
"""

# Fix Python path for background threads
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
import threading
import time
import markdown2
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__,
            template_folder='templates',
            static_folder='../static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', '../database/nexus.db')
app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'

# Global workflow storage (in production: use Redis or DB)
workflow_storage = {}


@app.route('/')
def index():
    """Startseite mit 3 Kacheln"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health Check Endpoint"""
    return {'status': 'ok', 'version': '2.0.0'}


# ========================================
# PROJEKT ROUTES (Kacheln)
# ========================================

@app.route('/projekt/neu', methods=['GET', 'POST'])
def projekt_neu():
    """Kachel 1: Neues Projekt erstellen (Phase 2)"""
    if request.method == 'POST':
        # Formular-Daten holen
        projektname = request.form.get('projektname', '').strip()
        projektplan = request.form.get('projektplan', '').strip()

        # Validierung
        if not projektname:
            flash('Bitte gib einen Projektnamen ein.', 'error')
            return render_template('projekt_neu.html',
                                 projektname=projektname,
                                 projektplan=projektplan)

        if not projektplan:
            flash('Bitte beschreibe deinen Projektplan.', 'error')
            return render_template('projekt_neu.html',
                                 projektname=projektname,
                                 projektplan=projektplan)

        # Daten in Session speichern für Multi-Agent Workflow
        session['projektname'] = projektname
        session['projektplan'] = projektplan

        # Weiterleitung zum Live-Tracker (Auftrag 2.2)
        return redirect(url_for('projekt_tracker'))

    # GET: Formular anzeigen
    return render_template('projekt_neu.html')


def run_workflow_background(workflow_id, projektname, projektplan):
    """Run workflow in background thread"""
    import logging
    import sys
    import os

    # CRITICAL: Set sys.path for this thread BEFORE importing
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Thread gestartet für Workflow {workflow_id}")
        logger.info(f"Project root in sys.path: {project_root}")

        # Import AFTER setting sys.path
        from app.services.multi_agent import MultiAgentWorkflow

        logger.info("MultiAgentWorkflow imported successfully")

        workflow = MultiAgentWorkflow()
        workflow_storage[workflow_id] = workflow

        logger.info(f"Starte Workflow für: {projektname}")
        result = workflow.run(projektname, projektplan)

        workflow_storage[workflow_id] = workflow
        logger.info("Workflow abgeschlossen!")

    except Exception as e:
        logger.error(f"Workflow Fehler: {e}", exc_info=True)
        # Store error in a minimal status object
        workflow_storage[workflow_id] = {
            'status': 'error',
            'error': str(e),
            'current_step': 0,
            'steps': []
        }


@app.route('/projekt/tracker')
def projekt_tracker():
    """Live-Tracker für Multi-Agent Workflow (Auftrag 2.3)"""
    projektname = session.get('projektname', 'Unbenanntes Projekt')
    projektplan = session.get('projektplan', '')

    # Generate workflow ID
    workflow_id = f"{session.sid}_{int(time.time())}" if hasattr(session, 'sid') else f"workflow_{int(time.time())}"
    session['workflow_id'] = workflow_id

    # Check if workflow already running
    if workflow_id not in workflow_storage:
        # Start workflow in background
        thread = threading.Thread(
            target=run_workflow_background,
            args=(workflow_id, projektname, projektplan),
            daemon=True
        )
        thread.start()

    # Get current status
    if workflow_id in workflow_storage:
        workflow = workflow_storage[workflow_id]
        tracker_status = workflow.get_status()
        tracker_status['projektname'] = projektname
    else:
        # Initial status
        tracker_status = {
            'current_step': 1,
            'projektname': projektname,
            'steps': [
                {'nr': 1, 'name': 'Sonnet analysiert', 'icon': '🔍', 'ai': 'Sonnet 4.5', 'status': 'active'},
                {'nr': 2, 'name': 'Gemini Feedback', 'icon': '💭', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
                {'nr': 3, 'name': 'Enterprise-Plan', 'icon': '📋', 'ai': 'Sonnet 4.5', 'status': 'waiting'},
                {'nr': 4, 'name': 'Qualitätsprüfung', 'icon': '🔎', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
                {'nr': 5, 'name': 'Verbesserung', 'icon': '✨', 'ai': 'Sonnet 4.5', 'status': 'waiting'},
                {'nr': 6, 'name': 'Finale Bewertung', 'icon': '⭐', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
            ]
        }

    return render_template('projekt_tracker.html', tracker=tracker_status)


@app.route('/projekt/tracker/status')
def projekt_tracker_status():
    """HTMX endpoint for live status updates (Progress Bar + Steps)"""
    workflow_id = session.get('workflow_id')

    if not workflow_id or workflow_id not in workflow_storage:
        return '''
        <div class="progress-section">
            <div class="progress-label">
                <span class="progress-text">Phase 0 von 6</span>
                <span class="progress-percentage">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%">
                    <div class="progress-glow"></div>
                </div>
            </div>
        </div>
        <div class="steps-container">
            <p>Workflow lädt...</p>
        </div>
        '''

    workflow = workflow_storage[workflow_id]
    status = workflow.get_status()

    # Calculate progress
    current_step = status.get('current_step', 0)
    progress_percent = int((current_step / 6) * 100)

    # Check if complete
    if status.get('status') == 'complete':
        return '<script>window.location.href="/projekt/ergebnis";</script>'

    # Build Progress Bar HTML
    html = f'''
    <div class="progress-section">
        <div class="progress-label">
            <span class="progress-text">Phase {current_step} von 6</span>
            <span class="progress-percentage">{progress_percent}%</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_percent}%">
                <div class="progress-glow"></div>
            </div>
        </div>
    </div>
    '''

    # Build Steps HTML
    html += '<div class="steps-container">'

    for step in status['steps']:
        status_class = f'step-{step["status"]}'
        html += f'<div class="step-item {status_class}">'
        html += '<div class="step-indicator">'

        if step['status'] == 'waiting':
            html += '<span class="step-dot step-dot-waiting">○</span>'
        elif step['status'] == 'active':
            html += '<span class="step-dot step-dot-active">●</span>'
        elif step['status'] == 'done':
            html += '<span class="step-dot step-dot-done">✓</span>'
        elif step['status'] == 'error':
            html += '<span class="step-dot step-dot-error">✗</span>'

        html += '</div><div class="step-content"><div class="step-header">'
        html += f'<span class="step-icon">{step["icon"]}</span>'
        html += f'<span class="step-number">[{step["nr"]}]</span>'
        html += f'<span class="step-name">{step["name"]}</span>'

        if step['status'] == 'active':
            html += '<span class="step-badge">← AKTIV</span>'

        html += f'</div><div class="step-ai">{step["ai"]}</div></div></div>'

    html += '</div>'
    return html


@app.route('/projekt/ergebnis')
def projekt_ergebnis():
    """Ergebnis-Anzeige nach Workflow-Ende (Auftrag 2.4)"""
    workflow_id = session.get('workflow_id')

    # Get workflow results
    if workflow_id and workflow_id in workflow_storage:
        workflow = workflow_storage[workflow_id]
        status = workflow.get_status()

        enterprise_plan = status.get('final_plan', 'Plan wird noch erstellt...')
        bewertung = status.get('bewertung', 'Bewertung ausstehend...')
    else:
        # Fallback from session
        enterprise_plan = session.get('enterprise_plan', 'Kein Plan verfügbar')
        bewertung = session.get('bewertung', 'Keine Bewertung verfügbar')

    # Render markdown
    plan_html = markdown2.markdown(enterprise_plan, extras=['fenced-code-blocks', 'tables', 'header-ids'])

    # Parse bewertung score
    score = parse_bewertung_score(bewertung)

    projektname = session.get('projektname', 'Unbenanntes Projekt')

    return render_template('projekt_ergebnis.html',
                          projektname=projektname,
                          plan_html=plan_html,
                          bewertung=bewertung,
                          score=score)


def parse_bewertung_score(bewertung_text):
    """Extract score from bewertung text (e.g., '8/10' or '8 Sterne')"""
    match = re.search(r'(\d+)\s*/\s*10|(\d+)\s*[Ss]tern', bewertung_text)
    if match:
        score = int(match.group(1) or match.group(2))
        return min(10, max(0, score))
    return 5  # Default


@app.route('/projekt/speichern', methods=['POST'])
def projekt_speichern():
    """Projekt in Datenbank speichern (Auftrag 2.5)"""
    from app.services.database import save_projekt

    workflow_id = session.get('workflow_id')

    # Get data from workflow
    if workflow_id and workflow_id in workflow_storage:
        workflow = workflow_storage[workflow_id]
        status = workflow.get_status()

        enterprise_plan = status.get('final_plan', '')
        bewertung = status.get('bewertung', '')
    else:
        # Fallback from session
        enterprise_plan = session.get('enterprise_plan', '')
        bewertung = session.get('bewertung', '')

    # Get original data from session
    projektname = session.get('projektname', 'Unbenanntes Projekt')
    projektplan = session.get('projektplan', '')

    # Save to database
    try:
        projekt_id = save_projekt(
            name=projektname,
            original_plan=projektplan,
            enterprise_plan=enterprise_plan,
            bewertung=bewertung
        )

        # Store projekt_id in session for next phases
        session['projekt_id'] = projekt_id

        # Clean up workflow from memory
        if workflow_id and workflow_id in workflow_storage:
            del workflow_storage[workflow_id]

        # Clean up workflow_id from session (keep projekt data)
        session.pop('workflow_id', None)

        flash(f'✅ Projekt "{projektname}" erfolgreich gespeichert!', 'success')

        # Redirect to Kachel 2: Phasen & Aufträge (with projekt_id)
        return redirect(url_for('projekt_phasen_view', projekt_id=projekt_id))

    except Exception as e:
        flash(f'❌ Fehler beim Speichern: {str(e)}', 'error')
        return redirect(url_for('projekt_ergebnis'))


@app.route('/projekt/<int:projekt_id>/phasen', methods=['GET', 'POST'])
def projekt_phasen_view(projekt_id):
    """Kachel 2: Phasen & Aufträge generieren (Phase 3)"""
    from app.services.database import get_projekt
    from app.services.phasen_generator import generate_phasen
    import threading

    # Projekt aus Datenbank laden
    projekt = get_projekt(projekt_id)

    if not projekt:
        flash('❌ Projekt nicht gefunden', 'error')
        return redirect(url_for('index'))

    # POST: Phasen generieren starten
    if request.method == 'POST':
        enterprise_plan = projekt['enterprise_plan']

        try:
            # Gemini aufrufen (könnte lange dauern)
            phasen_data = generate_phasen(enterprise_plan)

            # In Session speichern für Auftrag 3.2
            session['phasen_data'] = phasen_data
            session['projekt_id'] = projekt_id

            flash('✅ Phasen erfolgreich generiert!', 'success')
            return redirect(url_for('projekt_phasen_ergebnis', projekt_id=projekt_id))

        except Exception as e:
            flash(f'❌ Fehler bei Phasen-Generierung: {str(e)}', 'error')
            return redirect(url_for('projekt_phasen_view', projekt_id=projekt_id))

    # GET: Formular anzeigen
    return render_template('projekt_phasen.html', projekt=projekt)


@app.route('/projekt/<int:projekt_id>/phasen/ergebnis')
def projekt_phasen_ergebnis(projekt_id):
    """Zeigt generierte Phasen an (Auftrag 3.1)"""
    from app.services.database import get_projekt
    from app.services.phasen_generator import format_phasen_for_display

    projekt = get_projekt(projekt_id)
    phasen_data = session.get('phasen_data')

    if not phasen_data:
        flash('❌ Keine Phasen gefunden. Bitte erst generieren.', 'error')
        return redirect(url_for('projekt_phasen_view', projekt_id=projekt_id))

    # Formatiere für Anzeige
    phasen_markdown = format_phasen_for_display(phasen_data)
    phasen_html = markdown2.markdown(phasen_markdown, extras=['fenced-code-blocks', 'tables'])

    return render_template('projekt_phasen_ergebnis.html',
                          projekt=projekt,
                          phasen_data=phasen_data,
                          phasen_html=phasen_html)


@app.route('/projekt/phasen')
def projekt_phasen():
    """Legacy route - redirect to projekt with ID from session"""
    projekt_id = session.get('projekt_id')
    if projekt_id:
        return redirect(url_for('projekt_phasen_view', projekt_id=projekt_id))
    else:
        flash('❌ Kein aktives Projekt gefunden', 'error')
        return redirect(url_for('index'))


@app.route('/projekt/<int:projekt_id>/auftraege/generieren', methods=['POST'])
def auftraege_generieren(projekt_id):
    """Generiert Aufträge mit Sonnet 4.5 (Auftrag 3.2)"""
    from app.services.database import get_projekt
    from app.services.auftraege_generator import generate_auftraege

    projekt = get_projekt(projekt_id)
    phasen_data = session.get('phasen_data')

    if not projekt:
        flash('❌ Projekt nicht gefunden', 'error')
        return redirect(url_for('index'))

    if not phasen_data:
        flash('❌ Erst Phasen generieren!', 'error')
        return redirect(url_for('projekt_phasen_view', projekt_id=projekt_id))

    try:
        # Sonnet aufrufen (kann lange dauern)
        auftraege_data = generate_auftraege(phasen_data, projekt['enterprise_plan'])

        # In Session speichern für Auftrag 3.3
        session['auftraege_data'] = auftraege_data
        session['projekt_id'] = projekt_id

        flash('✅ Aufträge erfolgreich generiert!', 'success')
        return redirect(url_for('auftraege_anzeigen', projekt_id=projekt_id))

    except Exception as e:
        flash(f'❌ Fehler bei Auftrags-Generierung: {str(e)}', 'error')
        return redirect(url_for('projekt_phasen_ergebnis', projekt_id=projekt_id))


@app.route('/projekt/<int:projekt_id>/auftraege')
def auftraege_anzeigen(projekt_id):
    """Zeigt generierte Aufträge an (Auftrag 3.2)"""
    from app.services.database import get_projekt

    projekt = get_projekt(projekt_id)
    auftraege_data = session.get('auftraege_data')
    phasen_data = session.get('phasen_data')

    if not auftraege_data:
        flash('❌ Keine Aufträge gefunden. Bitte erst generieren.', 'error')
        return redirect(url_for('projekt_phasen_ergebnis', projekt_id=projekt_id))

    # Gruppiere Aufträge nach Phase
    auftraege_by_phase = {}
    for auftrag in auftraege_data['auftraege']:
        phase_nr = auftrag['phase_nummer']
        if phase_nr not in auftraege_by_phase:
            auftraege_by_phase[phase_nr] = []
        auftraege_by_phase[phase_nr].append(auftrag)

    # Phasen-Namen hinzufügen (aus phasen_data)
    phasen_namen = {}
    if phasen_data and 'phasen' in phasen_data:
        for phase in phasen_data['phasen']:
            phasen_namen[phase['nummer']] = phase['name']

    return render_template('projekt_auftraege.html',
                          projekt=projekt,
                          auftraege_data=auftraege_data,
                          auftraege_by_phase=auftraege_by_phase,
                          phasen_namen=phasen_namen)


@app.route('/projekt/<int:projekt_id>/auftraege/pruefen', methods=['POST'])
def auftraege_pruefen(projekt_id):
    """Prüft Aufträge mit Gemini 3 Pro (Auftrag 3.3)"""
    from app.services.database import get_projekt
    from app.services.qualitaetspruefung import pruefen_auftraege

    projekt = get_projekt(projekt_id)
    phasen_data = session.get('phasen_data')
    auftraege_data = session.get('auftraege_data')

    if not projekt:
        flash('❌ Projekt nicht gefunden', 'error')
        return redirect(url_for('index'))

    if not phasen_data or not auftraege_data:
        flash('❌ Erst Phasen und Aufträge generieren!', 'error')
        return redirect(url_for('projekt_phasen_view', projekt_id=projekt_id))

    try:
        # Gemini aufrufen (kann lange dauern)
        qualitaet_data = pruefen_auftraege(auftraege_data, phasen_data, projekt['enterprise_plan'])

        # In Session speichern für Auftrag 3.4
        session['qualitaet_data'] = qualitaet_data
        session['projekt_id'] = projekt_id

        flash('✅ Qualitätsprüfung abgeschlossen!', 'success')
        return redirect(url_for('qualitaet_anzeigen', projekt_id=projekt_id))

    except Exception as e:
        flash(f'❌ Fehler bei Qualitätsprüfung: {str(e)}', 'error')
        return redirect(url_for('auftraege_anzeigen', projekt_id=projekt_id))


@app.route('/projekt/<int:projekt_id>/auftraege/qualitaet')
def qualitaet_anzeigen(projekt_id):
    """Zeigt Qualitäts-Bewertung an (Auftrag 3.3)"""
    from app.services.database import get_projekt
    from app.services.qualitaetspruefung import get_status_icon, get_status_color

    projekt = get_projekt(projekt_id)
    qualitaet_data = session.get('qualitaet_data')

    if not qualitaet_data:
        flash('❌ Keine Qualitätsprüfung gefunden. Bitte erst prüfen.', 'error')
        return redirect(url_for('auftraege_anzeigen', projekt_id=projekt_id))

    # Icons und Farben für Template hinzufügen
    for kategorie in qualitaet_data['kategorien']:
        kategorie['icon'] = get_status_icon(kategorie['status'])
        kategorie['color_class'] = get_status_color(kategorie['status'])

    return render_template('projekt_qualitaet.html',
                          projekt=projekt,
                          qualitaet=qualitaet_data)


@app.route('/projekt/<int:projekt_id>/abschliessen', methods=['POST'])
def projekt_abschliessen(projekt_id):
    """
    Speichert alle generierten Daten in DB und schließt Phase 3 ab (Auftrag 3.4)
    """
    from app.services.database import save_phasen, save_auftraege, update_projekt_qualitaet

    # Daten aus Session holen
    phasen_data = session.get('phasen_data')
    auftraege_data = session.get('auftraege_data')
    qualitaet_data = session.get('qualitaet_data')

    if not phasen_data or not auftraege_data or not qualitaet_data:
        flash('❌ Nicht alle Daten vorhanden. Bitte Workflow komplett durchlaufen.', 'error')
        return redirect(url_for('index'))

    try:
        # 1. Phasen speichern
        phase_ids = save_phasen(projekt_id, phasen_data)

        # 2. Aufträge pro Phase speichern
        for phase_nr, phase_id in phase_ids:
            phase_auftraege = [a for a in auftraege_data.get('auftraege', [])
                              if a['phase_nummer'] == phase_nr]
            if phase_auftraege:
                save_auftraege(phase_id, phase_auftraege)

        # 3. Qualität speichern und Status auf "bereit" setzen
        update_projekt_qualitaet(projekt_id, qualitaet_data)

        # 4. Session aufräumen
        session.pop('phasen_data', None)
        session.pop('auftraege_data', None)
        session.pop('qualitaet_data', None)
        session.pop('projekt_id', None)

        flash('✅ Projekt erfolgreich gespeichert! Status: BEREIT', 'success')
        return redirect(url_for('projekt_uebersicht', projekt_id=projekt_id))

    except Exception as e:
        flash(f'❌ Fehler beim Speichern: {str(e)}', 'error')
        return redirect(url_for('qualitaet_anzeigen', projekt_id=projekt_id))


@app.route('/projekt/<int:projekt_id>')
def projekt_uebersicht(projekt_id):
    """
    Zeigt komplette Projekt-Übersicht mit allen Phasen und Aufträgen (Auftrag 3.4)
    """
    from app.services.database import get_projekt_komplett

    projekt = get_projekt_komplett(projekt_id)

    if not projekt:
        flash('❌ Projekt nicht gefunden.', 'error')
        return redirect(url_for('index'))

    return render_template('projekt_uebersicht.html', projekt=projekt)


@app.route('/projekt/liste')
def projekt_liste():
    """Kachel 3: Projekt öffnen und steuern (Phase 4)"""
    from app.services.database import get_all_projekte
    projekte = get_all_projekte()
    return render_template('projekt_liste.html', projekte=projekte)


@app.route('/projekt/<int:projekt_id>/steuern')
def projekt_steuern(projekt_id):
    """
    Kachel 3: Projekt steuern - Hauptarbeitsbereich (Auftrag 4.1)
    Layout mit Sidebar (Projekte + Phasen) und Chat-Bereich
    """
    from app.services.database import get_all_projekte, get_projekt_komplett

    # Alle Projekte für Sidebar laden
    projekte = get_all_projekte()

    # Aktuelles Projekt mit Phasen und Aufträgen laden
    projekt = get_projekt_komplett(projekt_id)

    if not projekt:
        flash('❌ Projekt nicht gefunden', 'error')
        return redirect(url_for('projekt_liste'))

    # Aktuelle Phase ermitteln (erste nicht-fertige Phase oder letzte)
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


@app.route('/projekt/<int:projekt_id>/auftrag', methods=['POST'])
def projekt_auftrag(projekt_id):
    """
    Holt nächsten offenen Auftrag und formatiert ihn für Claude Code (Auftrag 4.2)
    Wird per HTMX aufgerufen, gibt HTML für Chat-Container zurück
    """
    from app.services.database import get_projekt, get_next_open_auftrag, update_auftrag_status
    from app.services.auftrag_formatierer import format_auftrag_for_claude, get_no_auftraege_message

    # Projekt laden
    projekt = get_projekt(projekt_id)
    if not projekt:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Projekt nicht gefunden.')

    # Nächsten offenen Auftrag finden
    auftrag = get_next_open_auftrag(projekt_id)

    if not auftrag:
        # Keine offenen Aufträge
        return render_template('partials/chat_message.html',
                             message_type='info',
                             content=get_no_auftraege_message())

    # Auftrag formatieren (ohne AI für Schnelligkeit, AI kann später aktiviert werden)
    formatted_auftrag = format_auftrag_for_claude(auftrag, projekt)

    # Status auf "in_arbeit" setzen
    update_auftrag_status(auftrag['id'], 'in_arbeit')

    # Als Chat-Nachricht zurückgeben
    return render_template('partials/chat_message.html',
                         message_type='auftrag',
                         auftrag_name=f"{auftrag.get('phase_nummer', 1)}.{auftrag.get('nummer', 1)} - {auftrag.get('name', 'Auftrag')}",
                         content=formatted_auftrag,
                         auftrag_id=auftrag['id'])


@app.route('/projekt/<int:projekt_id>/auftrag/<int:auftrag_id>/status', methods=['POST'])
def auftrag_status_update(projekt_id, auftrag_id):
    """
    Aktualisiert den Status eines Auftrags (Auftrag 4.2)
    """
    from app.services.database import update_auftrag_status

    status = request.form.get('status', 'fertig')

    if status not in ['offen', 'in_arbeit', 'fertig', 'fehler']:
        return jsonify({'success': False, 'error': 'Ungültiger Status'}), 400

    success = update_auftrag_status(auftrag_id, status)

    if success:
        return jsonify({'success': True, 'status': status})
    else:
        return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404


@app.route('/projekt/<int:projekt_id>/fehler', methods=['POST'])
def projekt_fehler(projekt_id):
    """
    Analysiert einen Fehler und gibt Lösung zurück (Auftrag 4.3)
    Prüft DB nach bekannten Fehlern, sonst KI-Analyse
    """
    from app.services.database import get_projekt
    from app.services.fehler_analyzer import analyze_fehler

    # Projekt laden
    projekt = get_projekt(projekt_id)
    if not projekt:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Projekt nicht gefunden.')

    # Fehler-Text aus Request
    fehler_text = request.form.get('fehler_text', '').strip()

    if not fehler_text:
        return render_template('partials/chat_message.html',
                             message_type='error',
                             content='Bitte gib einen Fehler-Text ein.')

    # Fehler analysieren
    result = analyze_fehler(fehler_text, projekt.get('name', 'NEXUS OVERLORD'))

    # Als Chat-Nachricht zurückgeben
    return render_template('partials/fehler_response.html',
                         bekannt=result['bekannt'],
                         kategorie=result['kategorie'],
                         ursache=result['ursache'],
                         loesung=result['loesung'],
                         auftrag=result['auftrag'],
                         fehler_id=result.get('fehler_id'),
                         erfolgsrate=result.get('erfolgsrate', 0),
                         anzahl=result.get('anzahl', 0))


@app.route('/projekt/<int:projekt_id>/fehler/<int:fehler_id>/feedback', methods=['POST'])
def fehler_feedback(projekt_id, fehler_id):
    """
    Feedback zur Fehler-Lösung (hat geholfen / hat nicht geholfen) (Auftrag 4.3)
    """
    from app.services.database import update_fehler_erfolgsrate

    erfolg = request.form.get('erfolg', 'true').lower() == 'true'
    update_fehler_erfolgsrate(fehler_id, erfolg)

    return jsonify({'success': True, 'message': 'Feedback gespeichert'})


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = app.config['DEBUG']

    print("=" * 60)
    print("NEXUS OVERLORD v2.0 - Starting...")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)
