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

# KI Models
GEMINI_MODEL = 'google/gemini-3-pro-preview'
SONNET_MODEL = 'anthropic/claude-sonnet-4.5'

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
