"""
LiturgyBridge Wiki and AI Chatbot Router.

Defines endpoints for retrieving LiturgyWiki articles explaining terms and customs,
and hosts the Gemini-powered AI companion endpoint with static Wiki-first lookups
and contextual injection (Tone, readings, active section).
"""

import os
import uuid
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.database import get_session
from backend.app.config import settings
from backend.app.models import (
    User,
    LiturgicalService,
    LiturgicalTemplate,
    WikiArticle,
    WikiTranslation,
)
from backend.app.services.liturgical_calendar import get_liturgical_day_info

router = APIRouter(
    prefix="/wiki",
    tags=["LiturgyWiki & Chat"]
)

# --- Request Schemas ---

class WikiArticleCreate(BaseModel):
    slug: str
    category: str

class WikiTranslationSubmit(BaseModel):
    article_id: uuid.UUID
    language: str
    title: str
    content: str

class ChatRequest(BaseModel):
    question: str
    service_id: Optional[uuid.UUID] = None
    language: str = "de"


# --- Wiki Endpoints ---

@router.get("/articles")
def list_wiki_articles(
    category: Optional[str] = None,
    language: str = "de",
    session: Session = Depends(get_session)
):
    """
    Lists all LiturgyWiki articles with titles resolved for the requested language.
    """
    query = select(WikiArticle)
    if category:
        query = query.where(WikiArticle.category == category)
    articles = session.exec(query).all()

    result = []
    for art in articles:
        trans_query = select(WikiTranslation).where(
            WikiTranslation.article_id == art.id,
            WikiTranslation.language == language
        )
        trans = session.exec(trans_query).first()
        result.append({
            "id": art.id,
            "slug": art.slug,
            "category": art.category,
            "title": trans.title if trans else art.slug.capitalize(),
            "has_translation": trans is not None
        })
    return result

@router.get("/articles/{slug}")
def get_wiki_article(slug: str, language: str = "de", session: Session = Depends(get_session)):
    """
    Retrieves a specific WikiArticle and its translation body by slug.
    """
    art_query = select(WikiArticle).where(WikiArticle.slug == slug)
    art = session.exec(art_query).first()
    if not art:
        raise HTTPException(status_code=404, detail="Wiki article not found")

    trans_query = select(WikiTranslation).where(
        WikiTranslation.article_id == art.id,
        WikiTranslation.language == language
    )
    trans = session.exec(trans_query).first()

    return {
        "article": art,
        "translation": trans
    }

@router.post("/articles", response_model=WikiArticle, status_code=status.HTTP_201_CREATED)
def create_wiki_article(art_in: WikiArticleCreate, session: Session = Depends(get_session)):
    """
    Registers a new WikiArticle metadata entry (restricted to editors).
    """
    # Check duplicate
    dup = session.exec(select(WikiArticle).where(WikiArticle.slug == art_in.slug)).first()
    if dup:
        raise HTTPException(status_code=400, detail="Article slug already exists")

    db_art = WikiArticle(**art_in.model_dump())
    session.add(db_art)
    session.commit()
    session.refresh(db_art)
    return db_art

@router.post("/translations", response_model=WikiTranslation, status_code=status.HTTP_201_CREATED)
def submit_wiki_translation(trans_in: WikiTranslationSubmit, session: Session = Depends(get_session)):
    """
    Adds a localized title and content translation for a WikiArticle.
    """
    art = session.get(WikiArticle, trans_in.article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Base wiki article not found")

    # Check existing translation for language
    exist = session.exec(
        select(WikiTranslation).where(
            WikiTranslation.article_id == trans_in.article_id,
            WikiTranslation.language == trans_in.language
        )
    ).first()
    if exist:
        # Update existing
        exist.title = trans_in.title
        exist.content = trans_in.content
        exist.updated_at = datetime.now(timezone.utc)
        session.add(exist)
        session.commit()
        session.refresh(exist)
        return exist

    db_trans = WikiTranslation(**trans_in.model_dump())
    session.add(db_trans)
    session.commit()
    session.refresh(db_trans)
    return db_trans


# --- AI Chatbot Companion with Static Interception & Cost Control ---

@router.post("/chat")
def liturgy_chatbot_companion(chat_req: ChatRequest, session: Session = Depends(get_session)):
    """
    AI assistant that explains terms and prayers during a service.
    
    Cost control:
    1. Static Interception: Scans user query keywords against Wiki articles and slugs.
       If a term (like 'troparion') matches, returns the wiki text directly, skipping LLM costs.
    2. Dynamic Prompt Fallback: If not intercepted, queries Gemini API, providing the
       active liturgy section, Tone of the week, and scripture readings as context.
    """
    question_lower = chat_req.question.lower()
    
    # 1. Wiki Interception (Static Cache)
    # Search all Wiki translations for matches in titles or slugs
    translations = session.exec(select(WikiTranslation).where(WikiTranslation.language == chat_req.language)).all()
    for trans in translations:
        # Check if the title (e.g. "Troparion") or the slug is in the user question
        art_slug = session.get(WikiArticle, trans.article_id).slug
        if trans.title.lower() in question_lower or art_slug.replace("-", " ") in question_lower:
            return {
                "source": "wiki_interception",
                "message": f"**[LiturgyWiki: {trans.title}]**\n\n{trans.content}"
            }

    # 2. Context Gathering (Tone, Scripture Readings, Active Liturgy Section)
    context_str = ""
    if chat_req.service_id:
        service = session.get(LiturgicalService, chat_req.service_id)
        if service:
            template = session.get(LiturgicalTemplate, service.template_id)
            cal_info = get_liturgical_day_info(service.scheduled_time)
            
            context_str = (
                f"Active Liturgy Context:\n"
                f"- Liturgical Day: {cal_info['liturgical_day_name']}\n"
                f"- Current Tone: Tone {cal_info['tone']}\n"
                f"- Active Section Key: {service.current_section_key or 'None'}\n"
                f"- Today's Epistle: {cal_info['epistle_ref']}\n"
                f"- Today's Gospel: {cal_info['gospel_ref']}\n"
                f"- Tradition: {template.tradition if template else 'Orthodox'}\n\n"
            )

    # 3. LLM API Fallback (Interchangeable Strategy Pattern)
    from backend.app.services.llm_provider import get_llm_provider
    provider = get_llm_provider()
    
    system_instruction = (
        "You are an Orthodox liturgical assistant. Explain terms, prayers, and customs of "
        "the Orthodox liturgy accurately, respectfully, and in the requested language. "
        "Keep answers concise, clear, and easy to read. If service context is provided, "
        "relate your answer to the active liturgical day, readings, or section."
    )
    
    prompt = f"{context_str}User Question: {chat_req.question}\nRequested Language: {chat_req.language}\n"

    try:
        ai_response = provider.generate_text(prompt, system_instruction=system_instruction)
        
        # Identify provider source for transparency
        from backend.app.services.llm_provider import MockProvider, GeminiProvider, ClaudeProvider
        if isinstance(provider, MockProvider):
            source_label = f"mock_{provider.provider_name}"
        elif isinstance(provider, GeminiProvider):
            source_label = "gemini_api"
        elif isinstance(provider, ClaudeProvider):
            source_label = "claude_api"
        else:
            source_label = "llm_api"

        return {
            "source": source_label,
            "message": ai_response
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with AI service: {str(e)}"
        )
