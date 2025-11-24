"""
NEXUS OVERLORD v2.0 - OpenRouter API Client
Handles API calls to OpenRouter for Multi-Agent Workflow
"""

import requests
import os
from typing import List, Dict, Optional
import time


class OpenRouterClient:
    """Client for OpenRouter API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key (defaults to env variable)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OpenRouter API key not found in environment")

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: int = 60
    ) -> str:
        """
        Call OpenRouter API with retry logic

        Args:
            model: Model ID (e.g., 'anthropic/claude-sonnet-4.5')
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_retries: Number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            str: Response content from the model

        Raises:
            Exception: If all retries fail
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

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )

                response.raise_for_status()

                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    return content
                else:
                    raise ValueError("Unexpected response format from OpenRouter")

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout after {timeout}s: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            except requests.exceptions.RequestException as e:
                last_error = f"Request failed: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            except (ValueError, KeyError) as e:
                last_error = f"Response parsing failed: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

        raise Exception(f"OpenRouter API call failed after {max_retries} attempts: {last_error}")

    def call_sonnet(self, messages: List[Dict[str, str]], **kwargs) -> str:
        model = os.getenv('SONNET_MODEL', 'anthropic/claude-sonnet-4.5')
        return self.call(model, messages, **kwargs)

    def call_gemini(self, messages: List[Dict[str, str]], **kwargs) -> str:
        model = os.getenv('GEMINI_MODEL', 'google/gemini-3-pro-preview')
        return self.call(model, messages, **kwargs)


_client = None

def get_client() -> OpenRouterClient:
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
