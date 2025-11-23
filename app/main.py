"""
NEXUS OVERLORD v2.0 - Main Entry Point
Flask Web Application
"""

from flask import Flask, render_template
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

@app.route('/projekt/neu')
def projekt_neu():
    """Kachel 1: Neues Projekt erstellen (Phase 2)"""
    return render_template('projekt_neu.html')


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
