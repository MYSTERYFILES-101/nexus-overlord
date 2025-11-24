"""
NEXUS OVERLORD v2.0 - Main Entry Point
Flask Web Application
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from dotenv import load_dotenv
import threading
import time

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
    from app.services.multi_agent import MultiAgentWorkflow
    try:
        workflow = MultiAgentWorkflow()
        workflow_storage[workflow_id] = workflow
        result = workflow.run(projektname, projektplan)
        workflow_storage[workflow_id] = workflow
    except Exception as e:
        if workflow_id in workflow_storage:
            workflow_storage[workflow_id].status["error"] = str(e)


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
    """HTMX endpoint for live status updates"""
    workflow_id = session.get('workflow_id')

    if not workflow_id or workflow_id not in workflow_storage:
        return '<div class="steps-container">Workflow lädt...</div>'

    workflow = workflow_storage[workflow_id]
    status = workflow.get_status()

    # Render steps HTML
    html = '<div class="steps-container" hx-get="/projekt/tracker/status" hx-trigger="every 2s" hx-swap="outerHTML">'

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


@app.route('/projekt/phasen')
def projekt_phasen():
    """Kachel 2: Phasen & Aufträge generieren (Phase 3)"""
    return render_template('projekt_phasen.html')


@app.route('/projekt/liste')
def projekt_liste():
    """Kachel 3: Projekt öffnen und steuern (Phase 4)"""
    return render_template('projekt_liste.html')


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
