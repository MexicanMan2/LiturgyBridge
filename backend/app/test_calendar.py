"""
Tests for the Orthodox Liturgical Calendar Service, Wiki CRUD, Chatbot,
Parish Audio Sharing, and Cloud TTS Integration.

Verifies Easter calculations, Tone rotations, Wiki-first query interception,
aligned Slavonic/German layouts, parish choir recordings resolution, and
TTS bootstrapping under PostgreSQL.
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
    AudioTrack,
    WikiArticle,
    WikiTranslation,
)
from backend.app.seed_liturgy import seed_database

def test_liturgical_features_workflow():
    # 1. Reset tables and run seed script
    SQLModel.metadata.drop_all(engine)
    seed_database()
    print("Database schema reset and seeded with St. John Chrysostom Liturgy library!")

    # 2. Verify Easter algorithm calculations
    assert calculate_orthodox_pascha(2026) == date(2026, 4, 12)
    assert calculate_orthodox_pascha(2027) == date(2027, 5, 2)
    print("Pascha date calculations verified successfully.")

    # Verify Tone calculation
    assert get_liturgical_day_info(datetime(2026, 4, 19))["tone"] == 1
    assert get_liturgical_day_info(datetime(2026, 7, 12))["tone"] == 5

    # 3. Seed Wiki Article description for Chatbot interception tests
    with Session(engine) as session:
        wiki_art = WikiArticle(id=uuid.uuid4(), slug="troparion", category="terminology")
        session.add(wiki_art)
        session.commit()
        
        wiki_trans = WikiTranslation(
            article_id=wiki_art.id,
            language="de",
            title="Troparion",
            content="Ein Troparion ist ein kurzer Hymnus in der orthodoxen Liturgie."
        )
        session.add(wiki_trans)
        session.commit()

    client = TestClient(app)

    # 4. Verify Wiki Article retrieval endpoints
    response = client.get("/api/v1/wiki/articles")
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) == 1
    assert articles[0]["slug"] == "troparion"

    # 5. Verify Chatbot static interception (Cost Control Check)
    # Question mentions "troparion" -> should intercept and return Wiki translation content
    chat_response = client.post(
        "/api/v1/wiki/chat",
        json={"question": "Was ist ein Troparion?", "language": "de"}
    )
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert data["source"] == "wiki_interception"
    assert "Ein Troparion" in data["message"]
    print("Static Wiki-First query interception verified successfully.")

    # Question does NOT mention any wiki keywords -> should fallback to LLM provider (mocked in tests)
    ai_response = client.post(
        "/api/v1/wiki/chat",
        json={"question": "Wie lautet das Glaubensbekenntnis?", "language": "de"}
    )
    assert ai_response.status_code == 200
    ai_data = ai_response.json()
    assert ai_data["source"] == "mock_gemini"
    print("Gemini LLM Provider strategy routing verified successfully.")

    # Test dynamic LLM Provider Swapping
    from backend.app.config import settings as app_settings
    app_settings.LLM_PROVIDER = "claude"
    
    claude_response = client.post(
        "/api/v1/wiki/chat",
        json={"question": "Wie lautet das Glaubensbekenntnis?", "language": "de"}
    )
    assert claude_response.status_code == 200
    claude_data = claude_response.json()
    assert claude_data["source"] == "mock_claude"
    print("Claude LLM Provider strategy routing verified successfully.")
    
    # Revert setting
    app_settings.LLM_PROVIDER = "gemini"

    # 6. Verify Dynamic Calendar Placeholder & Aligned Translations Resolution
    # Schedule service for next Sunday: July 19, 2026 (6th Sunday after Pentecost -> Tone 6)
    service_date = datetime(2026, 7, 19, 10, 0, 0, tzinfo=timezone.utc)
    template_id = "a9fb5917-a068-4592-80de-df619280d922"
    community_id = "87a935b6-6124-4f7c-8b9c-8605ef4dad87"
    
    schedule_response = client.post(
        "/api/v1/liturgy/services",
        json={
            "template_id": template_id,
            "community_id": community_id,
            "scheduled_time": service_date.isoformat(),
            "active_languages": ["de", "cu", "en"] # Request German, Church Slavonic, and English overlays
        }
    )
    assert schedule_response.status_code == 201
    service_id = schedule_response.json()["id"]

    # Fetch details for the service run with German, Church Slavonic, and English overlays resolved
    details_response = client.get(f"/api/v1/liturgy/services/{service_id}?languages=de,cu,en")
    assert details_response.status_code == 200
    details = details_response.json()
    
    texts = details["texts"]
    
    # A. Assert dynamic Tone 6 troparion resolved correctly in both languages
    assert "dynamic.tonal_troparion" in texts
    assert "Engelsmächte" in texts["dynamic.tonal_troparion"]["translations"]["de"]
    assert "Ангельския силы" in texts["dynamic.tonal_troparion"]["translations"]["cu"]
    print("Dynamic Calendar Tonal Troparion placeholder resolved in German and Church Slavonic!")

    # B. Assert dynamic Rom 12:1-10 Epistle reading resolved correctly
    assert "dynamic.epistle_reading" in texts
    assert "Römer 12,1-10" in texts["dynamic.epistle_reading"]["translations"]["de"]
    assert "Римлянам 12:1-10" in texts["dynamic.epistle_reading"]["translations"]["cu"]
    print("Dynamic Calendar Epistle Reading placeholder resolved in German and Church Slavonic!")

    # C. Assert aligned static texts exist side-by-side (e.g. Lord's Prayer)
    assert "liturgy.lords_prayer.main" in texts
    assert "Vater unser" in texts["liturgy.lords_prayer.main"]["translations"]["de"]
    assert "Отче наш" in texts["liturgy.lords_prayer.main"]["translations"]["cu"]
    print("Aligned static texts resolved in German and Church Slavonic!")

    # D. Assert AudioTrack resolution (Community-shared Cherubic Hymn vs System Default vs TTS fallback)
    # Cherubic Hymn should select St. Nicholas Choir recording (since community matches Berlin)
    assert "liturgy.cherubic_hymn.main" in texts
    cherubic_audio_url = texts["liturgy.cherubic_hymn.main"]["audio_url"]
    assert "/api/v1/liturgy/audio-tracks/" in cherubic_audio_url
    assert "/stream" in cherubic_audio_url
    
    # Request the stream route to fetch raw database bytes
    cherubic_stream = client.get(cherubic_audio_url)
    assert cherubic_stream.status_code == 200
    assert cherubic_stream.content == b"MOCK_ST_NICHOLAS_CHOIR_RECORDING_BYTES_MP3"
    print("Community-shared choral recording bytes fetched from database successfully!")

    # Creed should select system default pre-recorded track
    assert "liturgy.creed.main" in texts
    creed_audio_url = texts["liturgy.creed.main"]["audio_url"]
    assert "/api/v1/liturgy/audio-tracks/" in creed_audio_url
    
    creed_stream = client.get(creed_audio_url)
    assert creed_stream.status_code == 200
    assert b"MOCK_DEFAULT_AUDIO_DATA_FOR_liturgy.creed.main" in creed_stream.content
    print("System default database audio track bytes fetched successfully!")

    # Sermon placeholder has no pre-recorded track -> should return fallback dynamic TTS streaming link
    assert "liturgy.sermon_placeholder" in texts
    assert "/api/v1/liturgy/tts?text=" in texts["liturgy.sermon_placeholder"]["audio_url"]
    print("Dynamic Text-to-Speech fallback URL generated correctly!")

    # 7. Verify Cloud-Based TTS Streaming Route
    tts_response = client.get("/api/v1/liturgy/tts?text=Test&language=de")
    assert tts_response.status_code == 200
    assert b"MOCK_MP3_AUDIO_DATA" in tts_response.content
    print("Cloud-based TTS streaming endpoint verified successfully.")

    # 8. Verify YouTube Audio Importer
    yt_import_response = client.post(
        "/api/v1/liturgy/audio-tracks/import-youtube",
        params={
            "text_key": "liturgy.opening_blessing",
            "language": "de",
            "youtube_url": "https://www.youtube.com/watch?v=TEST_ID_123",
            "description": "YouTube Byzantine Chant Test"
        }
    )
    assert yt_import_response.status_code == 201
    yt_track = yt_import_response.json()
    assert "/api/v1/liturgy/audio-tracks/" in yt_track["audio_url"]
    
    # Request raw bytes from YouTube import stream
    yt_stream = client.get(yt_track["audio_url"])
    assert yt_stream.status_code == 200
    assert b"MOCK_YOUTUBE_AUDIO_BYTES_FROM_https://www.youtube.com/watch?v=TEST_ID_123" in yt_stream.content
    print("YouTube Audio Importer and streaming extraction verified successfully.")

    # 9. Verify TTS Bootstrapping (creates default MP3 files directly in database)
    bootstrap_response = client.post("/api/v1/liturgy/audio-tracks/bootstrap?language=de")
    assert bootstrap_response.status_code == 200
    assert "fallback TTS audio in database." in bootstrap_response.json()["message"]
    print("TTS database bootstrapping mechanism verified successfully.")

    # 10. Verify Dynamic Priest Sermon Editing, Translation, and TTS Synthesis
    sermon_response = client.put(
        f"/api/v1/liturgy/services/{service_id}/sermon",
        json={
            "text": "Liebe Gemeinde, am heutigen Sonntag gedenken wir...",
            "language": "de"
        }
    )
    assert sermon_response.status_code == 200
    sermon_data = sermon_response.json()
    assert sermon_data["sermon_key"] == f"sermon.service_{service_id}"
    
    # Assert translations contains de and en
    langs = [t["language"] for t in sermon_data["translations"]]
    assert "de" in langs
    assert "en" in langs
    assert "cu" not in langs  # EXCLUDE Church Slavonic!
    print("Sermon translations generated successfully (excluding Church Slavonic)!")

    # Fetch service details again and assert the sermon placeholder points to the service-specific sermon
    service_details = client.get(f"/api/v1/liturgy/services/{service_id}?languages=de,en").json()
    texts = service_details["texts"]
    assert "liturgy.sermon_placeholder" in texts
    sermon_text_item = texts["liturgy.sermon_placeholder"]
    assert "Liebe Gemeinde" in sermon_text_item["translations"]["de"]
    assert "en" in sermon_text_item["translations"]
    
    # Verify AudioTrack was generated for the translated sermon
    sermon_audio_url = sermon_text_item["audio_url"]
    assert "/api/v1/liturgy/audio-tracks/" in sermon_audio_url
    assert "/stream" in sermon_audio_url
    
    # Request the audio stream
    sermon_stream = client.get(sermon_audio_url)
    assert sermon_stream.status_code == 200
    assert b"MOCK_MP3_AUDIO_DATA" in sermon_stream.content
    # 11. Verify Dynamic Scripture Resolution in 5 Languages (cu, ru, uk, de, en)
    # Schedule a service for August 2, 2026 (a date whose readings are not seeded in the database)
    aug_service_date = datetime(2026, 8, 2, 10, 0, 0, tzinfo=timezone.utc)
    aug_schedule_response = client.post(
        "/api/v1/liturgy/services",
        json={
            "template_id": template_id,
            "community_id": community_id,
            "scheduled_time": aug_service_date.isoformat(),
            "active_languages": ["de", "cu", "ru", "uk", "en"]
        }
    )
    assert aug_schedule_response.status_code == 201
    aug_service_id = aug_schedule_response.json()["id"]
    
    # Querying details triggers dynamic resolution and caching of August 2 scripture readings
    aug_details_response = client.get(
        f"/api/v1/liturgy/services/{aug_service_id}?languages=de,cu,ru,uk,en"
    )
    assert aug_details_response.status_code == 200
    aug_details = aug_details_response.json()
    aug_texts = aug_details["texts"]
    
    # Assert dynamic readings exist and contain all 5 requested translations!
    assert "dynamic.epistle_reading" in aug_texts
    epistle_item = aug_texts["dynamic.epistle_reading"]
    assert "de" in epistle_item["translations"]
    assert "cu" in epistle_item["translations"]
    assert "ru" in epistle_item["translations"]
    assert "uk" in epistle_item["translations"]
    assert "en" in epistle_item["translations"]
    
    # Verify German TTS audio was synthesized and registered in the database for the new scripture
    epistle_audio_url = epistle_item["audio_url"]
    assert "/api/v1/liturgy/audio-tracks/" in epistle_audio_url
    epistle_stream = client.get(epistle_audio_url)
    assert epistle_stream.status_code == 200
    assert b"MOCK_MP3_AUDIO_DATA" in epistle_stream.content
    print("Dynamic 5-language Scripture Resolution and TTS audio synthesis verified successfully!")

    print("ALL CALENDAR, WIKI, CHATBOT, AUDIOTRACK, TTS, SERMON, AND SCRIPTURE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_liturgical_features_workflow()
