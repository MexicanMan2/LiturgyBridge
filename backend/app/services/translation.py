"""
LiturgyBridge Translation & AI Service.

This module encapsulates connection logic to external AI APIs (like Google Gemini,
DeepL, or OpenAI) to support:
1. Live translation of sermons or announcements.
2. Machine translation suggestion for new/custom liturgical library elements.
"""

from typing import Optional
import urllib.request
import urllib.parse
import json
from backend.app.config import settings
from backend.app.services.llm_provider import get_llm_provider

class TranslationService:
    def __init__(self):
        self.deepl_key = settings.DEEPL_API_KEY

    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translates text from source_lang to target_lang.
        Priority:
        1. DeepL API (if DEEPL_API_KEY is present)
        2. Swappable LLM Provider (Gemini / Claude)
        3. Mock Fallback (for local development & tests)
        """
        if not text.strip():
            return ""

        # 1. Try DeepL API
        if self.deepl_key:
            endpoint = "https://api-free.deepl.com/v2/translate" if self.deepl_key.endswith(":fx") else "https://api.deepl.com/v2/translate"
            try:
                data = urllib.parse.urlencode({
                    "text": text,
                    "target_lang": target_lang.upper()
                }).encode("utf-8")
                
                req = urllib.request.Request(
                    endpoint,
                    data=data,
                    headers={
                        "Authorization": f"DeepL-Auth-Key {self.deepl_key}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5.0) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    return result["translations"][0]["text"]
            except Exception as e:
                print(f"DeepL translation request failed: {str(e)}")

        # 2. Try LLM Provider
        try:
            llm = get_llm_provider()
            prompt = (
                f"You are a translation assistant for LiturgyBridge. Translate the following text "
                f"from {source_lang} to {target_lang}. Return ONLY the direct translation. Do not write "
                f"introductory phrases, explanations, or quotes.\n\nText:\n{text}"
            )
            # LLMProvider generate_text is synchronous
            translated = llm.generate_text(prompt)
            if translated:
                cleaned = translated.strip().strip('"').strip("'").strip()
                if cleaned:
                    return cleaned
        except Exception as e:
            print(f"LLM translation fallback failed: {str(e)}")

        # 3. Mock Fallback
        return f"[Mock Translation to {target_lang}]: {text}"

    async def suggest_vocabulary(self, term: str, context: str) -> dict:
        """
        Uses LLM to explain specific ancient liturgical terminology to modern readers.
        """
        try:
            llm = get_llm_provider()
            prompt = (
                f"Explain the liturgical meaning of the Orthodox term '{term}' in the context "
                f"of the following section: '{context}'. Keep the explanation short, informative, "
                f"and easy to understand for average church visitors."
            )
            explanation = llm.generate_text(prompt)
        except Exception:
            explanation = f"Explanation of {term} within the context of {context}."

        return {
            "term": term,
            "explanation": explanation
        }

translation_service = TranslationService()
