"""
NEXUS OVERLORD v2.0 - Main Entry Point
Flask Web Application
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from dotenv import load_dotenv

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


@app.route('/projekt/tracker')
def projekt_tracker():
    """Live-Tracker für Multi-Agent Workflow (Phase 2, Auftrag 2.2)"""
    # Projektname aus Session holen
    projektname = session.get('projektname', 'Unbenanntes Projekt')

    # Initial-Status für Tracker (wird in Auftrag 2.3 dynamisch)
    tracker_status = {
        'current_step': 1,
        'projektname': projektname,
        'steps': [
            {'nr': 1, 'name': 'Sonnet analysiert', 'icon': '🔍', 'ai': 'Sonnet 4.5', 'status': 'waiting'},
            {'nr': 2, 'name': 'Gemini Feedback', 'icon': '💭', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
            {'nr': 3, 'name': 'Enterprise-Plan', 'icon': '📋', 'ai': 'Sonnet 4.5', 'status': 'waiting'},
            {'nr': 4, 'name': 'Qualitätsprüfung', 'icon': '🔎', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
            {'nr': 5, 'name': 'Verbesserung', 'icon': '✨', 'ai': 'Sonnet 4.5', 'status': 'waiting'},
            {'nr': 6, 'name': 'Finale Bewertung', 'icon': '⭐', 'ai': 'Gemini 3 Pro', 'status': 'waiting'},
        ]
    }

    return render_template('projekt_tracker.html', tracker=tracker_status)


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
