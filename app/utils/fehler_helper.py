"""
NEXUS OVERLORD v2.0 - Fehler Helper

Hilfsfunktionen fuer Fehler-Kategorisierung, Severity-Erkennung und Tag-Extraktion.
"""

import re
import json
import logging
from typing import Any

# Logger
logger = logging.getLogger(__name__)

# ========================================
# KONSTANTEN
# ========================================

# Gueltige Kategorien
VALID_CATEGORIES = [
    "python",      # Python-Fehler (Import, Syntax, etc.)
    "npm",         # Node/npm Fehler
    "permission",  # Berechtigungsfehler
    "database",    # Datenbank-Fehler
    "network",     # Netzwerk/API-Fehler
    "dependency",  # Fehlende Dependencies
    "config",      # Konfigurationsfehler
    "git",         # Git-Fehler
    "docker",      # Docker-Fehler
    "other"        # Sonstige
]

# Gueltige Severity-Level
VALID_SEVERITIES = ["critical", "high", "medium", "low"]

# Gueltige Status-Werte
VALID_STATUSES = ["aktiv", "geloest", "veraltet"]


# ========================================
# KATEGORIE-ERKENNUNG
# ========================================

def detect_category(fehler_text: str) -> str:
    """
    Erkennt Fehler-Kategorie aus Text.

    Args:
        fehler_text: Fehlertext oder Stack-Trace

    Returns:
        str: Erkannte Kategorie (aus VALID_CATEGORIES)
    """
    if not fehler_text:
        return "other"

    fehler_lower = fehler_text.lower()

    # Python-Fehler
    python_patterns = [
        "modulenotfounderror", "importerror", "syntaxerror",
        "nameerror", "typeerror", "valueerror", "attributeerror",
        "keyerror", "indexerror", "zerodivisionerror",
        "traceback (most recent call last)", "python", ".py",
        "pip install", "pip3"
    ]
    if any(p in fehler_lower for p in python_patterns):
        return "python"

    # NPM/Node-Fehler
    npm_patterns = [
        "npm err", "npm warn", "node_modules", "package.json",
        "enoent", "npm install", "yarn", "node ", "javascript",
        "cannot find module", "require(", "export default"
    ]
    if any(p in fehler_lower for p in npm_patterns):
        return "npm"

    # Permission-Fehler
    permission_patterns = [
        "permission denied", "eacces", "access denied",
        "sudo", "root", "chmod", "chown", "forbidden",
        "not permitted", "operation not permitted"
    ]
    if any(p in fehler_lower for p in permission_patterns):
        return "permission"

    # Datenbank-Fehler
    database_patterns = [
        "sqlite", "mysql", "postgresql", "postgres", "mongodb",
        "database", "sql error", "query failed", "connection refused",
        "no such table", "syntax error in sql", "duplicate entry",
        "foreign key constraint", "unique constraint"
    ]
    if any(p in fehler_lower for p in database_patterns):
        return "database"

    # Netzwerk-Fehler
    network_patterns = [
        "connection", "timeout", "etimedout", "econnrefused",
        "network", "socket", "http error", "api", "fetch failed",
        "dns", "ssl", "certificate", "handshake", "unreachable"
    ]
    if any(p in fehler_lower for p in network_patterns):
        return "network"

    # Git-Fehler
    git_patterns = [
        "git ", "fatal:", "merge conflict", "rebase",
        "branch", "commit", "push rejected", "pull failed",
        "detached head", "checkout"
    ]
    if any(p in fehler_lower for p in git_patterns):
        return "git"

    # Docker-Fehler
    docker_patterns = [
        "docker", "container", "image", "dockerfile",
        "docker-compose", "kubernetes", "k8s", "pod"
    ]
    if any(p in fehler_lower for p in docker_patterns):
        return "docker"

    # Dependency-Fehler
    dependency_patterns = [
        "not found", "command not found", "missing",
        "no such file", "dependency", "unresolved",
        "could not find", "unable to locate"
    ]
    if any(p in fehler_lower for p in dependency_patterns):
        return "dependency"

    # Config-Fehler
    config_patterns = [
        "config", "settings", "environment", "env",
        ".env", "configuration", "invalid option",
        "unknown option", "missing required"
    ]
    if any(p in fehler_lower for p in config_patterns):
        return "config"

    return "other"


# ========================================
# SEVERITY-ERKENNUNG
# ========================================

def detect_severity(fehler_text: str, kategorie: str | None = None) -> str:
    """
    Erkennt Schweregrad aus Text und Kategorie.

    Args:
        fehler_text: Fehlertext
        kategorie: Optional - Bereits erkannte Kategorie

    Returns:
        str: Severity-Level (critical, high, medium, low)
    """
    if not fehler_text:
        return "medium"

    fehler_lower = fehler_text.lower()

    # Critical: Blockt System komplett
    critical_patterns = [
        "fatal", "crashed", "stopped", "killed", "panic",
        "system failure", "critical error", "abort",
        "segmentation fault", "core dumped", "out of memory",
        "disk full", "no space left"
    ]
    if any(p in fehler_lower for p in critical_patterns):
        return "critical"

    # High: Wichtige Funktion kaputt
    high_patterns = [
        "error", "failed", "exception", "cannot", "unable",
        "refused", "denied", "forbidden", "unauthorized"
    ]
    if kategorie in ["database", "network", "permission"]:
        return "high"
    if any(p in fehler_lower for p in high_patterns):
        return "high"

    # Medium: Feature betroffen aber System laeuft
    medium_patterns = [
        "warning", "warn", "deprecated", "missing",
        "not found", "invalid", "unknown"
    ]
    if kategorie in ["dependency", "config"]:
        return "medium"
    if any(p in fehler_lower for p in medium_patterns):
        return "medium"

    # Low: Nur kosmetisch oder informativ
    low_patterns = [
        "info", "notice", "hint", "suggestion",
        "consider", "recommend"
    ]
    if any(p in fehler_lower for p in low_patterns):
        return "low"

    return "medium"


# ========================================
# TAG-EXTRAKTION
# ========================================

def extract_tags(fehler_text: str, kategorie: str | None = None) -> list[str]:
    """
    Extrahiert relevante Tags aus Fehlertext.

    Args:
        fehler_text: Fehlertext
        kategorie: Optional - Bereits erkannte Kategorie

    Returns:
        list[str]: Liste relevanter Tags
    """
    if not fehler_text:
        return []

    tags = set()
    fehler_lower = fehler_text.lower()

    # Kategorie als Tag
    if kategorie and kategorie != "other":
        tags.add(kategorie)

    # Technologie-Tags
    tech_tags = {
        "python": ["python", ".py", "pip"],
        "javascript": ["javascript", ".js", "node"],
        "typescript": ["typescript", ".ts"],
        "flask": ["flask", "werkzeug"],
        "django": ["django"],
        "react": ["react", "jsx"],
        "vue": ["vue"],
        "sqlite": ["sqlite", "sqlite3"],
        "postgresql": ["postgresql", "postgres", "psql"],
        "mysql": ["mysql"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "docker": ["docker", "dockerfile"],
        "git": ["git ", "github", "gitlab"],
        "npm": ["npm", "yarn", "package.json"],
        "pip": ["pip install", "requirements.txt"],
        "api": ["api", "rest", "graphql"],
        "http": ["http", "https", "request"],
        "ssl": ["ssl", "certificate", "tls"],
        "auth": ["auth", "token", "jwt", "oauth"],
        "file": ["file", "directory", "path"],
        "memory": ["memory", "ram", "heap"],
        "cpu": ["cpu", "processor"],
        "disk": ["disk", "storage", "space"]
    }

    for tag, patterns in tech_tags.items():
        if any(p in fehler_lower for p in patterns):
            tags.add(tag)

    # Error-Type Tags aus Python Exceptions
    error_types = [
        "modulenotfounderror", "importerror", "syntaxerror",
        "nameerror", "typeerror", "valueerror", "attributeerror",
        "keyerror", "indexerror", "filenotfounderror", "oserror",
        "connectionerror", "timeouterror"
    ]
    for error_type in error_types:
        if error_type in fehler_lower:
            # Formatiere als lesbaren Tag (z.B. "import-error")
            readable = error_type.replace("error", "").replace("exception", "")
            if readable:
                tags.add(f"{readable}-error")

    # HTTP Status Codes
    http_codes = re.findall(r'\b(4\d{2}|5\d{2})\b', fehler_text)
    for code in http_codes:
        tags.add(f"http-{code}")

    # Limitiere auf max 10 Tags
    return sorted(list(tags))[:10]


# ========================================
# FIX-COMMAND ERKENNUNG
# ========================================

def detect_fix_command(fehler_text: str, kategorie: str | None = None) -> str | None:
    """
    Versucht einen Fix-Befehl aus dem Fehlertext zu erkennen.

    Args:
        fehler_text: Fehlertext
        kategorie: Optional - Bereits erkannte Kategorie

    Returns:
        str | None: Empfohlener Fix-Befehl oder None
    """
    if not fehler_text:
        return None

    fehler_lower = fehler_text.lower()

    # ModuleNotFoundError -> pip install
    module_match = re.search(r"modulenotfounderror: no module named ['\"]?(\w+)['\"]?", fehler_lower)
    if module_match:
        module_name = module_match.group(1)
        return f"pip install {module_name}"

    # npm module not found
    npm_match = re.search(r"cannot find module ['\"]?([^'\"]+)['\"]?", fehler_lower)
    if npm_match:
        module_name = npm_match.group(1)
        if not module_name.startswith(".") and not module_name.startswith("/"):
            return f"npm install {module_name}"

    # Permission denied -> chmod oder sudo
    if "permission denied" in fehler_lower:
        return "sudo chmod +x <file> oder sudo <command>"

    # Git push rejected
    if "push rejected" in fehler_lower or "non-fast-forward" in fehler_lower:
        return "git pull origin main --rebase && git push"

    # No space left
    if "no space left" in fehler_lower:
        return "df -h && sudo apt autoremove && sudo apt clean"

    return None


# ========================================
# VALIDIERUNG
# ========================================

def validate_category(kategorie: str) -> str:
    """
    Validiert und korrigiert Kategorie.

    Args:
        kategorie: Kategorie-String

    Returns:
        str: Gueltige Kategorie
    """
    if kategorie and kategorie.lower() in VALID_CATEGORIES:
        return kategorie.lower()
    return "other"


def validate_severity(severity: str) -> str:
    """
    Validiert und korrigiert Severity.

    Args:
        severity: Severity-String

    Returns:
        str: Gueltige Severity
    """
    if severity and severity.lower() in VALID_SEVERITIES:
        return severity.lower()
    return "medium"


def validate_status(status: str) -> str:
    """
    Validiert und korrigiert Status.

    Args:
        status: Status-String

    Returns:
        str: Gueltiger Status
    """
    if status and status.lower() in VALID_STATUSES:
        return status.lower()
    return "aktiv"


def tags_to_json(tags: list[str]) -> str:
    """
    Konvertiert Tag-Liste zu JSON-String.

    Args:
        tags: Liste von Tags

    Returns:
        str: JSON-Array als String
    """
    return json.dumps(tags if tags else [])


def json_to_tags(json_str: str) -> list[str]:
    """
    Konvertiert JSON-String zu Tag-Liste.

    Args:
        json_str: JSON-Array als String

    Returns:
        list[str]: Liste von Tags
    """
    try:
        tags = json.loads(json_str) if json_str else []
        return tags if isinstance(tags, list) else []
    except json.JSONDecodeError:
        return []


# ========================================
# VOLLSTAENDIGE FEHLER-ANALYSE
# ========================================

def analyze_fehler(fehler_text: str, projekt_id: int | None = None) -> dict[str, Any]:
    """
    Fuehrt vollstaendige Fehler-Analyse durch.

    Args:
        fehler_text: Fehlertext oder Stack-Trace
        projekt_id: Optional - Projekt-ID fuer Verknuepfung

    Returns:
        dict: Alle analysierten Fehler-Attribute
    """
    kategorie = detect_category(fehler_text)
    severity = detect_severity(fehler_text, kategorie)
    tags = extract_tags(fehler_text, kategorie)
    fix_command = detect_fix_command(fehler_text, kategorie)

    return {
        "projekt_id": projekt_id,
        "kategorie": kategorie,
        "severity": severity,
        "status": "aktiv",
        "tags": tags,
        "tags_json": tags_to_json(tags),
        "fix_command": fix_command,
        "stack_trace": fehler_text if len(fehler_text) > 200 else None
    }
