"""
NEXUS OVERLORD v2.0 - Main Entry Point

Flask Web Application mit Blueprint-Architektur.
"""

import logging
import os
import sys

# Fix Python path for background threads
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Factory-Funktion für Flask-App.

    Returns:
        Flask: Die konfigurierte Flask-Anwendung
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='../static')

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', '../database/nexus.db')
    app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

    # Blueprints registrieren
    from app.routes import register_blueprints
    register_blueprints(app)

    logger.info("Flask-App initialisiert")
    return app


# App-Instanz erstellen
app = create_app()


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
