"""
NEXUS OVERLORD v2.0 - Routes Package

Blueprint-Registrierung fuer modulare Architektur.
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """
    Registriert alle Blueprints bei der Flask-App.

    Args:
        app: Die Flask-Anwendung
    """
    from .home import home_bp
    from .projekt import projekt_bp
    from .phasen import phasen_bp
    from .steuern import steuern_bp
    from .uebergaben import uebergaben_bp
    from .chat import chat_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(projekt_bp)
    app.register_blueprint(phasen_bp)
    app.register_blueprint(steuern_bp)
    app.register_blueprint(uebergaben_bp)
    app.register_blueprint(chat_bp)
