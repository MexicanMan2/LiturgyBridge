"""
Tests for the Orthodox Liturgical Calendar Service, Wiki CRUD, and Chatbot.

Verifies Easter calculations, Tone rotations, Wiki-first query interception,
and calendar-resolved text placeholder swaps inside scheduled services.
"""

import uuid
from datetime import date, datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from backend.app.main import app
from backend.app.database import engine
from backend.app.services.liturgical_calendar import calculate_orthodox_pascha, get_liturgical_day_info
from backend.app.models import (
    User,
    Community,
    LiturgicalTemplate,
    LiturgicalService,
    TextItem,
    TranslationItem,
    WikiArticle,
    WikiTranslation,
)

def test_liturgical_features_workflow():
    # 1. Reset tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    # 2. Verify Easter algorithm calculations
    # 2026: April 12 (Coinciding with Western Easter)
    # 2027: May 2
    assert calculate_orthodox_pascha(2026) == date(2026, 4, 12)
    assert calculate_orthodox_pascha(2027) == date(2027, 5, 2)
    print("Pascha date calculations match Meeus' algorithm!")

    # Verify Tone calculation
    # Thomas Sunday in 2026 is April 19 (1 week after Pascha) -> Tone 1
    assert get_liturgical_day_info(datetime(2026, 4, 19))["tone"] == 1
    # 5th Sunday after Pentecost in 2026 is July 12 (weeks_since_pascha = 13)
    # weeks_since = 13 -> Thomas Sunday (1) = Tone 1, Thomas+1 (2) = Tone 2... Tone = ((13-1)%8)+1 = (12%8)+1 = 4+1 = 5?
    # Wait, Thomas Sunday (weeks_since=1) is Tone 1.
    # weeks_since = 13 -> Thomas Sunday (1) -> Tone 1.
    # Tone = ((13 - 1) % 8) + 1 = 5. Correct!
    assert get_liturgical_day_info(datetime(2026, 7, 12))["tone"] == 5

    # 3. Seed data
    with Session(engine) as session:
        # Create users/community
        priest = User(id=uuid.uuid4(), name="Fr. John", email="john@gmail.com", sso_provider="nextcloud", external_user_id="nc_1")
        community = Community(id=uuid.uuid4(), name="St. Nicholas Parish", location="Berlin")
        session.add_all([priest, community])
        session.commit()
        
        priest_id = priest.id
        community_id = community.id

        # Seed Wiki Article on Troparion
        wiki_art = WikiArticle(id=uuid.uuid4(), slug="troparion", category="terminology")
        session.add(wiki_art)
        session.commit()
        
        wiki_trans = WikiTranslation(
            article_id=wiki_art.id,
            language="de",
            title="Troparion",
            content="Ein Troparion ist ein kurzer Hymnus in der orthodoxen Liturgie, der das Wesen eines Festes erklärt."
        )
        session.add(wiki_trans)
        session.commit()

        # Seed text item library (Tone 5 Troparion for our Sunday July 12, 2026 service)
        tonal_troparion_text = TextItem(
            key="oktoechos.tone_5.troparion",
            category="litany",
            default_text="Let us, the faithful, praise and worship the Word..."
        )
        # Translation
        tonal_troparion_trans = TranslationItem(
            text_key="oktoechos.tone_5.troparion",
            language="de",
            translation_text="Lasset uns, ihr Gläubigen, das Wort preisen und anbeten...",
            approved=True
        )
        session.add_all([tonal_troparion_text, tonal_troparion_trans])
        session.commit()

        # Seed a template referencing dynamic calendar placeholders
        template = LiturgicalTemplate(
            id=uuid.uuid4(),
            name="Sunday Divine Liturgy Template",
            tradition="Byzantine",
            structure={
                "name": "Divine Liturgy",
                "sections": [
                    {
                        "section_key": "entrance.troparia",
                        "text_keys": ["dynamic.tonal_troparion"] # Dynamic placeholder key
                    }
                ]
            }
        )
        session.add(template)
        session.commit()
        template_id = template.id

    client = TestClient(app)

    # 4. Verify Wiki Article retrieval endpoints
    response = client.get("/api/v1/wiki/articles")
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) == 1
    assert articles[0]["slug"] == "troparion"
    assert articles[0]["title"] == "Troparion"

    detail_response = client.get("/api/v1/wiki/articles/troparion?language=de")
    assert detail_response.status_code == 200
    assert detail_response.json()["translation"]["content"].startswith("Ein Troparion")

    # 5. Verify Chatbot static interception (Cost Control Check)
    # Question mentions "troparion" -> should intercept and return Wiki translation content
    chat_response = client.post(
        "/api/v1/wiki/chat",
        json={"question": "Was ist ein Troparion?", "language": "de"}
    )
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert data["source"] == "wiki_interception"
    assert "Ein Troparion ist ein kurzer Hymnus" in data["message"]
    print("Static Wiki-First query interception works!")

    # Question does NOT mention any wiki keywords -> should fallback to LLM provider (mocked in tests)
    ai_response = client.post(
        "/api/v1/wiki/chat",
        json={"question": "Wie läuft der Gottesdienst ab?", "language": "de"}
    )
    assert ai_response.status_code == 200
    ai_data = ai_response.json()
    assert ai_data["source"] == "mock_gemini"
    assert "Prompt received:" in ai_data["message"]
    print("Gemini mock provider routing works!")

    # Test dynamic LLM Provider Swapping
    from backend.app.config import settings as app_settings
    app_settings.LLM_PROVIDER = "claude"
    
    claude_response = client.post(
        "/api/v1/wiki/chat",
        json={"question": "Wie läuft der Gottesdienst ab?", "language": "de"}
    )
    assert claude_response.status_code == 200
    claude_data = claude_response.json()
    assert claude_data["source"] == "mock_claude"
    assert "[AI Assistant Mock (CLAUDE)]" in claude_data["message"]
    print("Claude mock provider routing and dynamic swapping works!")
    
    # Revert setting
    app_settings.LLM_PROVIDER = "gemini"

    # 6. Verify Dynamic Calendar Placeholder Resolution inside Liturgy Services
    # Schedule service for July 12, 2026 (5th Sunday after Pentecost -> Tone 5)
    service_date = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    schedule_response = client.post(
        "/api/v1/liturgy/services",
        json={
            "template_id": str(template_id),
            "community_id": str(community_id),
            "scheduled_time": service_date.isoformat(),
            "active_languages": ["de"]
        }
    )
    assert schedule_response.status_code == 201
    service_id = schedule_response.json()["id"]

    # Fetch details for the service run with de language overlay resolved
    details_response = client.get(f"/api/v1/liturgy/services/{service_id}?languages=de")
    assert details_response.status_code == 200
    details = details_response.json()
    
    # Assert placeholder key was resolved dynamically to the correct Tone 5 Troparion!
    # The frontend still queries 'dynamic.tonal_troparion' but receives the Tone 5 content!
    texts = details["texts"]
    assert "dynamic.tonal_troparion" in texts
    assert texts["dynamic.tonal_troparion"]["default_text"] == "Let us, the faithful, praise and worship the Word..."
    assert texts["dynamic.tonal_troparion"]["translations"]["de"] == "Lasset uns, ihr Gläubigen, das Wort preisen und anbeten..."
    print("Dynamic Calendar Placeholder Resolution verified successfully!")

    print("ALL CALENDAR, WIKI, AND CHATBOT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_liturgical_features_workflow()
