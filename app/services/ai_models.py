"""
NEXUS OVERLORD v2.0 - AI Models Integration
Funktionen für Gemini 3 Pro und Claude Sonnet 4.5
"""

from app.services.openrouter import call_openrouter

# ========================================
# MODEL-IDs (OpenRouter)
# ========================================

# Gemini 3 Pro - Stratege, Überblick, Prüfung
MODEL_GEMINI = "google/gemini-2.5-pro-preview-05-06"

# Claude Sonnet 4.5 - Detailarbeiter, Aufträge, Code
MODEL_SONNET = "anthropic/claude-sonnet-4-5-20250514"


# ========================================
# GEMINI 3 PRO - Stratege
# ========================================

def call_gemini(prompt: str, system: str = None, max_tokens: int = 4000, temperature: float = 0.7):
    """
    Call Gemini 3 Pro via OpenRouter

    Verwendung:
    - Stratege und Überblick
    - Feedback geben
    - Qualitätsprüfung
    - Phasen-Einteilung
    - Kritisches Prüfen

    Args:
        prompt (str): User-Prompt
        system (str): System-Prompt (optional)
        max_tokens (int): Max Tokens (default: 4000)
        temperature (float): Kreativität 0.0-1.0 (default: 0.7)

    Returns:
        str: Antwort von Gemini 3 Pro

    Example:
        >>> response = call_gemini("Analysiere diesen Projektplan...")
        >>> print(response)
    """
    messages = []

    # System message (falls vorhanden)
    if system:
        messages.append({"role": "system", "content": system})

    # User message
    messages.append({"role": "user", "content": prompt})

    # Call OpenRouter
    return call_openrouter(
        model=MODEL_GEMINI,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )


# ========================================
# CLAUDE SONNET 4.5 - Detailarbeiter
# ========================================

def call_sonnet(prompt: str, system: str = None, max_tokens: int = 4000, temperature: float = 0.7):
    """
    Call Claude Sonnet 4.5 via OpenRouter

    Verwendung:
    - Detailarbeiter
    - Aufträge erstellen
    - Code-Analyse
    - Präzise Anweisungen
    - Lösungs-Aufträge

    Args:
        prompt (str): User-Prompt
        system (str): System-Prompt (optional)
        max_tokens (int): Max Tokens (default: 4000)
        temperature (float): Kreativität 0.0-1.0 (default: 0.7)

    Returns:
        str: Antwort von Claude Sonnet 4.5

    Example:
        >>> response = call_sonnet("Erstelle einen Auftrag für...")
        >>> print(response)
    """
    messages = []

    # System message (falls vorhanden)
    if system:
        messages.append({"role": "system", "content": system})

    # User message
    messages.append({"role": "user", "content": prompt})

    # Call OpenRouter
    return call_openrouter(
        model=MODEL_SONNET,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )


# ========================================
# MULTI-AGENT WORKFLOW
# ========================================

def multi_agent_workflow(user_plan: str):
    """
    6-Phasen Multi-Agent Workflow
    Gemini und Sonnet arbeiten zusammen

    Phase 1: Sonnet analysiert
    Phase 2: Gemini gibt Feedback
    Phase 3: Sonnet erstellt Enterprise-Plan
    Phase 4: Gemini prüft Qualität
    Phase 5: Sonnet verbessert
    Phase 6: Gemini finale Bewertung

    Args:
        user_plan (str): User's Projektplan

    Returns:
        dict: {
            'enterprise_plan': str,
            'bewertung': str,
            'phases': list
        }
    """

    # Phase 1: Sonnet analysiert
    analyse = call_sonnet(
        prompt=f"Analysiere diesen Projektplan:\n\n{user_plan}",
        system="Du bist ein Enterprise-Architekt. Analysiere den Plan."
    )

    # Phase 2: Gemini gibt Feedback
    feedback = call_gemini(
        prompt=f"Gib Feedback zu dieser Analyse:\n\n{analyse}",
        system="Du bist ein kritischer Reviewer. Finde Lücken und Probleme."
    )

    # Phase 3: Sonnet erstellt Enterprise-Plan
    enterprise_plan = call_sonnet(
        prompt=f"Erstelle einen Enterprise-Plan basierend auf:\n\nOriginal: {user_plan}\n\nFeedback: {feedback}",
        system="Erstelle einen detaillierten Enterprise-Projektplan."
    )

    # Phase 4: Gemini prüft Qualität
    qualitaet = call_gemini(
        prompt=f"Prüfe die Qualität dieses Plans:\n\n{enterprise_plan}",
        system="Prüfe auf Vollständigkeit, Machbarkeit und Qualität."
    )

    # Phase 5: Sonnet verbessert (falls nötig)
    # TODO: Implementieren in späteren Phasen

    # Phase 6: Gemini finale Bewertung
    bewertung = call_gemini(
        prompt=f"Bewerte diesen finalen Plan (1-10) mit Begründung:\n\n{enterprise_plan}",
        system="Gib eine objektive Bewertung von 1-10 mit Begründung."
    )

    return {
        'enterprise_plan': enterprise_plan,
        'bewertung': bewertung,
        'analyse': analyse,
        'feedback': feedback,
        'qualitaet': qualitaet
    }
