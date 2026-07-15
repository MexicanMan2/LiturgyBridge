"""
LiturgyBridge TTS Provider Service.

Implements the Strategy Pattern for Text-to-Speech generation.
Defines the TTSProvider interface and concrete implementations for Google Cloud TTS,
OpenAI TTS, and a Mock TTS for local/test environments.
"""

from abc import ABC, abstractmethod
import httpx
from typing import Optional
from backend.app.config import settings

class TTSProvider(ABC):
    """
    Abstract Base Class for Text-to-Speech providers.
    """
    @abstractmethod
    def synthesize_speech(self, text: str, language: str) -> bytes:
        """
        Synthesizes text into spoken audio (MP3 format) and returns raw audio bytes.
        """
        pass

class GoogleTTSProvider(TTSProvider):
    """
    Google Cloud Text-to-Speech API implementation.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def synthesize_speech(self, text: str, language: str) -> bytes:
        # Use neural/Wavenet voices based on language code
        voice_name = "de-DE-Wavenet-B" if language.lower() == "de" else "en-US-Wavenet-D"
        
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language,
                "name": voice_name
            },
            "audioConfig": {
                "audioEncoding": "MP3"
            }
        }
        
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            # Google returns base64 encoded audio
            import base64
            audio_content = base64.b64decode(data["audioContent"])
            return audio_content
        except Exception as e:
            raise RuntimeError(f"Google Cloud TTS request failed: {str(e)}")

class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS API implementation.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def synthesize_speech(self, text: str, language: str) -> bytes:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": "alloy"  # alloy, echo, fable, onyx, nova, shimmer
        }
        
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            # OpenAI returns raw binary MP3 data
            return response.content
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS request failed: {str(e)}")

class MockTTSProvider(TTSProvider):
    """
    Mock TTS Provider for local development and testing.
    Returns simulated audio bytes.
    """
    def __init__(self, provider_name: str = "mock"):
        self.provider_name = provider_name

    def synthesize_speech(self, text: str, language: str) -> bytes:
        # Returns a mock audio byte signature (e.g. mock MP3 header)
        return b"MOCK_MP3_AUDIO_DATA_FOR_" + text[:20].encode("utf-8") + b"_LANG_" + language.encode("utf-8")

def get_tts_provider() -> TTSProvider:
    """
    Factory function to retrieve the configured TTS provider based on settings.
    Falls back to MockTTSProvider if credentials are not configured.
    """
    provider_name = settings.TTS_PROVIDER.lower()
    
    if provider_name == "google":
        # Can use GEMINI_API_KEY as the Google Cloud API Key for simple setups
        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("choose_"):
            return GoogleTTSProvider(settings.GEMINI_API_KEY)
    elif provider_name == "openai":
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("choose_"):
            return OpenAITTSProvider(settings.OPENAI_API_KEY)
            
    # Fallback to Mock if no keys are found or configured
    return MockTTSProvider(provider_name=provider_name)
