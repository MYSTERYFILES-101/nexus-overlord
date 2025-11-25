"""
NEXUS OVERLORD v2.0 - Home Routes

Startseite und Health-Check.
"""

from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    """Startseite mit 3 Kacheln."""
    return render_template('index.html')


@home_bp.route('/health')
def health():
    """Health Check Endpoint."""
    return {'status': 'ok', 'version': '2.0.0'}
