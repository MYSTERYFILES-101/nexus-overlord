"""
NEXUS OVERLORD v2.0 - Database Service
SQLite Database Operations
"""

import sqlite3
from datetime import datetime
import os


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'nexus.db')


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_projekt(name, original_plan, enterprise_plan, bewertung):
    """
    Save project to database

    Args:
        name: Project name
        original_plan: User's original project plan
        enterprise_plan: Generated enterprise plan
        bewertung: AI evaluation

    Returns:
        int: project_id
    """
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO projekte (name, original_plan, enterprise_plan, bewertung, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'erstellt', ?, ?)
    """, (name, original_plan, enterprise_plan, bewertung, now, now))

    projekt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return projekt_id


def get_projekt(projekt_id):
    """
    Get project by ID

    Args:
        projekt_id: Project ID

    Returns:
        dict: Project data or None
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projekte WHERE id = ?", (projekt_id,))
    projekt = cursor.fetchone()
    conn.close()
    return dict(projekt) if projekt else None


def get_all_projekte():
    """Get all projects"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projekte ORDER BY created_at DESC")
    projekte = cursor.fetchall()
    conn.close()
    return [dict(p) for p in projekte]
