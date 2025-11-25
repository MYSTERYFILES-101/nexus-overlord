"""
NEXUS OVERLORD v2.0 - JSON Extractor Utility

Extrahiert JSON-Objekte und -Arrays aus KI-Antworten.
Wird von phasen_generator, auftraege_generator und qualitaetspruefung genutzt.
"""

import json
import logging
import re
from typing import Any

# Logger konfigurieren
logger = logging.getLogger(__name__)


def extract_json(text: str, fallback: dict | None = None) -> dict:
    """
    Extrahiert ein JSON-Objekt aus einem Text.

    Versucht verschiedene Methoden, um JSON aus KI-Antworten zu extrahieren:
    1. Direkt als JSON parsen
    2. JSON aus Markdown Code-Bloecken extrahieren
    3. JSON-Objekt mit Regex finden

    Args:
        text: Text der JSON enthalten koennte
        fallback: Fallback-Dict falls kein JSON gefunden wird (Standard: {})

    Returns:
        dict: Das extrahierte JSON-Objekt oder fallback
    """
    if fallback is None:
        fallback = {}

    if not text or not text.strip():
        logger.warning("Leerer Text fuer JSON-Extraktion uebergeben")
        return fallback

    # 1. Versuche direkt zu parsen
    try:
        result = json.loads(text.strip())
        if isinstance(result, dict):
            logger.debug("JSON direkt geparst")
            return result
    except json.JSONDecodeError:
        pass

    # 2. Suche in Markdown Code-Bloecken
    code_block_patterns = [
        r'```json\s*\n?(.*?)\n?```',
        r'```\s*\n?(.*?)\n?```',
    ]

    for pattern in code_block_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                if isinstance(result, dict):
                    logger.debug("JSON aus Code-Block extrahiert")
                    return result
            except json.JSONDecodeError:
                continue

    # 3. Suche nach JSON-Objekt mit geschweiften Klammern
    # Finde das aeusserste Klammerpaar
    try:
        start = text.find('{')
        if start != -1:
            depth = 0
            end = start
            in_string = False
            escape_next = False

            for i, char in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            if end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
                if isinstance(result, dict):
                    logger.debug("JSON mit Klammer-Matching extrahiert")
                    return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.debug(f"Klammer-Matching fehlgeschlagen: {e}")

    # 4. Einfaches Regex als letzte Option
    try:
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, dict):
                logger.debug("JSON mit einfachem Regex extrahiert")
                return result
    except json.JSONDecodeError:
        pass

    logger.warning("Kein gueltiges JSON-Objekt gefunden, verwende Fallback")
    return fallback


def extract_json_array(text: str, fallback: list | None = None) -> list:
    """
    Extrahiert ein JSON-Array aus einem Text.

    Args:
        text: Text der JSON-Array enthalten koennte
        fallback: Fallback-Liste falls kein Array gefunden wird (Standard: [])

    Returns:
        list: Das extrahierte JSON-Array oder fallback
    """
    if fallback is None:
        fallback = []

    if not text or not text.strip():
        logger.warning("Leerer Text fuer JSON-Array-Extraktion uebergeben")
        return fallback

    # 1. Versuche direkt zu parsen
    try:
        result = json.loads(text.strip())
        if isinstance(result, list):
            logger.debug("JSON-Array direkt geparst")
            return result
    except json.JSONDecodeError:
        pass

    # 2. Suche in Markdown Code-Bloecken
    code_block_patterns = [
        r'```json\s*\n?(.*?)\n?```',
        r'```\s*\n?(.*?)\n?```',
    ]

    for pattern in code_block_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                if isinstance(result, list):
                    logger.debug("JSON-Array aus Code-Block extrahiert")
                    return result
            except json.JSONDecodeError:
                continue

    # 3. Suche nach JSON-Array mit eckigen Klammern
    try:
        start = text.find('[')
        if start != -1:
            depth = 0
            end = start
            in_string = False
            escape_next = False

            for i, char in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == '[':
                    depth += 1
                elif char == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            if end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
                if isinstance(result, list):
                    logger.debug("JSON-Array mit Klammer-Matching extrahiert")
                    return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.debug(f"Klammer-Matching fuer Array fehlgeschlagen: {e}")

    logger.warning("Kein gueltiges JSON-Array gefunden, verwende Fallback")
    return fallback


def sanitize_json_response(text: str) -> str:
    """
    Bereinigt einen Text fuer besseres JSON-Parsing.

    Entfernt Steuerzeichen und andere problematische Zeichen.

    Args:
        text: Zu bereinigender Text

    Returns:
        str: Bereinigter Text
    """
    # Entferne BOM und andere unsichtbare Zeichen am Anfang
    text = text.lstrip('\ufeff\u200b\u200c\u200d')

    # Ersetze problematische Whitespace-Zeichen
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Entferne Steuerzeichen (ausser \n und \t)
    text = ''.join(char for char in text if char == '\n' or char == '\t' or char >= ' ')

    return text.strip()
