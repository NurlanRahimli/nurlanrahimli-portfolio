from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import AdminUser, MediaAsset, Skill


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_headers(db_session: Session) -> dict[str, str]:
    admin = AdminUser(
        email="skills-admin@example.com",
        hashed_password="unused-test-hash",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token(str(admin.id))
    return {
        "Authorization": f"Bearer {token}",
    }


def create_image_asset(
    db_session: Session,
    *,
    name: str = "python.png",
) -> MediaAsset:
    asset = MediaAsset(
        filename=name,
        original_filename=name,
        storage_key=f"media/images/{name}",
        mime_type="image/png",
        file_type="image",
        file_size=1024,
        width=512,
        height=512,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def create_document_asset(db_session: Session) -> MediaAsset:
    asset = MediaAsset(
        filename="resume.pdf",
        original_filename="resume.pdf",
        storage_key="media/documents/resume.pdf",
        mime_type="application/pdf",
        file_type="document",
        file_size=2048,
        width=None,
        height=None,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_skills_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/skills")
    assert response.status_code == 401


def test_create_and_get_skill(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    asset = create_image_asset(db_session)

    response = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "  Python  ",
            "media_asset_id": asset.id,
            "is_active": True,
        },
    )

    assert response.status_code == 201
    body = response.json()

    assert body["name"] == "Python"
    assert body["media_asset_id"] == asset.id
    assert body["is_active"] is True
    assert body["display_order"] == 0
    assert body["image_url"]
    assert "id" in body

    detail = client.get(
        f"/api/v1/skills/{body['id']}",
        headers=authenticated_headers,
    )

    assert detail.status_code == 200
    assert detail.json()["name"] == "Python"


def test_create_skill_rejects_missing_media(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "React",
            "media_asset_id": 999999,
            "is_active": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The selected skill logo does not exist."


def test_create_skill_rejects_document_media(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    document = create_document_asset(db_session)

    response = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "PostgreSQL",
            "media_asset_id": document.id,
            "is_active": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Skill logos must use image media assets."


def test_skill_names_are_required(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    asset = create_image_asset(db_session)

    response = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "   ",
            "media_asset_id": asset.id,
            "is_active": True,
        },
    )

    assert response.status_code == 422


def test_skills_append_display_order(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    first_asset = create_image_asset(db_session, name="python.png")
    second_asset = create_image_asset(db_session, name="react.png")

    first = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": first_asset.id,
            "is_active": True,
        },
    )
    second = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "React",
            "media_asset_id": second_asset.id,
            "is_active": True,
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["display_order"] == 0
    assert second.json()["display_order"] == 1


def test_list_skills_supports_search_and_status_filter(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    python_asset = create_image_asset(db_session, name="python.png")
    react_asset = create_image_asset(db_session, name="react.png")

    client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": python_asset.id,
            "is_active": True,
        },
    )
    client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "React",
            "media_asset_id": react_asset.id,
            "is_active": False,
        },
    )

    search = client.get(
        "/api/v1/skills?search=pyth",
        headers=authenticated_headers,
    )
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["name"] == "Python"

    inactive = client.get(
        "/api/v1/skills?is_active=false",
        headers=authenticated_headers,
    )
    assert inactive.status_code == 200
    assert inactive.json()["total"] == 1
    assert inactive.json()["items"][0]["name"] == "React"


def test_update_skill(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    python_asset = create_image_asset(db_session, name="python.png")
    fastapi_asset = create_image_asset(db_session, name="fastapi.png")

    created = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": python_asset.id,
            "is_active": True,
        },
    ).json()

    response = client.put(
        f"/api/v1/skills/{created['id']}",
        headers=authenticated_headers,
        json={
            "name": "FastAPI",
            "media_asset_id": fastapi_asset.id,
            "is_active": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "FastAPI"
    assert body["media_asset_id"] == fastapi_asset.id
    assert body["is_active"] is False
    assert body["display_order"] == created["display_order"]


def test_reorder_skills(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    first_asset = create_image_asset(db_session, name="python.png")
    second_asset = create_image_asset(db_session, name="react.png")

    first = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": first_asset.id,
            "is_active": True,
        },
    ).json()

    second = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "React",
            "media_asset_id": second_asset.id,
            "is_active": True,
        },
    ).json()

    response = client.post(
        "/api/v1/skills/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": second["id"], "display_order": 0},
                {"id": first["id"], "display_order": 1},
            ]
        },
    )

    assert response.status_code == 204

    listing = client.get(
        "/api/v1/skills",
        headers=authenticated_headers,
    ).json()

    assert [item["name"] for item in listing["items"]] == [
        "React",
        "Python",
    ]


def test_reorder_rejects_duplicate_ids(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    asset = create_image_asset(db_session)

    skill = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": asset.id,
            "is_active": True,
        },
    ).json()

    response = client.post(
        "/api/v1/skills/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": skill["id"], "display_order": 0},
                {"id": skill["id"], "display_order": 1},
            ]
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Each skill can only appear once in a reorder request."
    )


def test_delete_skill_preserves_media_asset(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    asset = create_image_asset(db_session)

    skill = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": asset.id,
            "is_active": True,
        },
    ).json()

    response = client.delete(
        f"/api/v1/skills/{skill['id']}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert db_session.get(Skill, skill["id"]) is None
    assert db_session.get(MediaAsset, asset.id) is not None


def test_public_skills_only_return_active_items_in_order(
    client: TestClient,
    db_session: Session,
    authenticated_headers: dict[str, str],
) -> None:
    python_asset = create_image_asset(db_session, name="python.png")
    react_asset = create_image_asset(db_session, name="react.png")
    docker_asset = create_image_asset(db_session, name="docker.png")

    python = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Python",
            "media_asset_id": python_asset.id,
            "is_active": True,
        },
    ).json()

    react = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "React",
            "media_asset_id": react_asset.id,
            "is_active": False,
        },
    ).json()

    docker = client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "name": "Docker",
            "media_asset_id": docker_asset.id,
            "is_active": True,
        },
    ).json()

    reorder = client.post(
        "/api/v1/skills/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": docker["id"], "display_order": 0},
                {"id": react["id"], "display_order": 1},
                {"id": python["id"], "display_order": 2},
            ]
        },
    )
    assert reorder.status_code == 204

    response = client.get("/api/v1/public/skills")

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 2
    assert [item["name"] for item in body["items"]] == [
        "Docker",
        "Python",
    ]

    assert set(body["items"][0]) == {
        "name",
        "image_url",
        "thumbnail_url",
    }


def test_missing_skill_returns_404(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/skills/999999",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Skill not found."
