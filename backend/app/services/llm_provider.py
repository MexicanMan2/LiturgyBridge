"""
LiturgyBridge LLM Provider Service.

Implements the Strategy Pattern for text generation. Defines the LLMProvider
interface and concrete implementations for Google Gemini, Anthropic Claude,
and a Mock LLM for local/test environments.
"""

from abc import ABC, abstractmethod
import httpx
from typing import Optional
from backend.app.config import settings

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    """
    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Sends a text prompt to the LLM and returns the text response.
        """
        pass

class GeminiProvider(LLMProvider):
    """
    Google Gemini API implementation.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        system_text = f"{system_instruction}\n\n" if system_instruction else ""
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_text}{prompt}"}]
            }]
        }
        
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {str(e)}")

class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude API implementation.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        if system_instruction:
            payload["system"] = system_instruction
            
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"Claude API request failed: {str(e)}")

class MockProvider(LLMProvider):
    """
    Mock LLM Provider for local development and testing.
    """
    def __init__(self, provider_name: str = "mock"):
        self.provider_name = provider_name

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        return (
            f"[AI Assistant Mock ({self.provider_name.upper()})]\n"
            f"Prompt received: '{prompt[:40]}...'\n"
            f"System instruction: '{system_instruction[:40]}...'"
        )

def get_llm_provider() -> LLMProvider:
    """
    Factory function to retrieve the configured LLM provider based on settings.
    Falls back to MockProvider if credentials are not configured.
    """
    provider_name = settings.LLM_PROVIDER.lower()
    
    if provider_name == "gemini":
        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("choose_"):
            return GeminiProvider(settings.GEMINI_API_KEY)
    elif provider_name == "claude":
        if settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("choose_"):
            return ClaudeProvider(settings.ANTHROPIC_API_KEY)
            
    # Fallback to Mock if no keys are found or configured
    return MockProvider(provider_name=provider_name)
