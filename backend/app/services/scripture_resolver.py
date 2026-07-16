"""
LiturgyBridge Dynamic Scripture Resolver.

Fetches daily Epistle/Gospel readings dynamically in multiple languages
(cu, ru, uk, de, en) using the active LLM provider strategy and caches
them in the PostgreSQL database.
"""

import json
from typing import Optional
from sqlmodel import Session, select
from backend.app.models import TextItem, TranslationItem, AudioTrack
from backend.app.services.llm_provider import get_llm_provider
from backend.app.services.tts_provider import get_tts_provider

def resolve_scripture_passage(reference_key: str, session: Session) -> Optional[TextItem]:
    """
    Resolves a scripture reference (e.g. 'scripture.epistle.Romans 12:1-10') by fetching
    the passage dynamically in cu, ru, uk, de, and en languages using the active LLM.
    Caches the results in the database and pre-generates the German TTS audio.
    """
    # 1. Parse the actual bible reference (e.g. 'Romans 12:1-10')
    prefix = "scripture.epistle."
    if reference_key.startswith("scripture.gospel."):
        prefix = "scripture.gospel."
    
    bible_ref = reference_key[len(prefix):]
    
    # 2. Check if already exists in DB
    existing = session.get(TextItem, reference_key)
    if existing:
        return existing

    # 3. Call LLM to fetch the scripture in multiple languages
    print(f"Resolving scripture '{bible_ref}' dynamically via LLM...")
    llm = get_llm_provider()
    
    prompt = f"""You are a biblical scholar specializing in Orthodox liturgical texts.
Retrieve the exact scripture passage for the reference: "{bible_ref}".
Provide the text in the following five languages:
1. "cu": The exact Church Slavonic text in Cyrillic script (Elizaveta Bible version).
2. "ru": The Russian Synodal Bible translation.
3. "uk": The Ukrainian translation (Ogienko version).
4. "de": The German translation (Luther or Einheitsübersetzung style).
5. "en": The English translation (King James Version or Orthodox Study Bible style).

Format your response as a strict JSON object with keys "cu", "ru", "uk", "de", and "en".
Do not include any markdown formatting, prefix, or explanation.
Example response:
{{
  "cu": "Святый Боже...",
  "ru": "Святой Боже...",
  "uk": "Святий Боже...",
  "de": "Heiliger Gott...",
  "en": "Holy God..."
}}
"""
    try:
        response_text = llm.generate_response(prompt)
        # Parse JSON from response
        # Strip potential markdown fences if added by LLM
        cleaned_json = response_text.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()
        
        bible_data = json.loads(cleaned_json)
    except Exception as e:
        print(f"Failed to fetch scripture via LLM for ref '{bible_ref}': {str(e)}")
        # Fallback to simple placeholder so the service doesn't crash
        bible_data = {
            "cu": f"Чтение из {bible_ref} (Славянский)",
            "ru": f"Чтение из {bible_ref} (Русский)",
            "uk": f"Читання з {bible_ref} (Українська)",
            "de": f"Lesung aus {bible_ref} (Deutsch)",
            "en": f"Reading from {bible_ref} (English)"
        }

    # 4. Save TextItem in DB
    category = "epistle" if prefix == "scripture.epistle." else "gospel"
    text_item = TextItem(
        key=reference_key,
        category=category,
        default_text=bible_data.get("de", f"Reading {bible_ref}"),
        community_id=None # Global scripture
    )
    session.add(text_item)
    session.commit()
    session.refresh(text_item)

    # 5. Save TranslationItems
    for lang, text in bible_data.items():
        trans_item = TranslationItem(
            text_key=reference_key,
            language=lang,
            translation_text=text,
            approved=True
        )
        session.add(trans_item)
    session.commit()

    # 6. Pre-generate German TTS audio and save as AudioTrack in DB
    try:
        tts = get_tts_provider()
        audio_bytes = tts.synthesize_speech(bible_data.get("de", ""), "de")
        
        audio_track = AudioTrack(
            text_key=reference_key,
            language="de",
            audio_url="placeholder",
            is_system_default=True,
            is_shared=True,
            description=f"Generated TTS for {reference_key} (de)",
            audio_data=audio_bytes
        )
        session.add(audio_track)
        session.commit()
        session.refresh(audio_track)
        
        audio_track.audio_url = f"/api/v1/liturgy/audio-tracks/{audio_track.id}/stream"
        session.add(audio_track)
        session.commit()
    except Exception as e:
        print(f"Failed to generate TTS audio for scripture {reference_key}: {str(e)}")

    return text_item
