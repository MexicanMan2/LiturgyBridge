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
)

router = APIRouter(
    prefix="/liturgy",
    tags=["Liturgy Library"]
)

# --- Request Schemas ---

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
        
        raw_keys = extract_text_keys(template.structure)
        
        # Define mappings from placeholder keys to actual resolved database keys
        placeholder_mapping = {
            "dynamic.tonal_troparion": f"oktoechos.tone_{tone}.troparion",
            "dynamic.tonal_kontakion": f"oktoechos.tone_{tone}.kontakion",
            "dynamic.tonal_prokeimenon": f"oktoechos.tone_{tone}.prokeimenon",
            "dynamic.epistle_reading": f"scripture.epistle.{cal_info['epistle_ref']}",
            "dynamic.gospel_reading": f"scripture.gospel.{cal_info['gospel_ref']}"
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
            
            # Group translations by text key
            trans_map = {}
            for t in translations:
                trans_map.setdefault(t.text_key, {})[t.language] = t.translation_text
                
            for bt in base_texts:
                original_key = reverse_mapping.get(bt.key, bt.key)
                resolved_texts[original_key] = {
                    "category": bt.category,
                    "default_text": bt.default_text,
                    "translations": trans_map.get(bt.key, {})
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
