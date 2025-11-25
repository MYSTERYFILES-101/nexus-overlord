"""
NEXUS OVERLORD v2.0 - OpenRouter API Client

Handles API calls to OpenRouter for Multi-Agent Workflow.
Unterstuetzt mehrere KI-Modelle: Opus 4.5, Gemini 3 Pro.

Features:
    - Retry-Logik mit exponentialem Backoff
    - Timeout-Handling
    - Rate-Limiting durch Exponential Backoff
    - Logging fuer Debugging
"""

import logging
import os
import time
from typing import Any

import requests

# Logger konfigurieren
logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Client fuer die OpenRouter API.

    Unterstuetzt Retry-Logik mit exponentialem Backoff und
    verschiedene KI-Modelle (Opus 4.5, Gemini 3 Pro).

    Attributes:
        api_key: OpenRouter API-Schluessel
        base_url: OpenRouter API Endpoint
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialisiert den OpenRouter Client.

        Args:
            api_key: OpenRouter API-Schluessel (Standard: aus Umgebungsvariable)

        Raises:
            ValueError: Wenn kein API-Schluessel gefunden wird
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            logger.error("OpenRouter API-Schluessel nicht gefunden")
            raise ValueError("OpenRouter API key not found in environment")

        logger.info("OpenRouter Client initialisiert")

    def call(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: int = 60
    ) -> str:
        """
        Ruft die OpenRouter API mit Retry-Logik auf.

        Args:
            model: Model-ID (z.B. 'anthropic/claude-opus-4-5-20251101')
            messages: Liste von Nachrichten mit 'role' und 'content'
            temperature: Sampling-Temperatur (0-1)
            max_retries: Anzahl der Wiederholungsversuche
            timeout: Request-Timeout in Sekunden

        Returns:
            str: Antwortinhalt vom Modell

        Raises:
            Exception: Wenn alle Versuche fehlschlagen
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexus-overlord.com",
            "X-Title": "NEXUS OVERLORD v2.0"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        last_error = None
        model_name = model.split('/')[-1] if '/' in model else model

        logger.info(f"API-Call an {model_name} (Temperatur: {temperature})")
        logger.debug(f"Prompt: {messages[-1]['content'][:200]}...")

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )

                elapsed = time.time() - start_time
                logger.debug(f"API-Response in {elapsed:.2f}s (Status: {response.status_code})")

                response.raise_for_status()

                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"API-Call erfolgreich ({len(content)} Zeichen)")
                    return content
                else:
                    raise ValueError("Unerwartetes Antwortformat von OpenRouter")

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout nach {timeout}s: {str(e)}"
                logger.warning(f"Versuch {attempt + 1}/{max_retries}: Timeout")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Warte {wait_time}s vor naechstem Versuch...")
                    time.sleep(wait_time)
                    continue

            except requests.exceptions.RequestException as e:
                last_error = f"Request fehlgeschlagen: {str(e)}"
                logger.warning(f"Versuch {attempt + 1}/{max_retries}: {last_error}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Warte {wait_time}s vor naechstem Versuch...")
                    time.sleep(wait_time)
                    continue

            except (ValueError, KeyError) as e:
                last_error = f"Response-Parsing fehlgeschlagen: {str(e)}"
                logger.warning(f"Versuch {attempt + 1}/{max_retries}: {last_error}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

        logger.error(f"API-Call fehlgeschlagen nach {max_retries} Versuchen: {last_error}")
        raise Exception(f"OpenRouter API call failed after {max_retries} attempts: {last_error}")

    def call_sonnet(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """
        Ruft Opus 4.5 auf (Name fuer Kompatibilitaet beibehalten).

        Args:
            messages: Liste von Nachrichten
            **kwargs: Weitere Argumente fuer call()

        Returns:
            str: Antwort vom Modell
        """
        model = os.getenv('OPUS_MODEL', 'anthropic/claude-opus-4-5-20251101')
        logger.debug("call_sonnet() -> Opus 4.5")
        return self.call(model, messages, **kwargs)

    def call_opus(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """
        Ruft Opus 4.5 auf - das neueste Claude-Modell.

        Args:
            messages: Liste von Nachrichten
            **kwargs: Weitere Argumente fuer call()

        Returns:
            str: Antwort vom Modell
        """
        model = os.getenv('OPUS_MODEL', 'anthropic/claude-opus-4-5-20251101')
        logger.debug("call_opus() -> Opus 4.5")
        return self.call(model, messages, **kwargs)

    def call_gemini(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """
        Ruft Gemini 3 Pro auf.

        Args:
            messages: Liste von Nachrichten
            **kwargs: Weitere Argumente fuer call()

        Returns:
            str: Antwort vom Modell
        """
        model = os.getenv('GEMINI_MODEL', 'google/gemini-3-pro-preview')
        logger.debug("call_gemini() -> Gemini 3 Pro")
        return self.call(model, messages, **kwargs)


# Singleton-Instanz
_client: OpenRouterClient | None = None


def get_client() -> OpenRouterClient:
    """
    Gibt die Singleton-Instanz des OpenRouter-Clients zurueck.

    Returns:
        OpenRouterClient: Die Client-Instanz
    """
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
