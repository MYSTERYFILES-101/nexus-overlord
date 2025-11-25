"""
NEXUS OVERLORD v2.0 - Multi-Agent Workflow

6-Phasen Enterprise-Plan Erstellung mit Opus 4.5 + Gemini 3 Pro.

Workflow:
    1. Opus 4.5 analysiert den User-Plan
    2. Gemini 3 Pro gibt Feedback zur Analyse
    3. Opus 4.5 erstellt Enterprise-Plan
    4. Gemini 3 Pro prüft Qualität
    5. Opus 4.5 verbessert den Plan
    6. Gemini 3 Pro bewertet final
"""

import logging
from typing import Any

from .openrouter import get_client, OpenRouterClient

# Logger konfigurieren
logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """
    6-Phasen Multi-Agent Workflow für Enterprise-Plan Erstellung.

    Der Workflow nutzt zwei KI-Modelle (Opus 4.5 + Gemini 3 Pro) in
    einem iterativen Prozess, um aus einem einfachen Projektplan
    einen vollständigen Enterprise-Plan zu erstellen.

    Attributes:
        client: OpenRouter API Client
        status: Aktueller Workflow-Status mit Schritten und Ergebnissen
    """

    def __init__(self):
        """Initialisiert den Multi-Agent Workflow."""
        self.client: OpenRouterClient = get_client()
        self.status: dict[str, Any] = {
            "current_step": 0,
            "steps": self._init_steps(),
            "results": {},
            "final_plan": None,
            "bewertung": None,
            "error": None
        }
        logger.info("Multi-Agent Workflow initialisiert")

    def _init_steps(self) -> list[dict[str, Any]]:
        """
        Initialisiert die Workflow-Schritte.

        Returns:
            list: Liste der Schritt-Definitionen
        """
        return [
            {"nr": 1, "name": "Opus analysiert", "icon": "🔍", "ai": "Opus 4.5", "status": "waiting", "result": None},
            {"nr": 2, "name": "Gemini Feedback", "icon": "💭", "ai": "Gemini 3 Pro", "status": "waiting", "result": None},
            {"nr": 3, "name": "Enterprise-Plan", "icon": "📋", "ai": "Opus 4.5", "status": "waiting", "result": None},
            {"nr": 4, "name": "Qualitätsprüfung", "icon": "🔎", "ai": "Gemini 3 Pro", "status": "waiting", "result": None},
            {"nr": 5, "name": "Verbesserung", "icon": "✨", "ai": "Opus 4.5", "status": "waiting", "result": None},
            {"nr": 6, "name": "Finale Bewertung", "icon": "⭐", "ai": "Gemini 3 Pro", "status": "waiting", "result": None},
        ]

    def _set_step_status(self, step_nr: int, status: str, result: str | None = None) -> None:
        """
        Aktualisiert den Status eines Schritts.

        Args:
            step_nr: Schritt-Nummer (1-6)
            status: Neuer Status ('waiting', 'active', 'done', 'error')
            result: Optionales Ergebnis des Schritts
        """
        self.status["current_step"] = step_nr

        for step in self.status["steps"]:
            if step["nr"] == step_nr:
                step["status"] = status
                if result:
                    step["result"] = result
                logger.debug(f"Schritt {step_nr} '{step['name']}': {status}")
                break

    def run(self, projektname: str, projektplan: str) -> dict[str, Any]:
        """
        Führt den kompletten 6-Phasen Workflow aus.

        Args:
            projektname: Name des Projekts
            projektplan: User-Projektplan als Text

        Returns:
            dict: Workflow-Status mit final_plan, bewertung und allen Zwischenergebnissen

        Raises:
            Exception: Bei Fehlern in einer der Phasen
        """
        logger.info(f"Starte Multi-Agent Workflow für Projekt: {projektname}")

        try:
            # Phase 1: Opus analysiert
            logger.info("Phase 1: Opus analysiert den Plan")
            self._set_step_status(1, "active")
            analyse = self._phase_1_analyse(projektplan)
            self._set_step_status(1, "done", analyse)
            self.status["results"]["analyse"] = analyse
            logger.info("Phase 1 abgeschlossen")

            # Phase 2: Gemini Feedback
            logger.info("Phase 2: Gemini gibt Feedback")
            self._set_step_status(2, "active")
            feedback = self._phase_2_feedback(projektplan, analyse)
            self._set_step_status(2, "done", feedback)
            self.status["results"]["feedback"] = feedback
            logger.info("Phase 2 abgeschlossen")

            # Phase 3: Enterprise-Plan erstellen
            logger.info("Phase 3: Opus erstellt Enterprise-Plan")
            self._set_step_status(3, "active")
            enterprise_plan = self._phase_3_enterprise_plan(projektplan, analyse, feedback)
            self._set_step_status(3, "done", enterprise_plan)
            self.status["results"]["enterprise_plan"] = enterprise_plan
            logger.info("Phase 3 abgeschlossen")

            # Phase 4: Qualitätsprüfung
            logger.info("Phase 4: Gemini prüft Qualität")
            self._set_step_status(4, "active")
            gepruefter_plan = self._phase_4_qualitaetspruefung(enterprise_plan)
            self._set_step_status(4, "done", gepruefter_plan)
            self.status["results"]["gepruefter_plan"] = gepruefter_plan
            logger.info("Phase 4 abgeschlossen")

            # Phase 5: Verbesserung
            logger.info("Phase 5: Opus verbessert den Plan")
            self._set_step_status(5, "active")
            verbesserter_plan = self._phase_5_verbesserung(gepruefter_plan, feedback)
            self._set_step_status(5, "done", verbesserter_plan)
            self.status["results"]["verbesserter_plan"] = verbesserter_plan
            logger.info("Phase 5 abgeschlossen")

            # Phase 6: Finale Bewertung
            logger.info("Phase 6: Gemini bewertet final")
            self._set_step_status(6, "active")
            bewertung = self._phase_6_bewertung(verbesserter_plan)
            self._set_step_status(6, "done", bewertung)
            self.status["results"]["bewertung"] = bewertung
            logger.info("Phase 6 abgeschlossen")

            # Finale Ergebnisse setzen
            self.status["final_plan"] = verbesserter_plan
            self.status["bewertung"] = bewertung
            self.status["current_step"] = 6

            logger.info(f"Multi-Agent Workflow erfolgreich abgeschlossen für: {projektname}")
            return self.status

        except Exception as e:
            # Fehler-Status setzen
            current = self.status["current_step"]
            error_msg = str(e)

            if current > 0:
                self._set_step_status(current, "error", error_msg)

            self.status["error"] = error_msg
            logger.error(f"Workflow fehlgeschlagen in Phase {current}: {error_msg}")
            raise

    def _phase_1_analyse(self, projektplan: str) -> str:
        """
        Phase 1: Opus analysiert den User-Plan.

        Args:
            projektplan: Der User-Projektplan

        Returns:
            str: Detaillierte Analyse des Plans
        """
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Senior Software-Architekt. Analysiere den folgenden Projektplan detailliert und strukturiert."
            },
            {
                "role": "user",
                "content": f"""Analysiere diesen Projektplan:

{projektplan}

Erstelle eine detaillierte Analyse mit:
1. Hauptziel des Projekts
2. Identifizierte Features
3. Technische Anforderungen
4. Potenzielle Herausforderungen
5. Empfohlene Technologie-Stack"""
            }
        ]

        return self.client.call_sonnet(messages, timeout=90)

    def _phase_2_feedback(self, projektplan: str, analyse: str) -> str:
        """
        Phase 2: Gemini gibt Feedback zur Analyse.

        Args:
            projektplan: Der ursprüngliche User-Plan
            analyse: Die Analyse aus Phase 1

        Returns:
            str: Konstruktives Feedback zur Analyse
        """
        messages = [
            {
                "role": "system",
                "content": "Du bist ein kritischer Reviewer. Gib konstruktives Feedback zur Projekt-Analyse."
            },
            {
                "role": "user",
                "content": f"""Ursprünglicher Projektplan:
{projektplan}

Analyse von Opus:
{analyse}

Gib kritisches aber konstruktives Feedback:
1. Was wurde gut analysiert?
2. Was fehlt in der Analyse?
3. Welche zusätzlichen Aspekte sollten berücksichtigt werden?
4. Gibt es Risiken die nicht erwähnt wurden?"""
            }
        ]

        return self.client.call_gemini(messages, timeout=60)

    def _phase_3_enterprise_plan(self, projektplan: str, analyse: str, feedback: str) -> str:
        """
        Phase 3: Opus erstellt den Enterprise-Plan.

        Args:
            projektplan: Der ursprüngliche User-Plan
            analyse: Die Analyse aus Phase 1
            feedback: Das Feedback aus Phase 2

        Returns:
            str: Der erstellte Enterprise-Plan
        """
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Enterprise-Architekt. Erstelle einen professionellen, strukturierten Projektplan."
            },
            {
                "role": "user",
                "content": f"""Erstelle einen Enterprise-Projektplan basierend auf:

ORIGINALPLAN:
{projektplan}

ANALYSE:
{analyse}

FEEDBACK:
{feedback}

Der Enterprise-Plan soll enthalten:
1. Executive Summary
2. Detaillierte Feature-Liste
3. Technische Architektur
4. Entwicklungs-Phasen (zeitlich strukturiert)
5. Risiken & Mitigation
6. Ressourcen-Planung
7. Qualitätssicherung

Format: Professionell, strukturiert, Enterprise-ready."""
            }
        ]

        return self.client.call_sonnet(messages, timeout=120)

    def _phase_4_qualitaetspruefung(self, enterprise_plan: str) -> str:
        """
        Phase 4: Gemini prüft Qualität und entfernt Überflüssiges.

        Args:
            enterprise_plan: Der Enterprise-Plan aus Phase 3

        Returns:
            str: Der optimierte Plan
        """
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Qualitäts-Manager. Prüfe den Plan auf Vollständigkeit, Konsistenz und entferne Überflüssiges."
            },
            {
                "role": "user",
                "content": f"""Prüfe diesen Enterprise-Plan:

{enterprise_plan}

Aufgaben:
1. Prüfe auf Vollständigkeit
2. Entferne redundante oder überflüssige Abschnitte
3. Prüfe auf Konsistenz
4. Identifiziere Lücken
5. Gib den optimierten Plan zurück (ohne Überflüssiges)

Gib NUR den optimierten Plan zurück, keine zusätzliche Erklärung."""
            }
        ]

        return self.client.call_gemini(messages, timeout=90)

    def _phase_5_verbesserung(self, gepruefter_plan: str, feedback: str) -> str:
        """
        Phase 5: Opus verbessert den Plan basierend auf Feedback.

        Args:
            gepruefter_plan: Der geprüfte Plan aus Phase 4
            feedback: Das ursprüngliche Feedback aus Phase 2

        Returns:
            str: Der finale, verbesserte Plan
        """
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Senior Consultant. Verbessere den Plan basierend auf dem Feedback."
            },
            {
                "role": "user",
                "content": f"""Verbessere diesen Plan:

{gepruefter_plan}

Berücksichtige dabei das frühere Feedback:
{feedback}

Erstelle die finale, verbesserte Version:
- Integriere alle wichtigen Punkte aus dem Feedback
- Behebe identifizierte Lücken
- Optimiere Struktur und Klarheit
- Mache ihn actionable und umsetzbar

Gib NUR den finalen Plan zurück."""
            }
        ]

        return self.client.call_sonnet(messages, timeout=120)

    def _phase_6_bewertung(self, finaler_plan: str) -> str:
        """
        Phase 6: Gemini bewertet den finalen Plan.

        Args:
            finaler_plan: Der finale Plan aus Phase 5

        Returns:
            str: Die Bewertung mit Sternen und Begründung
        """
        messages = [
            {
                "role": "system",
                "content": "Du bist ein erfahrener Projekt-Evaluator. Bewerte den finalen Plan."
            },
            {
                "role": "user",
                "content": f"""Bewerte diesen finalen Enterprise-Plan:

{finaler_plan}

Gib eine Bewertung im folgenden Format:

BEWERTUNG: X/10 Sterne

BEGRÜNDUNG:
- [Stärken des Plans]
- [Schwächen/Verbesserungspotential]
- [Umsetzbarkeit]
- [Vollständigkeit]

EMPFEHLUNG: [Kann direkt umgesetzt werden / Noch Anpassungen nötig / etc.]"""
            }
        ]

        return self.client.call_gemini(messages, timeout=60)

    def get_status(self) -> dict[str, Any]:
        """
        Gibt den aktuellen Workflow-Status zurück.

        Returns:
            dict: Status mit current_step, steps, results, final_plan, bewertung, error
        """
        return self.status
