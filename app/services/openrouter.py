"""
NEXUS OVERLORD v2.0 - OpenRouter API Integration
Basis-Funktion für alle OpenRouter API Calls
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(model: str, messages: list, max_tokens: int = 4000, temperature: float = 0.7):
    """
    Basis-Funktion für OpenRouter API Calls

    Args:
        model (str): OpenRouter Model-ID
        messages (list): Liste von Message-Dicts mit role und content
        max_tokens (int): Maximale Anzahl an Tokens in der Antwort
        temperature (float): Kreativität (0.0 - 1.0)

    Returns:
        str: Antwort des KI-Models

    Raises:
        ValueError: Wenn API Key fehlt
        requests.HTTPError: Bei API-Fehlern
    """

    # Validate API Key
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )

    # Headers
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nexus-overlord.ai",  # Optional
        "X-Title": "NEXUS OVERLORD v2.0"  # Optional
    }

    # Payload
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    try:
        # API Call
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        # Extract response
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        # HTTP Error (4xx, 5xx)
        error_msg = f"OpenRouter API Error: {e.response.status_code}"
        if e.response.text:
            error_msg += f" - {e.response.text}"
        raise requests.HTTPError(error_msg)

    except requests.exceptions.Timeout:
        raise TimeoutError("OpenRouter API request timed out after 60 seconds")

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"OpenRouter API connection error: {str(e)}")

    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected API response format: {str(e)}")


def test_connection():
    """
    Test OpenRouter API Connection

    Returns:
        bool: True wenn Verbindung erfolgreich
    """
    try:
        messages = [{"role": "user", "content": "Antworte mit: OK"}]
        response = call_openrouter(
            model="anthropic/claude-sonnet-4-5-20250514",
            messages=messages,
            max_tokens=10
        )
        return "OK" in response or len(response) > 0
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False
