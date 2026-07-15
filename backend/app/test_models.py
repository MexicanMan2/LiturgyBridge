import uuid
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel, create_engine, select
from backend.app.models import (
    User,
    Community,
    Membership,
    LiturgicalTemplate,
    LiturgicalService,
    Event,
    TextItem,
    TranslationItem,
    Resource,
    Notification,
    Bookmark,
    UserNote,
)

def test_liturgy_bridge_models():
    # 1. Setup in-memory database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 2. Seed User & Community
        user_a = User(
            name="John Doe",
            email="john@example.com",
            sso_provider="nextcloud",
            external_user_id="nc_user_123",
            global_roles=["translator"],
        )
        community_a = Community(
            name="St. Nicholas Parish",
            description="A local orthodox community",
            location="Munich, Germany",
        )
        session.add(user_a)
        session.add(community_a)
        session.commit()
        session.refresh(user_a)
        session.refresh(community_a)

        # 3. Create Membership with community-specific roles
        membership = Membership(
            user_id=user_a.id,
            community_id=community_a.id,
            community_roles=["priest", "administrator"],
        )
        session.add(membership)
        session.commit()

        # 4. Create a Liturgical Template with nested JSON structure
        template_struct = {
            "version": "1.0",
            "sections": [
                {
                    "key": "litany.great_peace",
                    "type": "litany",
                    "text_items": ["great_litany.lord_have_mercy"],
                },
                {
                    "key": "hymn.cherubic",
                    "type": "hymn",
                    "text_items": ["cherubic_hymn.main"],
                }
            ]
        }
        template = LiturgicalTemplate(
            name="Sunday Divine Liturgy",
            tradition="Byzantine",
            structure=template_struct,
        )
        session.add(template)
        session.commit()
        session.refresh(template)

        # 5. Create Text Items & Translations
        text_item_1 = TextItem(
            key="great_litany.lord_have_mercy",
            category="litany",
            default_text="Господи помилуй",
        )
        text_item_2 = TextItem(
            key="local.parish_announcement",
            category="announcement",
            default_text="Gottesdienst beginnt am Sonntag um 10:00 Uhr.",
            community_id=community_a.id, # Local community text
        )
        session.add(text_item_1)
        session.add(text_item_2)
        session.commit()

        translation = TranslationItem(
            text_key=text_item_1.key,
            language="de",
            translation_text="Herr, erbarme dich.",
            approved=True,
            author_id=user_a.id,
        )
        session.add(translation)
        session.commit()

        # 6. Create active Liturgical Service
        service = LiturgicalService(
            template_id=template.id,
            community_id=community_a.id,
            scheduled_time=datetime.now(timezone.utc),
            status="active",
            current_section_key="litany.great_peace",
            active_languages=["cu", "de"],
        )
        session.add(service)
        session.commit()
        session.refresh(service)

        # 7. Create a Bookmark & UserNote (Reader Features)
        bookmark = Bookmark(
            user_id=user_a.id,
            service_id=service.id,
            section_key="litany.great_peace",
        )
        note = UserNote(
            user_id=user_a.id,
            text_key=text_item_1.key,
            content="This response is sung three times.",
        )
        session.add(bookmark)
        session.add(note)
        session.commit()

        # 8. Query verification
        # Retrieve User and verify communities and roles
        queried_user = session.exec(select(User).where(User.email == "john@example.com")).first()
        assert queried_user is not None
        assert queried_user.name == "John Doe"
        assert queried_user.global_roles == ["translator"]
        assert len(queried_user.communities) == 1
        assert queried_user.communities[0].name == "St. Nicholas Parish"

        # Check membership roles
        queried_membership = session.exec(
            select(Membership).where(
                Membership.user_id == user_a.id,
                Membership.community_id == community_a.id
            )
        ).first()
        assert queried_membership is not None
        assert "priest" in queried_membership.community_roles

        # Verify template JSON parsing
        queried_template = session.exec(select(LiturgicalTemplate).where(LiturgicalTemplate.id == template.id)).first()
        assert queried_template.structure["sections"][0]["key"] == "litany.great_peace"

        # Verify translation links
        queried_text = session.exec(select(TextItem).where(TextItem.key == "great_litany.lord_have_mercy")).first()
        assert len(queried_text.translations) == 1
        assert queried_text.translations[0].translation_text == "Herr, erbarme dich."

        # Verify Local Text Item vs Global
        assert queried_text.community_id is None
        queried_local_text = session.exec(select(TextItem).where(TextItem.key == "local.parish_announcement")).first()
        assert queried_local_text.community_id == community_a.id

        # Verify Reader features (Bookmarks & Notes)
        assert len(queried_user.bookmarks) == 1
        assert queried_user.bookmarks[0].section_key == "litany.great_peace"
        assert len(queried_user.notes) == 1
        assert queried_user.notes[0].content == "This response is sung three times."

        print("SUCCESS: All models and relationships verified successfully!")

if __name__ == "__main__":
    test_liturgy_bridge_models()
