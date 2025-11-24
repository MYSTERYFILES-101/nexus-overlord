"""
NEXUS OVERLORD v2.0 - Multi-Agent Workflow
6-Phasen Enterprise-Plan Erstellung mit Sonnet 4.5 + Gemini 3 Pro
"""

from typing import Dict, List, Any
from .openrouter import get_client
import time


class MultiAgentWorkflow:
    """6-Phasen Multi-Agent Workflow für Enterprise-Plan Erstellung"""

    def __init__(self):
        self.client = get_client()
        self.status = {
            "current_step": 0,
            "steps": self._init_steps(),
            "results": {},
            "final_plan": None,
            "bewertung": None,
            "error": None
        }

    def _init_steps(self) -> List[Dict[str, Any]]:
        """Initialize step status"""
        return [
            {"nr": 1, "name": "Sonnet analysiert", "icon": "🔍", "ai": "Sonnet 4.5", "status": "waiting", "result": None},
            {"nr": 2, "name": "Gemini Feedback", "icon": "💭", "ai": "Gemini 3 Pro", "status": "waiting", "result": None},
            {"nr": 3, "name": "Enterprise-Plan", "icon": "📋", "ai": "Sonnet 4.5", "status": "waiting", "result": None},
            {"nr": 4, "name": "Qualitätsprüfung", "icon": "🔎", "ai": "Gemini 3 Pro", "status": "waiting", "result": None},
            {"nr": 5, "name": "Verbesserung", "icon": "✨", "ai": "Sonnet 4.5", "status": "waiting", "result": None},
            {"nr": 6, "name": "Finale Bewertung", "icon": "⭐", "ai": "Gemini 3 Pro", "status": "waiting", "result": None},
        ]

    def _set_step_status(self, step_nr: int, status: str, result: str = None):
        """Update step status"""
        self.status["current_step"] = step_nr
        for step in self.status["steps"]:
            if step["nr"] == step_nr:
                step["status"] = status
                if result:
                    step["result"] = result
                break

    def run(self, projektname: str, projektplan: str) -> Dict[str, Any]:
        """
        Run the complete 6-phase workflow

        Args:
            projektname: Name of the project
            projektplan: User's project plan

        Returns:
            Dict with final_plan, bewertung, and status
        """
        try:
            # Phase 1: Sonnet analysiert
            self._set_step_status(1, "active")
            analyse = self._phase_1_analyse(projektplan)
            self._set_step_status(1, "done", analyse)
            self.status["results"]["analyse"] = analyse

            # Phase 2: Gemini Feedback
            self._set_step_status(2, "active")
            feedback = self._phase_2_feedback(projektplan, analyse)
            self._set_step_status(2, "done", feedback)
            self.status["results"]["feedback"] = feedback

            # Phase 3: Enterprise-Plan erstellen
            self._set_step_status(3, "active")
            enterprise_plan = self._phase_3_enterprise_plan(projektplan, analyse, feedback)
            self._set_step_status(3, "done", enterprise_plan)
            self.status["results"]["enterprise_plan"] = enterprise_plan

            # Phase 4: Qualitätsprüfung
            self._set_step_status(4, "active")
            gepruefter_plan = self._phase_4_qualitaetspruefung(enterprise_plan)
            self._set_step_status(4, "done", gepruefter_plan)
            self.status["results"]["gepruefter_plan"] = gepruefter_plan

            # Phase 5: Verbesserung
            self._set_step_status(5, "active")
            verbesserter_plan = self._phase_5_verbesserung(gepruefter_plan, feedback)
            self._set_step_status(5, "done", verbesserter_plan)
            self.status["results"]["verbesserter_plan"] = verbesserter_plan

            # Phase 6: Finale Bewertung
            self._set_step_status(6, "active")
            bewertung = self._phase_6_bewertung(verbesserter_plan)
            self._set_step_status(6, "done", bewertung)
            self.status["results"]["bewertung"] = bewertung

            # Set final results
            self.status["final_plan"] = verbesserter_plan
            self.status["bewertung"] = bewertung
            self.status["current_step"] = 6

            return self.status

        except Exception as e:
            # Set error status
            current = self.status["current_step"]
            if current > 0:
                self._set_step_status(current, "error", str(e))
            self.status["error"] = str(e)
            raise

    def _phase_1_analyse(self, projektplan: str) -> str:
        """Phase 1: Sonnet analysiert den User-Plan"""
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

        return self.client.call_sonnet(messages)

    def _phase_2_feedback(self, projektplan: str, analyse: str) -> str:
        """Phase 2: Gemini gibt Feedback zur Analyse"""
        messages = [
            {
                "role": "system",
                "content": "Du bist ein kritischer Reviewer. Gib konstruktives Feedback zur Projekt-Analyse."
            },
            {
                "role": "user",
                "content": f"""Ursprünglicher Projektplan:
{projektplan}

Analyse von Sonnet:
{analyse}

Gib kritisches aber konstruktives Feedback:
1. Was wurde gut analysiert?
2. Was fehlt in der Analyse?
3. Welche zusätzlichen Aspekte sollten berücksichtigt werden?
4. Gibt es Risiken die nicht erwähnt wurden?"""
            }
        ]

        return self.client.call_gemini(messages)

    def _phase_3_enterprise_plan(self, projektplan: str, analyse: str, feedback: str) -> str:
        """Phase 3: Sonnet erstellt Enterprise-Plan"""
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

        return self.client.call_sonnet(messages)

    def _phase_4_qualitaetspruefung(self, enterprise_plan: str) -> str:
        """Phase 4: Gemini prüft Qualität und entfernt Ungewünschtes"""
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

        return self.client.call_gemini(messages)

    def _phase_5_verbesserung(self, gepruefter_plan: str, feedback: str) -> str:
        """Phase 5: Sonnet verbessert den Plan"""
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

        return self.client.call_sonnet(messages)

    def _phase_6_bewertung(self, finaler_plan: str) -> str:
        """Phase 6: Gemini bewertet final"""
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

        return self.client.call_gemini(messages)

    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return self.status
