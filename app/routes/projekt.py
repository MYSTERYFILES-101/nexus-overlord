"""
NEXUS OVERLORD v2.0 - Projekt Routes

Kachel 1: Neues Projekt erstellen, Multi-Agent Workflow, Ergebnis anzeigen.
"""

import logging
import re
import threading
import time

import markdown2
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

# Logger
logger = logging.getLogger(__name__)

projekt_bp = Blueprint('projekt', __name__)

# Global workflow storage (in production: use Redis or DB)
workflow_storage = {}


def run_workflow_background(workflow_id: str, projektname: str, projektplan: str) -> None:
    """
    Fuehrt den Multi-Agent Workflow in einem Background-Thread aus.

    Args:
        workflow_id: Eindeutige ID fuer den Workflow
        projektname: Name des Projekts
        projektplan: User-Projektplan
    """
    import sys
    import os

    # CRITICAL: Set sys.path for this thread BEFORE importing
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        logger.info(f"Thread gestartet fuer Workflow {workflow_id}")

        # Import AFTER setting sys.path
        from app.services.multi_agent import MultiAgentWorkflow

        workflow = MultiAgentWorkflow()
        workflow_storage[workflow_id] = workflow

        logger.info(f"Starte Workflow fuer: {projektname}")
        workflow.run(projektname, projektplan)
        workflow_storage[workflow_id] = workflow

        logger.info("Workflow abgeschlossen!")

    except Exception as e:
        logger.error(f"Workflow Fehler: {e}", exc_info=True)
        workflow_storage[workflow_id] = {
            'status': 'error',
            'error': str(e),
            'current_step': 0,
            'steps': []
        }


def parse_bewertung_score(bewertung_text: str) -> int:
    """
    Extrahiert Score aus Bewertungstext (z.B. '8/10' oder '8 Sterne').

    Args:
        bewertung_text: Bewertungstext

    Returns:
        int: Score zwischen 0 und 10
    """
    match = re.search(r'(\d+)\s*/\s*10|(\d+)\s*[Ss]tern', bewertung_text)
    if match:
        score = int(match.group(1) or match.group(2))
        return min(10, max(0, score))
    return 5  # Default


@projekt_bp.route('/projekt/neu', methods=['GET', 'POST'])
def projekt_neu():
    """Kachel 1: Neues Projekt erstellen (Phase 2)."""
    if request.method == 'POST':
        projektname = request.form.get('projektname', '').strip()
        projektplan = request.form.get('projektplan', '').strip()

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

        # Daten in Session speichern
        session['projektname'] = projektname
        session['projektplan'] = projektplan

        return redirect(url_for('projekt.projekt_tracker'))

    return render_template('projekt_neu.html')


@projekt_bp.route('/projekt/upload-plan', methods=['POST'])
def upload_plan():
    """
    Upload eines PDF/DOCX Plans fuer Kachel 1.

    Extrahiert Text aus der Datei und gibt ihn zurueck.
    """
    from app.services.document_extractor import extract_text_from_file, is_supported_format

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Keine Datei hochgeladen'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Keine Datei ausgewaehlt'}), 400

    if not is_supported_format(file.filename):
        return jsonify({
            'success': False,
            'error': 'Nicht unterstuetztes Format. Erlaubt: PDF, DOCX, TXT, MD'
        }), 400

    # Text extrahieren
    text, error = extract_text_from_file(file, file.filename)

    if error:
        return jsonify({'success': False, 'error': error}), 400

    if not text.strip():
        return jsonify({
            'success': False,
            'error': 'Kein Text konnte aus der Datei extrahiert werden'
        }), 400

    return jsonify({
        'success': True,
        'text': text,
        'filename': file.filename,
        'chars': len(text)
    })


@projekt_bp.route('/projekt/tracker')
def projekt_tracker():
    """Live-Tracker fuer Multi-Agent Workflow (Auftrag 2.3)."""
    projektname = session.get('projektname', 'Unbenanntes Projekt')
    projektplan = session.get('projektplan', '')

    # Generate workflow ID
    workflow_id = f"workflow_{int(time.time())}"
    session['workflow_id'] = workflow_id

    # Start workflow in background if not running
    if workflow_id not in workflow_storage:
        thread = threading.Thread(
            target=run_workflow_background,
            args=(workflow_id, projektname, projektplan),
            daemon=True
        )
        thread.start()

    # Get current status
    if workflow_id in workflow_storage:
        workflow = workflow_storage[workflow_id]
        if hasattr(workflow, 'get_status'):
            tracker_status = workflow.get_status()
        else:
            tracker_status = workflow
        tracker_status['projektname'] = projektname
    else:
        tracker_status = {
            'current_step': 1,
            'projektname': projektname,
            'steps': [
                {'nr': 1, 'name': 'Opus analysiert', 'icon': '🔍', 'ai': 'Opus 4.5', 'status': 'active'},
                {'nr': 2, 'name': 'Gemini Feedback', 'icon': '💭', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
                {'nr': 3, 'name': 'Enterprise-Plan', 'icon': '📋', 'ai': 'Opus 4.5', 'status': 'waiting'},
                {'nr': 4, 'name': 'Qualitaetspruefung', 'icon': '🔎', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
                {'nr': 5, 'name': 'Verbesserung', 'icon': '✨', 'ai': 'Opus 4.5', 'status': 'waiting'},
                {'nr': 6, 'name': 'Finale Bewertung', 'icon': '⭐', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
            ]
        }

    return render_template('projekt_tracker.html', tracker=tracker_status)


@projekt_bp.route('/projekt/tracker/status')
def projekt_tracker_status():
    """HTMX endpoint for live status updates (Progress Bar + Steps)."""
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
            <p>Workflow laedt...</p>
        </div>
        '''

    workflow = workflow_storage[workflow_id]
    if hasattr(workflow, 'get_status'):
        status = workflow.get_status()
    else:
        status = workflow

    current_step = status.get('current_step', 0)
    progress_percent = int((current_step / 6) * 100)

    # Check if complete
    if status.get('status') == 'complete' or (current_step == 6 and status.get('final_plan')):
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

    for step in status.get('steps', []):
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


@projekt_bp.route('/projekt/ergebnis')
def projekt_ergebnis():
    """Ergebnis-Anzeige nach Workflow-Ende (Auftrag 2.4)."""
    workflow_id = session.get('workflow_id')

    if workflow_id and workflow_id in workflow_storage:
        workflow = workflow_storage[workflow_id]
        if hasattr(workflow, 'get_status'):
            status = workflow.get_status()
        else:
            status = workflow

        enterprise_plan = status.get('final_plan', 'Plan wird noch erstellt...')
        bewertung = status.get('bewertung', 'Bewertung ausstehend...')
    else:
        enterprise_plan = session.get('enterprise_plan', 'Kein Plan verfuegbar')
        bewertung = session.get('bewertung', 'Keine Bewertung verfuegbar')

    plan_html = markdown2.markdown(enterprise_plan, extras=['fenced-code-blocks', 'tables', 'header-ids'])
    score = parse_bewertung_score(bewertung)
    projektname = session.get('projektname', 'Unbenanntes Projekt')

    return render_template('projekt_ergebnis.html',
                          projektname=projektname,
                          plan_html=plan_html,
                          bewertung=bewertung,
                          score=score)


@projekt_bp.route('/projekt/speichern', methods=['POST'])
def projekt_speichern():
    """Projekt in Datenbank speichern (Auftrag 2.5)."""
    from app.services.database import save_projekt

    workflow_id = session.get('workflow_id')

    if workflow_id and workflow_id in workflow_storage:
        workflow = workflow_storage[workflow_id]
        if hasattr(workflow, 'get_status'):
            status = workflow.get_status()
        else:
            status = workflow

        enterprise_plan = status.get('final_plan', '')
        bewertung = status.get('bewertung', '')
    else:
        enterprise_plan = session.get('enterprise_plan', '')
        bewertung = session.get('bewertung', '')

    projektname = session.get('projektname', 'Unbenanntes Projekt')
    projektplan = session.get('projektplan', '')

    try:
        projekt_id = save_projekt(
            name=projektname,
            original_plan=projektplan,
            enterprise_plan=enterprise_plan,
            bewertung=bewertung
        )

        session['projekt_id'] = projekt_id

        # Clean up
        if workflow_id and workflow_id in workflow_storage:
            del workflow_storage[workflow_id]
        session.pop('workflow_id', None)

        flash(f'Projekt "{projektname}" erfolgreich gespeichert!', 'success')
        return redirect(url_for('phasen.projekt_phasen_view', projekt_id=projekt_id))

    except Exception as e:
        logger.error(f"Fehler beim Speichern: {e}")
        flash(f'Fehler beim Speichern: {str(e)}', 'error')
        return redirect(url_for('projekt.projekt_ergebnis'))


@projekt_bp.route('/projekt/<int:projekt_id>')
def projekt_uebersicht(projekt_id: int):
    """Zeigt komplette Projekt-Uebersicht mit allen Phasen und Auftraegen."""
    from app.services.database import get_projekt_komplett

    projekt = get_projekt_komplett(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden.', 'error')
        return redirect(url_for('home.index'))

    return render_template('projekt_uebersicht.html', projekt=projekt)


@projekt_bp.route('/projekt/liste')
def projekt_liste():
    """Kachel 3: Projekt oeffnen und steuern (Phase 4)."""
    from app.services.database import get_all_projekte

    projekte = get_all_projekte()
    return render_template('projekt_liste.html', projekte=projekte)


@projekt_bp.route('/projekt/<int:projekt_id>/export-pdf')
def export_pdf(projekt_id: int):
    """
    Exportiert Projekt-Dokumentation als PDF (Auftrag 6.1).

    Args:
        projekt_id: ID des Projekts

    Returns:
        PDF-Datei zum Download
    """
    from flask import Response
    from app.services.database import get_projekt_komplett, get_fehler_stats
    from app.services.pdf_generator import NexusPDFGenerator

    logger.info(f"PDF-Export fuer Projekt {projekt_id}")

    # Komplettes Projekt mit Phasen und Auftraegen laden
    projekt = get_projekt_komplett(projekt_id)
    if not projekt:
        flash('Projekt nicht gefunden.', 'error')
        return redirect(url_for('home.index'))

    # Phasen aus Projekt extrahieren
    phasen = projekt.get('phasen', [])

    # PDF Generator initialisieren
    pdf = NexusPDFGenerator(f"{projekt['name']} - Dokumentation")

    # Titelseite
    pdf.add_title_page(
        projekt_name=projekt['name'],
        beschreibung=projekt.get('beschreibung', '')[:200] if projekt.get('beschreibung') else '',
        status=projekt.get('status', 'Aktiv'),
        version="2.0"
    )

    # Inhaltsverzeichnis
    toc_entries = [
        ("1. Projektuebersicht", 1),
        ("2. Phasen & Auftraege", 1),
    ]
    for i, phase in enumerate(phasen, 1):
        toc_entries.append((f"   2.{i} {phase['name']}", 2))
    toc_entries.append(("3. Statistiken", 1))
    pdf.add_toc(toc_entries)

    # Kapitel 1: Projektuebersicht
    pdf.add_chapter("1. Projektuebersicht")
    pdf.add_paragraph(projekt.get('beschreibung', 'Keine Beschreibung verfuegbar.'))
    pdf.add_spacer()

    # Projekt-Info Tabelle
    pdf.add_table([
        ["Eigenschaft", "Wert"],
        ["Name", projekt['name']],
        ["Status", projekt.get('status', 'Aktiv')],
        ["Erstellt", projekt.get('created_at', 'Unbekannt')[:10] if projekt.get('created_at') else 'Unbekannt'],
        ["Phasen", str(len(phasen))],
    ], col_widths=[5, 10])

    # Kapitel 2: Phasen & Auftraege
    pdf.add_page_break()
    pdf.add_chapter("2. Phasen & Auftraege")

    for i, phase in enumerate(phasen, 1):
        pdf.add_section(f"2.{i} {phase['name']}")

        # Phase-Info
        if phase.get('beschreibung'):
            pdf.add_paragraph(phase['beschreibung'])

        # Status-Info
        status_text = f"Status: {phase.get('status', 'offen').upper()}"
        pdf.add_paragraph(f"<b>{status_text}</b>")

        # Auftraege als Tabelle
        auftraege = phase.get('auftraege', [])
        if auftraege:
            table_data = [["Nr.", "Name", "Status"]]
            for auftrag in auftraege:
                nr = f"{phase.get('nummer', i)}.{auftrag.get('nummer', '?')}"
                name = auftrag.get('name', 'Unbenannt')[:40]
                status = auftrag.get('status', 'offen')
                table_data.append([nr, name, status.upper()])

            pdf.add_table(table_data, col_widths=[2, 10, 3])
        else:
            pdf.add_paragraph("Keine Auftraege vorhanden.")

        pdf.add_spacer(0.5)

    # Kapitel 3: Statistiken
    pdf.add_page_break()
    pdf.add_chapter("3. Statistiken")

    # Fortschritt berechnen
    total_auftraege = sum(len(p.get('auftraege', [])) for p in phasen)
    fertige_auftraege = sum(
        len([a for a in p.get('auftraege', []) if a.get('status') == 'fertig'])
        for p in phasen
    )
    fortschritt = round((fertige_auftraege / total_auftraege * 100) if total_auftraege > 0 else 0)

    pdf.add_table([
        ["Metrik", "Wert"],
        ["Gesamtfortschritt", f"{fortschritt}%"],
        ["Phasen gesamt", str(len(phasen))],
        ["Auftraege gesamt", str(total_auftraege)],
        ["Auftraege fertig", str(fertige_auftraege)],
        ["Auftraege offen", str(total_auftraege - fertige_auftraege)],
    ], col_widths=[6, 6])

    # PDF generieren
    pdf_bytes = pdf.build()

    # Als Download zurueckgeben
    filename = f"{projekt['name'].replace(' ', '_')}_Dokumentation.pdf"

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(pdf_bytes))
        }
    )


@projekt_bp.route('/test-pdf')
def test_pdf():
    """
    Generiert ein Test-PDF zur Ueberpruefung des Generators.

    Returns:
        Test-PDF zum Download
    """
    from flask import Response
    from app.services.pdf_generator import create_test_pdf

    logger.info("Generiere Test-PDF")

    pdf_bytes = create_test_pdf()

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': 'attachment; filename="NEXUS_Test_PDF.pdf"',
            'Content-Length': str(len(pdf_bytes))
        }
    )
