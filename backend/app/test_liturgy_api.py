"""
Integration Tests for Liturgy API routes.

This script tests template listing/filtering, template cloning, live service updates,
and the dynamic translation overlay functionality against the PostgreSQL container.
"""

import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from backend.app.main import app
from backend.app.database import engine
from backend.app.models import User, Community, LiturgicalTemplate, TextItem, TranslationItem

def test_liturgy_api_workflow():
    # 1. Clean database state and recreate tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    # 2. Seed initial relational records directly
    with Session(engine) as session:
        # Create users
        priest_a = User(
            id=uuid.uuid4(),
            name="Priest Alexander",
            email="alexander@parish.org",
            sso_provider="nextcloud",
            external_user_id="nc_alex",
            global_roles=[]
        )
        priest_b = User(
            id=uuid.uuid4(),
            name="Priest Basil",
            email="basil@parish.org",
            sso_provider="nextcloud",
            external_user_id="nc_basil",
            global_roles=[]
        )
        community_a = Community(
            id=uuid.uuid4(),
            name="Holy Trinity Parish",
            description="Parish A",
            location="Berlin"
        )
        session.add_all([priest_a, priest_b, community_a])
        session.commit()
        
        # Keep references
        priest_a_id = priest_a.id
        priest_b_id = priest_b.id
        community_a_id = community_a.id
        
        # Create global/system template
        system_template = LiturgicalTemplate(
            id=uuid.uuid4(),
            name="Divine Liturgy of St. John Chrysostom",
            tradition="Byzantine",
            structure={
                "name": "Divine Liturgy",
                "sections": [
                    {
                        "section_key": "litany.peace",
                        "text_keys": ["great_litany.lord_have_mercy", "great_litany.amen"]
                    }
                ]
            },
            author_id=None,
            is_shared=True
        )
        session.add(system_template)
        session.commit()
        system_template_id = system_template.id

        # Seed text items
        text_1 = TextItem(
            key="great_litany.lord_have_mercy",
            category="litany",
            default_text="Lord, have mercy."
        )
        text_2 = TextItem(
            key="great_litany.amen",
            category="litany",
            default_text="Amen."
        )
        session.add_all([text_1, text_2])
        session.commit()

        # Seed translation overlays
        trans_de = TranslationItem(
            text_key="great_litany.lord_have_mercy",
            language="de",
            translation_text="Herr, erbarme Dich.",
            approved=True
        )
        trans_cu = TranslationItem(
            text_key="great_litany.lord_have_mercy",
            language="cu",
            translation_text="Господи помилуй.",
            approved=True
        )
        session.add_all([trans_de, trans_cu])
        session.commit()

    # 3. Perform Test Client API requests
    client = TestClient(app)

    # A. Retrieve System Templates
    response = client.get("/api/v1/liturgy/templates?scope=system")
    assert response.status_code == 200, response.text
    templates = response.json()
    assert len(templates) == 1
    assert templates[0]["name"] == "Divine Liturgy of St. John Chrysostom"
    assert templates[0]["author_id"] is None

    # B. Priest A clones the system template
    clone_response = client.post(
        f"/api/v1/liturgy/templates/{system_template_id}/clone",
        json={"current_user_id": str(priest_a_id)}
    )
    assert clone_response.status_code == 201
    cloned_template = clone_response.json()
    assert cloned_template["name"] == "Copy of Divine Liturgy of St. John Chrysostom"
    assert cloned_template["author_id"] == str(priest_a_id)
    assert cloned_template["is_shared"] is False
    cloned_id = cloned_template["id"]

    # C. Priest A lists their personal templates
    personal_response = client.get(f"/api/v1/liturgy/templates?scope=personal&user_id={priest_a_id}")
    assert personal_response.status_code == 200
    assert len(personal_response.json()) == 1

    # D. Priest B tries to view Priest A's private template (should be omitted)
    b_view_response = client.get(f"/api/v1/liturgy/templates?user_id={priest_b_id}")
    assert b_view_response.status_code == 200
    b_visible_ids = [t["id"] for t in b_view_response.json()]
    assert str(cloned_id) not in b_visible_ids  # Private template is hidden

    # E. Priest A marks their template as shared (updates in DB)
    with Session(engine) as session:
        tmpl = session.get(LiturgicalTemplate, uuid.UUID(cloned_id))
        tmpl.is_shared = True
        session.add(tmpl)
        session.commit()

    # F. Priest B now searches for shared templates (should see it)
    shared_response = client.get(f"/api/v1/liturgy/templates?scope=shared&user_id={priest_b_id}")
    assert shared_response.status_code == 200
    shared_ids = [t["id"] for t in shared_response.json()]
    assert str(cloned_id) in shared_ids

    # G. Priest B clones the shared template
    clone_b_response = client.post(
        f"/api/v1/liturgy/templates/{cloned_id}/clone",
        json={"current_user_id": str(priest_b_id)}
    )
    assert clone_b_response.status_code == 201
    assert clone_b_response.json()["author_id"] == str(priest_b_id)

    # H. Priest A schedules a live service using their cloned template
    service_response = client.post(
        "/api/v1/liturgy/services",
        json={
            "template_id": cloned_id,
            "community_id": str(community_a_id),
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "active_languages": ["de", "cu"]
        }
    )
    assert service_response.status_code == 201
    service = service_response.json()
    service_id = service["id"]
    assert service["status"] == "draft"

    # I. Priest A updates/starts the service and progresses the scroll point
    patch_response = client.patch(
        f"/api/v1/liturgy/services/{service_id}",
        json={
            "status": "active",
            "current_section_key": "litany.peace"
        }
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["current_section_key"] == "litany.peace"
    assert patch_response.json()["status"] == "active"

    # J. Visitor fetches service details with translation overlays resolved
    details_response = client.get(f"/api/v1/liturgy/services/{service_id}?languages=de,cu")
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["service"]["id"] == service_id
    assert details["template"]["id"] == cloned_id
    
    # Check that text items are resolved with translations
    texts = details["texts"]
    assert "great_litany.lord_have_mercy" in texts
    assert texts["great_litany.lord_have_mercy"]["default_text"] == "Lord, have mercy."
    assert texts["great_litany.lord_have_mercy"]["translations"]["de"] == "Herr, erbarme Dich."
    assert texts["great_litany.lord_have_mercy"]["translations"]["cu"] == "Господи помилуй."

    # K. Test Bookmarks and User Notes CRUD
    bookmark_response = client.post(
        "/api/v1/liturgy/bookmarks",
        json={
            "user_id": str(priest_b_id),
            "service_id": service_id,
            "section_key": "litany.peace"
        }
    )
    assert bookmark_response.status_code == 201
    
    bookmarks_get = client.get(f"/api/v1/liturgy/bookmarks?user_id={priest_b_id}")
    assert bookmarks_get.status_code == 200
    assert len(bookmarks_get.json()) == 1
    assert bookmarks_get.json()[0]["section_key"] == "litany.peace"

    note_response = client.post(
        "/api/v1/liturgy/notes",
        json={
            "user_id": str(priest_b_id),
            "text_key": "great_litany.lord_have_mercy",
            "content": "Sermon reflection note"
        }
    )
    assert note_response.status_code == 201
    
    notes_get = client.get(f"/api/v1/liturgy/notes?user_id={priest_b_id}")
    assert notes_get.status_code == 200
    assert len(notes_get.json()) == 1
    assert notes_get.json()[0]["content"] == "Sermon reflection note"

    print("API INTEGRATION TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_liturgy_api_workflow()
