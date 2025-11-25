"""
NEXUS OVERLORD v2.0 - AI Models Integration
Funktionen fuer Gemini 3 Pro und Claude Opus 4.5
"""

from app.services.openrouter import call_openrouter

# ========================================
# MODEL-IDs (OpenRouter)
# ========================================

# Gemini 3 Pro - Stratege, Ueberblick, Pruefung
MODEL_GEMINI = "google/gemini-3-pro-preview"

# Claude Opus 4.5 - Detailarbeiter, Auftraege, Code (Upgrade von Sonnet)
MODEL_OPUS = "anthropic/claude-opus-4-5-20251101"

# Alias fuer Abwaertskompatibilitaet
MODEL_SONNET = MODEL_OPUS


# ========================================
# GEMINI 3 PRO - Stratege
# ========================================

def call_gemini(prompt: str, system: str = None, max_tokens: int = 4000, temperature: float = 0.7):
    """
    Call Gemini 3 Pro via OpenRouter

    Verwendung:
    - Stratege und Ueberblick
    - Feedback geben
    - Qualitaetspruefung
    - Phasen-Einteilung
    - Kritisches Pruefen

    Args:
        prompt (str): User-Prompt
        system (str): System-Prompt (optional)
        max_tokens (int): Max Tokens (default: 4000)
        temperature (float): Kreativitaet 0.0-1.0 (default: 0.7)

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
# CLAUDE OPUS 4.5 - Detailarbeiter
# ========================================

def call_sonnet(prompt: str, system: str = None, max_tokens: int = 4000, temperature: float = 0.7):
    """
    Call Claude Opus 4.5 via OpenRouter

    Verwendung:
    - Detailarbeiter
    - Auftraege erstellen
    - Code-Analyse
    - Praezise Anweisungen
    - Loesungs-Auftraege

    Args:
        prompt (str): User-Prompt
        system (str): System-Prompt (optional)
        max_tokens (int): Max Tokens (default: 4000)
        temperature (float): Kreativitaet 0.0-1.0 (default: 0.7)

    Returns:
        str: Antwort von Claude Opus 4.5

    Example:
        >>> response = call_sonnet("Erstelle einen Auftrag fuer...")
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
    Gemini und Opus arbeiten zusammen

    Phase 1: Opus analysiert
    Phase 2: Gemini gibt Feedback
    Phase 3: Opus erstellt Enterprise-Plan
    Phase 4: Gemini prueft Qualitaet
    Phase 5: Opus verbessert
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
        system="Du bist ein kritischer Reviewer. Finde Luecken und Probleme."
    )

    # Phase 3: Sonnet erstellt Enterprise-Plan
    enterprise_plan = call_sonnet(
        prompt=f"Erstelle einen Enterprise-Plan basierend auf:\n\nOriginal: {user_plan}\n\nFeedback: {feedback}",
        system="Erstelle einen detaillierten Enterprise-Projektplan."
    )

    # Phase 4: Gemini prueft Qualitaet
    qualitaet = call_gemini(
        prompt=f"Pruefe die Qualitaet dieses Plans:\n\n{enterprise_plan}",
        system="Pruefe auf Vollstaendigkeit, Machbarkeit und Qualitaet."
    )

    # Phase 5: Sonnet verbessert (falls noetig)
    # TODO: Implementieren in spaeteren Phasen

    # Phase 6: Gemini finale Bewertung
    bewertung = call_gemini(
        prompt=f"Bewerte diesen finalen Plan (1-10) mit Begruendung:\n\n{enterprise_plan}",
        system="Gib eine objektive Bewertung von 1-10 mit Begruendung."
    )

    return {
        'enterprise_plan': enterprise_plan,
        'bewertung': bewertung,
        'analyse': analyse,
        'feedback': feedback,
        'qualitaet': qualitaet
    }
