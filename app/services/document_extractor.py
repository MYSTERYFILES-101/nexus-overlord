"""
NEXUS OVERLORD v2.0 - Document Extractor

Extrahiert Text aus PDF- und DOCX-Dateien fuer Projekt-Upload.
"""

import logging
import os
from typing import Any

# Logger konfigurieren
logger = logging.getLogger(__name__)


def extract_text_from_file(file: Any, filename: str) -> tuple[str, str | None]:
    """
    Extrahiert Text aus einer hochgeladenen Datei.

    Unterstuetzte Formate:
        - PDF (.pdf)
        - Word (.docx, .doc)
        - Text (.txt, .md)

    Args:
        file: Werkzeug FileStorage Objekt
        filename: Original-Dateiname

    Returns:
        tuple: (extrahierter_text, fehler_nachricht oder None)
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    try:
        if ext == 'pdf':
            return extract_pdf_text(file)
        elif ext in ['docx', 'doc']:
            return extract_docx_text(file)
        elif ext in ['txt', 'md']:
            return extract_txt_text(file)
        else:
            return '', f'Nicht unterstuetztes Format: .{ext}'

    except Exception as e:
        logger.error(f"Fehler beim Extrahieren aus {filename}: {e}")
        return '', f'Fehler beim Extrahieren: {str(e)}'


def extract_pdf_text(file: Any) -> tuple[str, str | None]:
    """
    Extrahiert Text aus einer PDF-Datei.

    Args:
        file: FileStorage Objekt

    Returns:
        tuple: (text, fehler oder None)
    """
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber nicht installiert")
        return '', 'PDF-Extraktion nicht verfuegbar (pdfplumber fehlt)'

    try:
        text_parts = []

        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        text = '\n\n'.join(text_parts)

        if not text.strip():
            return '', 'PDF enthaelt keinen extrahierbaren Text (evtl. gescanntes Dokument)'

        logger.info(f"PDF extrahiert: {len(text)} Zeichen aus {len(text_parts)} Seiten")
        return text, None

    except Exception as e:
        logger.error(f"PDF-Extraktion fehlgeschlagen: {e}")
        return '', f'PDF-Extraktion fehlgeschlagen: {str(e)}'


def extract_docx_text(file: Any) -> tuple[str, str | None]:
    """
    Extrahiert Text aus einer DOCX-Datei.

    Args:
        file: FileStorage Objekt

    Returns:
        tuple: (text, fehler oder None)
    """
    try:
        from docx import Document
    except ImportError:
        logger.warning("python-docx nicht installiert")
        return '', 'DOCX-Extraktion nicht verfuegbar (python-docx fehlt)'

    try:
        doc = Document(file)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = '\n\n'.join(paragraphs)

        if not text.strip():
            return '', 'DOCX enthaelt keinen extrahierbaren Text'

        logger.info(f"DOCX extrahiert: {len(text)} Zeichen aus {len(paragraphs)} Absaetzen")
        return text, None

    except Exception as e:
        logger.error(f"DOCX-Extraktion fehlgeschlagen: {e}")
        return '', f'DOCX-Extraktion fehlgeschlagen: {str(e)}'


def extract_txt_text(file: Any) -> tuple[str, str | None]:
    """
    Extrahiert Text aus einer TXT/MD-Datei.

    Args:
        file: FileStorage Objekt

    Returns:
        tuple: (text, fehler oder None)
    """
    try:
        # Versuche verschiedene Encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                file.seek(0)
                text = file.read().decode(encoding)
                logger.info(f"TXT extrahiert: {len(text)} Zeichen (Encoding: {encoding})")
                return text, None
            except UnicodeDecodeError:
                continue

        return '', 'Datei konnte nicht dekodiert werden (unbekanntes Encoding)'

    except Exception as e:
        logger.error(f"TXT-Extraktion fehlgeschlagen: {e}")
        return '', f'TXT-Extraktion fehlgeschlagen: {str(e)}'


def is_supported_format(filename: str) -> bool:
    """
    Prueft ob das Dateiformat fuer Textextraktion unterstuetzt wird.

    Args:
        filename: Dateiname

    Returns:
        bool: True wenn unterstuetzt
    """
    supported = {'pdf', 'docx', 'doc', 'txt', 'md'}
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in supported


def get_supported_formats() -> list[str]:
    """
    Gibt Liste der unterstuetzten Formate zurueck.

    Returns:
        list: Liste der Dateiendungen
    """
    return ['pdf', 'docx', 'doc', 'txt', 'md']
