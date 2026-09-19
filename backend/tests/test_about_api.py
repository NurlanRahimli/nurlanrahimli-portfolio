from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import AboutContent, AdminUser, MediaAsset


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(
        dbapi_connection,
        connection_record,
    ) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with testing_session_local() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(
    db_session: Session,
) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_headers(
    db_session: Session,
) -> dict[str, str]:
    admin = AdminUser(
        email="about-admin@example.com",
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
    filename: str = "profile.webp",
) -> MediaAsset:
    asset = MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/images/test/{filename}",
        mime_type="image/webp",
        file_type="image",
        file_size=100,
        width=800,
        height=800,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def create_document_asset(
    db_session: Session,
    *,
    filename: str = "resume.pdf",
    mime_type: str = "application/pdf",
) -> MediaAsset:
    asset = MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/documents/test/{filename}",
        mime_type=mime_type,
        file_type="document",
        file_size=100,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def valid_payload() -> dict:
    return {
        "full_name": "Nurlan Rahimli",
        "profile_media_asset_id": None,
        "resume_media_asset_id": None,
        "about_html": (
            "<p>Software Engineer building "
            "<strong>production applications</strong>.</p>"
        ),
        "experience_years": 3,
        "location": "Sacramento, California",
        "is_available": True,
        "availability_modes": ["remote", "onsite"],
        "software_fields": [
            {"name": "Software Engineer"},
            {"name": "AI Engineer"},
        ],
        "social_links": [
            {
                "platform": "GitHub",
                "url": "https://github.com/NurlanRahimli",
            },
            {
                "platform": "LinkedIn",
                "url": "https://www.linkedin.com/in/nurlan-rahimli",
            },
        ],
    }


def test_admin_about_requires_authentication(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/about").status_code == 401

    response = client.put(
        "/api/v1/about",
        json=valid_payload(),
    )
    assert response.status_code == 401


def test_empty_admin_about_returns_null(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/about",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json() is None


def test_update_creates_singleton_about_content(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=valid_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["full_name"] == "Nurlan Rahimli"
    assert body["experience_years"] == 3
    assert body["location"] == "Sacramento, California"
    assert body["is_available"] is True
    assert body["availability_modes"] == ["remote", "onsite"]

    assert [item["name"] for item in body["software_fields"]] == [
        "Software Engineer",
        "AI Engineer",
    ]

    assert [item["display_order"] for item in body["software_fields"]] == [
        0,
        1,
    ]

    assert [item["platform"] for item in body["social_links"]] == [
        "GitHub",
        "LinkedIn",
    ]

    count = db_session.scalar(
        select(func.count(AboutContent.id))
    )
    assert count == 1


def test_second_update_reuses_singleton(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    first = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=valid_payload(),
    )

    assert first.status_code == 200
    first_id = first.json()["id"]

    payload = valid_payload()
    payload["full_name"] = "Nurlan R. Rahimli"
    payload["software_fields"] = [
        {"name": "Full-Stack Engineer"},
    ]
    payload["social_links"] = [
        {
            "platform": "GitHub",
            "url": "https://github.com/NurlanRahimli",
        },
    ]

    second = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert second.status_code == 200
    assert second.json()["id"] == first_id
    assert second.json()["full_name"] == "Nurlan R. Rahimli"

    count = db_session.scalar(
        select(func.count(AboutContent.id))
    )
    assert count == 1


def test_about_sanitizes_rich_text(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["about_html"] = (
        '<p onclick="alert(1)">Hello '
        "<strong>world</strong></p>"
        "<script>alert('xss')</script>"
        '<a href="javascript:alert(1)">bad</a>'
        '<a href="https://example.com" target="_blank">good</a>'
    )

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 200

    html = response.json()["about_html"]

    assert "<strong>world</strong>" in html
    assert "onclick" not in html
    assert "<script" not in html
    assert "javascript:" not in html
    assert 'href="https://example.com"' in html
    assert 'rel="noopener noreferrer"' in html


def test_about_accepts_four_software_fields(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["software_fields"] = [
        {"name": "Software Engineer"},
        {"name": "AI Engineer"},
        {"name": "Backend Engineer"},
        {"name": "Full-Stack Engineer"},
    ]

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 200
    assert len(response.json()["software_fields"]) == 4


def test_about_rejects_more_than_four_software_fields(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["software_fields"] = [
        {"name": "Software Engineer"},
        {"name": "AI Engineer"},
        {"name": "Backend Engineer"},
        {"name": "Full-Stack Engineer"},
        {"name": "Cloud Engineer"},
    ]

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_about_rejects_duplicate_software_fields(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["software_fields"] = [
        {"name": "Software Engineer"},
        {"name": " software engineer "},
    ]

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_available_about_requires_availability_mode(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["availability_modes"] = []

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_unavailable_about_can_have_no_availability_modes(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["is_available"] = False
    payload["availability_modes"] = []

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["is_available"] is False
    assert response.json()["availability_modes"] == []


def test_about_rejects_duplicate_availability_modes(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["availability_modes"] = ["remote", "remote"]

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_about_rejects_invalid_availability_mode(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["availability_modes"] = ["remote", "spaceship"]

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_about_accepts_profile_image_and_resume_pdf(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    image = create_image_asset(db_session)
    document = create_document_asset(db_session)

    payload = valid_payload()
    payload["profile_media_asset_id"] = image.id
    payload["resume_media_asset_id"] = document.id

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile_media_asset_id"] == image.id
    assert body["resume_media_asset_id"] == document.id
    assert body["resume_filename"] == "resume.pdf"


def test_about_rejects_document_as_profile_image(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    document = create_document_asset(db_session)

    payload = valid_payload()
    payload["profile_media_asset_id"] = document.id

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "The About profile media must be an image."
    }


def test_about_rejects_image_as_resume(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    image = create_image_asset(db_session)

    payload = valid_payload()
    payload["resume_media_asset_id"] = image.id

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "The About resume media must be a PDF document."
    }


def test_about_rejects_non_pdf_document_as_resume(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    document = create_document_asset(
        db_session,
        filename="resume.txt",
        mime_type="text/plain",
    )

    payload = valid_payload()
    payload["resume_media_asset_id"] = document.id

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "The About resume media must be a PDF document."
    }


def test_about_rejects_missing_media(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["profile_media_asset_id"] = 999999

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "The selected profile image does not exist."
    }


def test_about_rejects_duplicate_social_platforms(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = valid_payload()
    payload["social_links"] = [
        {
            "platform": "GitHub",
            "url": "https://github.com/NurlanRahimli",
        },
        {
            "platform": " github ",
            "url": "https://github.com/example",
        },
    ]

    response = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_public_about_requires_no_authentication(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    created = client.put(
        "/api/v1/about",
        headers=authenticated_headers,
        json=valid_payload(),
    )
    assert created.status_code == 200

    response = client.get("/api/v1/public/about")

    assert response.status_code == 200

    body = response.json()

    assert body["full_name"] == "Nurlan Rahimli"
    assert body["experience_years"] == 3
    assert body["location"] == "Sacramento, California"

    assert body["software_fields"] == [
        {"name": "Software Engineer"},
        {"name": "AI Engineer"},
    ]

    assert body["social_links"][0] == {
        "platform": "GitHub",
        "url": "https://github.com/NurlanRahimli",
    }

    assert "id" not in body
    assert "profile_media_asset_id" not in body
    assert "resume_media_asset_id" not in body
    assert "created_at" not in body
    assert "updated_at" not in body


def test_empty_public_about_returns_null(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/public/about")

    assert response.status_code == 200
    assert response.json() is None
