"""
NEXUS OVERLORD v2.0 - Configuration Settings
"""

import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'database' / 'nexus.db'))

# API Keys
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

# KI Models (OpenRouter IDs)
# Gemini 3 Pro - Stratege, Überblick, Prüfung
GEMINI_MODEL = 'google/gemini-3-pro-preview'
# Claude Opus 4.5 - Detailarbeiter, Aufträge, Code (Upgrade von Sonnet)
OPUS_MODEL = 'anthropic/claude-opus-4-5-20251101'
# Alias für Abwärtskompatibilität
SONNET_MODEL = OPUS_MODEL

# Server
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Projekt-Ordner
PROJEKT_DIR = BASE_DIR / 'projekt'
AUFTRAEGE_DIR = PROJEKT_DIR / 'auftraege'
RUECKMELDUNGEN_DIR = PROJEKT_DIR / 'rueckmeldungen'
FEHLER_DIR = PROJEKT_DIR / 'fehler'
UEBERGABEN_DIR = PROJEKT_DIR / 'uebergaben'
