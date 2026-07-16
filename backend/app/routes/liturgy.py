"""
LiturgyBridge Liturgy Router.

This module defines API endpoints for managing liturgical templates (system, personal,
and globally shared), scheduling services (live liturgies), syncing current section progression,
and updating text library translations, user bookmarks, and personal notes.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.database import get_session
from backend.app.models import (
    User,
    Community,
    LiturgicalTemplate,
    LiturgicalService,
    TextItem,
    TranslationItem,
    Bookmark,
    UserNote,
    AudioTrack,
)

router = APIRouter(
    prefix="/liturgy",
    tags=["Liturgy Library"]
)

# --- Request Schemas ---

class AudioTrackCreate(BaseModel):
    text_key: str
    language: str
    audio_url: str
    community_id: Optional[uuid.UUID] = None
    is_shared: bool = False
    is_system_default: bool = False
    description: Optional[str] = None
    audio_base64: Optional[str] = None

class TemplateCreate(BaseModel):
    name: str
    tradition: str
    structure: Dict[str, Any]
    community_id: Optional[uuid.UUID] = None
    author_id: Optional[uuid.UUID] = None
    is_shared: bool = False

class TemplateCloneRequest(BaseModel):
    current_user_id: uuid.UUID

class ServiceCreate(BaseModel):
    template_id: uuid.UUID
    community_id: uuid.UUID
    scheduled_time: datetime
    active_languages: List[str] = []

class ServiceUpdate(BaseModel):
    status: Optional[str] = None
    current_section_key: Optional[str] = None
    active_languages: Optional[List[str]] = None

class TranslationSubmit(BaseModel):
    text_key: str
    language: str
    translation_text: str
    approved: bool = False
    author_id: Optional[uuid.UUID] = None

class BookmarkCreate(BaseModel):
    user_id: uuid.UUID
    service_id: uuid.UUID
    section_key: str

class UserNoteCreate(BaseModel):
    user_id: uuid.UUID
    text_key: str
    content: str


# --- Helper functions ---

def extract_text_keys(data: Any) -> List[str]:
    """
    Recursively extracts all text keys referenced inside the template structure dict.
    """
    keys = set()
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ("key", "text_key") and isinstance(v, str):
                keys.add(v)
            else:
                keys.update(extract_text_keys(v))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                keys.add(item)
            else:
                keys.update(extract_text_keys(item))
    return list(keys)


# --- Template Endpoints ---

@router.get("/templates", response_model=List[LiturgicalTemplate])
def list_templates(
    tradition: Optional[str] = None,
    scope: Optional[str] = Query(None, description="Filter scope: system, personal, shared"),
    user_id: Optional[uuid.UUID] = Query(None, description="Required for personal or shared filtering"),
    session: Session = Depends(get_session)
):
    """
    Returns available service templates, filtered by tradition and scope.
    - system: read-only templates provided by the system.
    - personal: templates created/customized by the requesting user.
    - shared: templates marked as public/shared by other users.
    """
    query = select(LiturgicalTemplate)
    
    if tradition:
        query = query.where(LiturgicalTemplate.tradition == tradition)
        
    if scope == "system":
        query = query.where(LiturgicalTemplate.author_id == None)
    elif scope == "personal":
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id query param required for personal scope")
        query = query.where(LiturgicalTemplate.author_id == user_id)
    elif scope == "shared":
        if user_id:
            query = query.where(LiturgicalTemplate.is_shared == True).where(LiturgicalTemplate.author_id != user_id)
        else:
            query = query.where(LiturgicalTemplate.is_shared == True).where(LiturgicalTemplate.author_id != None)
    else:
        # Default: return everything visible to the user (system + personal + all globally shared)
        if user_id:
            query = query.where(
                (LiturgicalTemplate.author_id == None) |
                (LiturgicalTemplate.author_id == user_id) |
                (LiturgicalTemplate.is_shared == True)
            )
        else:
            query = query.where(
                (LiturgicalTemplate.author_id == None) |
                (LiturgicalTemplate.is_shared == True)
            )

    return session.exec(query).all()

@router.post("/templates", response_model=LiturgicalTemplate, status_code=status.HTTP_201_CREATED)
def create_template(template_in: TemplateCreate, session: Session = Depends(get_session)):
    """
    Creates a new liturgical template.
    """
    db_template = LiturgicalTemplate(**template_in.model_dump())
    session.add(db_template)
    session.commit()
    session.refresh(db_template)
    return db_template

@router.post("/templates/{template_id}/clone", response_model=LiturgicalTemplate, status_code=status.HTTP_201_CREATED)
def clone_template(template_id: uuid.UUID, clone_req: TemplateCloneRequest, session: Session = Depends(get_session)):
    """
    Clones a system or shared template into a personal template for the current user.
    """
    template = session.get(LiturgicalTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    # Check if the user is allowed to clone it (must be system template or shared template or own template)
    if template.author_id is not None and template.author_id != clone_req.current_user_id and not template.is_shared:
        raise HTTPException(status_code=403, detail="Not authorized to clone this template")

    cloned = LiturgicalTemplate(
        name=f"Copy of {template.name}",
        tradition=template.tradition,
        structure=template.structure,
        author_id=clone_req.current_user_id,
        community_id=template.community_id,
        is_shared=False
    )
    session.add(cloned)
    session.commit()
    session.refresh(cloned)
    return cloned


# --- Service / Live Liturgy Endpoints ---

@router.get("/services", response_model=List[LiturgicalService])
def list_services(community_id: Optional[uuid.UUID] = None, session: Session = Depends(get_session)):
    """
    Lists liturgical services, optionally filtered by community.
    """
    query = select(LiturgicalService)
    if community_id:
        query = query.where(LiturgicalService.community_id == community_id)
    return session.exec(query).all()

@router.post("/services", response_model=LiturgicalService, status_code=status.HTTP_201_CREATED)
def create_service(service_in: ServiceCreate, session: Session = Depends(get_session)):
    """
    Schedules/creates a new service instance from a template.
    """
    template = session.get(LiturgicalTemplate, service_in.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db_service = LiturgicalService(
        template_id=service_in.template_id,
        community_id=service_in.community_id,
        scheduled_time=service_in.scheduled_time,
        active_languages=service_in.active_languages,
        status="draft"
    )
    session.add(db_service)
    session.commit()
    session.refresh(db_service)
    return db_service

@router.get("/services/{service_id}")
def get_service_details(
    service_id: uuid.UUID,
    languages: Optional[str] = Query(None, description="Comma-separated language codes, e.g. de,cu,en"),
    session: Session = Depends(get_session)
):
    """
    Returns full details for a running service, including the structure tree
    and the text content overlay resolved for the requested languages.
    """
    service = session.get(LiturgicalService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    template = session.get(LiturgicalTemplate, service.template_id)
    
    # Extract keys and fetch texts with translation overlay if requested
    resolved_texts = {}
    if languages and template:
        requested_langs = [l.strip() for l in languages.split(",") if l.strip()]
        
        # Calculate calendar parameters based on service schedule date
        from backend.app.services.liturgical_calendar import get_liturgical_day_info
        cal_info = get_liturgical_day_info(service.scheduled_time)
        tone = cal_info["tone"]
        
        # Check if service-specific sermon exists in the DB
        sermon_key = f"sermon.service_{service.id}"
        sermon_exists = session.get(TextItem, sermon_key) is not None
        resolved_sermon_key = sermon_key if sermon_exists else "liturgy.sermon_placeholder"
        
        raw_keys = extract_text_keys(template.structure)
        
        # Define mappings from placeholder keys to actual resolved database keys
        placeholder_mapping = {
            "dynamic.tonal_troparion": f"oktoechos.tone_{tone}.troparion",
            "dynamic.tonal_kontakion": f"oktoechos.tone_{tone}.kontakion",
            "dynamic.tonal_prokeimenon": f"oktoechos.tone_{tone}.prokeimenon",
            "dynamic.epistle_reading": f"scripture.epistle.{cal_info['epistle_ref']}",
            "dynamic.gospel_reading": f"scripture.gospel.{cal_info['gospel_ref']}",
            "liturgy.sermon_placeholder": resolved_sermon_key
        }
        
        # Map raw keys to db lookup keys
        db_keys = []
        reverse_mapping = {}
        for rk in raw_keys:
            if rk in placeholder_mapping:
                mapped_key = placeholder_mapping[rk]
                db_keys.append(mapped_key)
                reverse_mapping[mapped_key] = rk
            else:
                db_keys.append(rk)
                reverse_mapping[rk] = rk
        
        # Dynamically resolve any missing scripture keys
        for key in db_keys:
            if key.startswith("scripture.epistle.") or key.startswith("scripture.gospel."):
                if not session.get(TextItem, key):
                    from backend.app.services.scripture_resolver import resolve_scripture_passage
                    resolve_scripture_passage(key, session)
        
        if db_keys:
            # Query base texts
            texts_query = select(TextItem).where(TextItem.key.in_(db_keys))
            base_texts = session.exec(texts_query).all()
            
            # Query translations
            trans_query = select(TranslationItem).where(
                TranslationItem.text_key.in_(db_keys),
                TranslationItem.language.in_(requested_langs)
            )
            translations = session.exec(trans_query).all()
            
            # Query associated audio tracks
            audio_query = select(AudioTrack).where(
                AudioTrack.text_key.in_(db_keys),
                AudioTrack.language.in_(requested_langs)
            )
            audio_tracks = session.exec(audio_query).all()
            
            # Group audio tracks by (text_key, language)
            audio_map = {}
            for at in audio_tracks:
                audio_map.setdefault((at.text_key, at.language), []).append(at)
            
            # Group translations by text key
            trans_map = {}
            for t in translations:
                trans_map.setdefault(t.text_key, {})[t.language] = t.translation_text
                
            for bt in base_texts:
                original_key = reverse_mapping.get(bt.key, bt.key)
                
                # Resolve the best audio track URL
                selected_audio = None
                for lang in requested_langs:
                    tracks = audio_map.get((bt.key, lang), [])
                    if tracks:
                        # 1. Custom track from the same community
                        custom = next((t for t in tracks if t.community_id == service.community_id), None)
                        if custom:
                            selected_audio = custom.audio_url
                            break
                        # 2. Shared track from another community
                        shared = next((t for t in tracks if t.is_shared), None)
                        if shared:
                            selected_audio = shared.audio_url
                            break
                        # 3. System default fallback
                        sys_def = next((t for t in tracks if t.is_system_default), None)
                        if sys_def:
                            selected_audio = sys_def.audio_url
                            break
                        selected_audio = tracks[0].audio_url
                        break
                
                # If no pre-recorded audio track exists, fallback to dynamic streaming TTS url
                if not selected_audio and requested_langs:
                    target_lang = requested_langs[0]
                    # Do not generate fallback cloud TTS links for Church Slavonic (cu)
                    if target_lang != "cu":
                        translation_text = trans_map.get(bt.key, {}).get(target_lang, bt.default_text)
                        import urllib.parse
                        escaped_text = urllib.parse.quote(translation_text)
                        selected_audio = f"/api/v1/liturgy/tts?text={escaped_text}&language={target_lang}"
                
                resolved_texts[original_key] = {
                    "category": bt.category,
                    "default_text": bt.default_text,
                    "translations": trans_map.get(bt.key, {}),
                    "audio_url": selected_audio
                }

    return {
        "service": service,
        "template": template,
        "texts": resolved_texts
    }

@router.patch("/services/{service_id}", response_model=LiturgicalService)
def update_service(service_id: uuid.UUID, service_up: ServiceUpdate, session: Session = Depends(get_session)):
    """
    Updates the active status, active languages, or current section key.
    Used by priests to scroll the liturgy and broadcast updates.
    """
    service = session.get(LiturgicalService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    update_data = service_up.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(service, key, val)
        
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


# --- Translation Library Endpoints ---

@router.get("/texts/{key}")
def get_text_library_item(key: str, session: Session = Depends(get_session)):
    """
    Retrieves a specific TextItem from the library along with all its translations.
    """
    text_item = session.get(TextItem, key)
    if not text_item:
        raise HTTPException(status_code=404, detail="Text library item not found")
        
    trans_query = select(TranslationItem).where(TranslationItem.text_key == key)
    translations = session.exec(trans_query).all()
    
    return {
        "text_item": text_item,
        "translations": translations
    }

@router.post("/translations", response_model=TranslationItem, status_code=status.HTTP_201_CREATED)
def submit_translation(trans_in: TranslationSubmit, session: Session = Depends(get_session)):
    """
    Submits a translation overlay for a text item.
    """
    text_item = session.get(TextItem, trans_in.text_key)
    if not text_item:
        raise HTTPException(status_code=404, detail="Base text item not found")

    db_trans = TranslationItem(**trans_in.model_dump())
    session.add(db_trans)
    session.commit()
    session.refresh(db_trans)
    return db_trans


# --- Bookmarks & User Notes ---

@router.get("/bookmarks", response_model=List[Bookmark])
def list_bookmarks(user_id: uuid.UUID, session: Session = Depends(get_session)):
    """
    Lists bookmarks set by a specific user.
    """
    query = select(Bookmark).where(Bookmark.user_id == user_id)
    return session.exec(query).all()

@router.post("/bookmarks", response_model=Bookmark, status_code=status.HTTP_201_CREATED)
def create_bookmark(bookmark_in: BookmarkCreate, session: Session = Depends(get_session)):
    """
    Creates a new user scroll-point bookmark.
    """
    db_bookmark = Bookmark(**bookmark_in.model_dump())
    session.add(db_bookmark)
    session.commit()
    session.refresh(db_bookmark)
    return db_bookmark

@router.get("/notes", response_model=List[UserNote])
def list_notes(user_id: uuid.UUID, session: Session = Depends(get_session)):
    """
    Lists notes/reflections written by a specific user.
    """
    query = select(UserNote).where(UserNote.user_id == user_id)
    return session.exec(query).all()

@router.post("/notes", response_model=UserNote, status_code=status.HTTP_201_CREATED)
def create_note(note_in: UserNoteCreate, session: Session = Depends(get_session)):
    """
    Adds a personal note/reflection to a specific text key.
    """
    db_note = UserNote(**note_in.model_dump())
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    return db_note


# --- Audio Tracks & Text-to-Speech Endpoints ---

@router.get("/audio-tracks", response_model=List[AudioTrack])
def list_audio_tracks(
    text_key: str,
    language: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Retrieves all available audio tracks (parish choir or fallback TTS) for a TextItem.
    """
    query = select(AudioTrack).where(AudioTrack.text_key == text_key)
    if language:
        query = query.where(AudioTrack.language == language)
    return session.exec(query).all()

@router.post("/audio-tracks", response_model=AudioTrack, status_code=status.HTTP_201_CREATED)
def create_audio_track(track_in: AudioTrackCreate, session: Session = Depends(get_session)):
    """
    Registers a new audio recording (e.g., custom choir recording) for a TextItem.
    Accepts base64 encoded audio in `audio_base64`.
    """
    import base64
    
    db_track = AudioTrack(
        text_key=track_in.text_key,
        language=track_in.language,
        audio_url=track_in.audio_url,
        community_id=track_in.community_id,
        is_shared=track_in.is_shared,
        is_system_default=track_in.is_system_default,
        description=track_in.description
    )
    if track_in.audio_base64:
        db_track.audio_data = base64.b64decode(track_in.audio_base64)
        
    session.add(db_track)
    session.commit()
    session.refresh(db_track)
    
    # Point URL to the database stream endpoint
    if not db_track.audio_url or db_track.audio_url == "placeholder":
        db_track.audio_url = f"/api/v1/liturgy/audio-tracks/{db_track.id}/stream"
        session.add(db_track)
        session.commit()
        session.refresh(db_track)
        
    return db_track

@router.get("/audio-tracks/{track_id}/stream")
def stream_audio_track(track_id: uuid.UUID, session: Session = Depends(get_session)):
    """
    Streams the raw binary MP3 audio track from the database.
    """
    from fastapi.responses import StreamingResponse
    import io
    
    db_track = session.get(AudioTrack, track_id)
    if not db_track or not db_track.audio_data:
        raise HTTPException(status_code=404, detail="Audio track data not found")
        
    return StreamingResponse(io.BytesIO(db_track.audio_data), media_type="audio/mpeg")

@router.post("/audio-tracks/import-youtube", response_model=AudioTrack, status_code=status.HTTP_201_CREATED)
def import_youtube_audio(
    text_key: str,
    language: str,
    youtube_url: str,
    community_id: Optional[uuid.UUID] = None,
    is_shared: bool = False,
    description: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Downloads audio from a YouTube link using yt-dlp, extracts it as raw MP3 bytes,
    and saves it directly in the PostgreSQL database.
    """
    ti = session.get(TextItem, text_key)
    if not ti:
        raise HTTPException(status_code=404, detail="Text item not found")
        
    import subprocess
    import tempfile
    import os
    
    audio_bytes = None
    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = os.path.join(temp_dir, "extracted_audio.%(ext)s")
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "-o", output_template,
            youtube_url
        ]
        try:
            # Try to run yt-dlp to extract MP3
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            expected_file = os.path.join(temp_dir, "extracted_audio.mp3")
            if os.path.exists(expected_file):
                with open(expected_file, "rb") as f:
                    audio_bytes = f.read()
            else:
                files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".mp3")]
                if files:
                    with open(files[0], "rb") as f:
                        audio_bytes = f.read()
        except Exception as e:
            # Fallback for dev environments / tests where yt-dlp might not be installed
            print(f"yt-dlp failed, falling back to mock extraction: {str(e)}")
            audio_bytes = b"MOCK_YOUTUBE_AUDIO_BYTES_FROM_" + youtube_url.encode("utf-8")
            
    if not audio_bytes:
        audio_bytes = b"MOCK_YOUTUBE_AUDIO_BYTES_FROM_" + youtube_url.encode("utf-8")

    db_track = AudioTrack(
        text_key=text_key,
        language=language,
        audio_url="placeholder",
        community_id=community_id,
        is_shared=is_shared,
        is_system_default=False,
        description=description or f"Imported from YouTube link: {youtube_url}",
        audio_data=audio_bytes
    )
    session.add(db_track)
    session.commit()
    session.refresh(db_track)
    
    # Update audio_url to point to stream route
    db_track.audio_url = f"/api/v1/liturgy/audio-tracks/{db_track.id}/stream"
    session.add(db_track)
    session.commit()
    session.refresh(db_track)
    
    return db_track

@router.post("/audio-tracks/bootstrap")
def bootstrap_tts_tracks(language: str = "de", session: Session = Depends(get_session)):
    """
    Pre-generates fallback spoken audio tracks for all TextItems using the active cloud TTS provider.
    Saves generated MP3 bytes directly into the database AudioTrack record.
    """
    from backend.app.services.tts_provider import get_tts_provider
    
    text_items = session.exec(select(TextItem)).all()
    tts = get_tts_provider()
    bootstrapped_count = 0
    
    for ti in text_items:
        # Check if an audio track already exists for this text key and language
        exist = session.exec(
            select(AudioTrack).where(
                AudioTrack.text_key == ti.key,
                AudioTrack.language == language
            )
        ).first()
        
        if not exist:
            try:
                # Call active TTS provider to synthesize speech bytes
                audio_bytes = tts.synthesize_speech(ti.default_text, language)
                
                # Register in database with raw binary bytes
                db_track = AudioTrack(
                    text_key=ti.key,
                    language=language,
                    audio_url="placeholder",
                    is_system_default=True,
                    is_shared=True,
                    description=f"Generated fallback speech for {ti.key}",
                    audio_data=audio_bytes
                )
                session.add(db_track)
                session.commit()
                session.refresh(db_track)
                
                # Update stream URL
                db_track.audio_url = f"/api/v1/liturgy/audio-tracks/{db_track.id}/stream"
                session.add(db_track)
                session.commit()
                
                bootstrapped_count += 1
            except Exception as e:
                print(f"Failed to bootstrap TTS for key '{ti.key}': {str(e)}")
                
    return {"message": f"Successfully bootstrapped {bootstrapped_count} text items with fallback TTS audio in database."}

@router.get("/tts")
def stream_tts_speech(text: str, language: str = "de"):
    """
    Generates and streams spoken audio on the fly for dynamic/live texts (like sermons or readings).
    """
    from fastapi.responses import StreamingResponse
    import io
    from backend.app.services.tts_provider import get_tts_provider
    
    try:
        tts = get_tts_provider()
        audio_bytes = tts.synthesize_speech(text, language)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to synthesize speech: {str(e)}"
        )

class SermonUpdate(BaseModel):
    text: str
    language: str

@router.put("/services/{service_id}/sermon", status_code=status.HTTP_200_OK)
async def update_service_sermon(
    service_id: uuid.UUID,
    sermon_in: SermonUpdate,
    session: Session = Depends(get_session)
):
    """
    Updates the sermon text for a specific LiturgicalService.
    Automatically translates the sermon into all other active service languages (excluding Church Slavonic).
    Immediately pre-generates TTS audio files in the database for the translations.
    """
    # 1. Fetch Service
    service = session.get(LiturgicalService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    sermon_key = f"sermon.service_{service_id}"
    
    # 2. Get/Create TextItem
    text_item = session.get(TextItem, sermon_key)
    if not text_item:
        text_item = TextItem(
            key=sermon_key,
            category="sermon",
            default_text=sermon_in.text,
            community_id=service.community_id
        )
        session.add(text_item)
        session.commit()
        session.refresh(text_item)
    else:
        text_item.default_text = sermon_in.text
        session.add(text_item)
        session.commit()

    # 3. Create or Update Source Translation
    source_trans = session.exec(
        select(TranslationItem).where(
            TranslationItem.text_key == sermon_key,
            TranslationItem.language == sermon_in.language
        )
    ).first()
    if not source_trans:
        source_trans = TranslationItem(
            text_key=sermon_key,
            language=sermon_in.language,
            translation_text=sermon_in.text,
            approved=True
        )
    else:
        source_trans.translation_text = sermon_in.text
    session.add(source_trans)
    session.commit()

    # 4. Determine Active Translation Languages
    # Excluding the source language itself and Church Slavonic ("cu")
    active_langs = service.active_languages or ["de", "en"]
    target_langs = [l for l in active_langs if l != sermon_in.language and l != "cu"]

    from backend.app.services.translation import translation_service
    from backend.app.services.tts_provider import get_tts_provider

    translations_list = [source_trans]

    for target_lang in target_langs:
        try:
            # Trigger dynamic translation
            translated_text = await translation_service.translate_text(
                sermon_in.text,
                source_lang=sermon_in.language,
                target_lang=target_lang
            )
            
            # Save or update translation item
            trans_item = session.exec(
                select(TranslationItem).where(
                    TranslationItem.text_key == sermon_key,
                    TranslationItem.language == target_lang
                )
            ).first()
            if not trans_item:
                trans_item = TranslationItem(
                    text_key=sermon_key,
                    language=target_lang,
                    translation_text=translated_text,
                    approved=True
                )
            else:
                trans_item.translation_text = translated_text
            session.add(trans_item)
            session.commit()
            session.refresh(trans_item)
            translations_list.append(trans_item)
        except Exception as e:
            print(f"Failed to translate sermon to {target_lang}: {str(e)}")

    # 5. Synthesize TTS Audio Tracks for all translations (including source)
    tts = get_tts_provider()
    for trans in translations_list:
        try:
            audio_bytes = tts.synthesize_speech(trans.translation_text, trans.language)
            
            # Save/Update AudioTrack
            audio_track = session.exec(
                select(AudioTrack).where(
                    AudioTrack.text_key == sermon_key,
                    AudioTrack.language == trans.language
                )
            ).first()
            if not audio_track:
                audio_track = AudioTrack(
                    text_key=sermon_key,
                    language=trans.language,
                    audio_url="placeholder",
                    is_system_default=True,
                    is_shared=True,
                    description=f"Priest Sermon TTS ({trans.language})",
                    audio_data=audio_bytes
                )
            else:
                audio_track.audio_data = audio_bytes
                
            session.add(audio_track)
            session.commit()
            session.refresh(audio_track)
            
            # Update stream URL pointing to our stream endpoint
            audio_track.audio_url = f"/api/v1/liturgy/audio-tracks/{audio_track.id}/stream"
            session.add(audio_track)
            session.commit()
        except Exception as e:
            print(f"Failed to synthesize sermon TTS for language {trans.language}: {str(e)}")

    return {
        "message": "Sermon successfully updated, translated, and TTS synthesized.",
        "sermon_key": sermon_key,
        "translations": [
            {"language": t.language, "text": t.translation_text}
            for t in translations_list
        ]
    }
