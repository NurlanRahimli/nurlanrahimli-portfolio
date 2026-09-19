from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import AdminUser, Education, MediaAsset
from app.services.media_library import get_media_asset_usages


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
        email="education-admin@example.com",
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


def education_payload(
    *,
    title: str = "Bachelor of Science in Computer Science",
    location: str = "California State University",
    start_date: str = "2021-08-01",
    end_date: str | None = "2025-05-01",
    is_current: bool = False,
    description: str | None = "Studied computer science and software engineering.",
    certification_media_asset_id: int | None = None,
    is_active: bool = True,
) -> dict[str, object]:
    return {
        "title": title,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "is_current": is_current,
        "description": description,
        "certification_media_asset_id": certification_media_asset_id,
        "is_active": is_active,
    }


def create_education_record(
    db_session: Session,
    *,
    title: str = "Bachelor of Science in Computer Science",
    location: str = "California State University",
    start_date: date = date(2021, 8, 1),
    end_date: date | None = date(2025, 5, 1),
    is_current: bool = False,
    description: str | None = "Computer Science",
    is_active: bool = True,
    display_order: int = 0,
    certification_media_asset: MediaAsset | None = None,
) -> Education:
    education = Education(
        title=title,
        location=location,
        start_date=start_date,
        end_date=end_date,
        is_current=is_current,
        description=description,
        certification_media_asset=certification_media_asset,
        is_active=is_active,
        display_order=display_order,
    )
    db_session.add(education)
    db_session.commit()
    db_session.refresh(education)
    return education


def create_pdf_asset(
    db_session: Session,
    *,
    filename: str = "certificate.pdf",
    mime_type: str = "application/pdf",
    file_type: str = "document",
) -> MediaAsset:
    asset = MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/documents/{filename}",
        mime_type=mime_type,
        file_type=file_type,
        file_size=2048,
        width=None,
        height=None,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_admin_educations_require_auth(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/educations")

    assert response.status_code == 401


def test_admin_can_create_education(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["title"] == "Bachelor of Science in Computer Science"
    assert body["location"] == "California State University"
    assert body["start_date"] == "2021-08-01"
    assert body["end_date"] == "2025-05-01"
    assert body["is_current"] is False
    assert body["description"] == ("Studied computer science and software engineering.")
    assert body["certification_media_asset_id"] is None
    assert body["certification_filename"] is None
    assert body["certification_url"] is None
    assert body["is_active"] is True
    assert body["display_order"] == 0


def test_education_text_is_trimmed_and_blank_description_becomes_null(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            title="  Software Engineering Certificate  ",
            location="  Example University  ",
            description="   ",
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["title"] == "Software Engineering Certificate"
    assert body["location"] == "Example University"
    assert body["description"] is None


def test_education_requires_month_start_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            start_date="2021-08-15",
        ),
    )

    assert response.status_code == 422


def test_education_requires_month_end_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            end_date="2025-05-15",
        ),
    )

    assert response.status_code == 422


def test_current_education_requires_null_end_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            end_date="2025-05-01",
            is_current=True,
        ),
    )

    assert response.status_code == 422


def test_current_education_allows_null_end_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            end_date=None,
            is_current=True,
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["start_date"] == "2021-08-01"
    assert body["end_date"] is None
    assert body["is_current"] is True


def test_non_current_education_requires_end_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            end_date=None,
            is_current=False,
        ),
    )

    assert response.status_code == 422


def test_education_end_date_cannot_precede_start_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            start_date="2025-05-01",
            end_date="2024-12-01",
        ),
    )

    assert response.status_code == 422


def test_admin_can_create_education_with_pdf_certificate(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = create_pdf_asset(db_session)

    monkeypatch.setattr(
        "app.api.v1.educations.r2_storage.public_url",
        lambda key: f"https://media.example.com/{key}",
    )

    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            certification_media_asset_id=asset.id,
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["certification_media_asset_id"] == asset.id
    assert body["certification_filename"] == "certificate.pdf"
    assert body["certification_url"] == (
        "https://media.example.com/media/documents/certificate.pdf"
    )


def test_education_rejects_image_as_certificate(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    asset = create_pdf_asset(
        db_session,
        filename="certificate.png",
        mime_type="image/png",
        file_type="image",
    )

    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            certification_media_asset_id=asset.id,
        ),
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Education certifications must use document media assets."
    )


def test_education_rejects_non_pdf_document(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    asset = create_pdf_asset(
        db_session,
        filename="certificate.txt",
        mime_type="text/plain",
        file_type="document",
    )

    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            certification_media_asset_id=asset.id,
        ),
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"] == "Education certifications must be PDF documents."
    )


def test_education_rejects_missing_certificate_asset(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/educations",
        headers=authenticated_headers,
        json=education_payload(
            certification_media_asset_id=999999,
        ),
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "The selected certification document does not exist."
    )


def test_admin_can_list_search_and_filter_educations(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    create_education_record(
        db_session,
        title="Computer Science Degree",
        location="Example University",
        description="Backend systems and algorithms",
        display_order=1,
    )

    create_education_record(
        db_session,
        title="Web Development Certificate",
        location="Example Academy",
        description="React frontend development",
        is_active=False,
        display_order=0,
    )

    response = client.get(
        "/api/v1/educations",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["title"] for item in response.json()["items"]] == [
        "Web Development Certificate",
        "Computer Science Degree",
    ]

    search_response = client.get(
        "/api/v1/educations",
        headers=authenticated_headers,
        params={"search": "React"},
    )

    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1
    assert search_response.json()["items"][0]["title"] == "Web Development Certificate"

    active_response = client.get(
        "/api/v1/educations",
        headers=authenticated_headers,
        params={"is_active": True},
    )

    assert active_response.status_code == 200
    assert active_response.json()["total"] == 1
    assert active_response.json()["items"][0]["title"] == "Computer Science Degree"


def test_admin_can_update_education_and_remove_certificate(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    asset = create_pdf_asset(db_session)

    education = create_education_record(
        db_session,
        certification_media_asset=asset,
    )

    response = client.put(
        f"/api/v1/educations/{education.id}",
        headers=authenticated_headers,
        json=education_payload(
            title="Updated Computer Science Degree",
            location="Updated University",
            start_date="2022-08-01",
            end_date="2026-05-01",
            is_current=False,
            description=None,
            certification_media_asset_id=None,
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == "Updated Computer Science Degree"
    assert body["location"] == "Updated University"
    assert body["start_date"] == "2022-08-01"
    assert body["end_date"] == "2026-05-01"
    assert body["is_current"] is False
    assert body["description"] is None
    assert body["certification_media_asset_id"] is None
    assert body["certification_filename"] is None
    assert body["certification_url"] is None


def test_admin_can_reorder_educations(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    first = create_education_record(
        db_session,
        title="First Education",
        display_order=0,
    )

    second = create_education_record(
        db_session,
        title="Second Education",
        display_order=1,
    )

    response = client.post(
        "/api/v1/educations/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": second.id,
                    "display_order": 0,
                },
                {
                    "id": first.id,
                    "display_order": 1,
                },
            ]
        },
    )

    assert response.status_code == 204

    listed = client.get(
        "/api/v1/educations",
        headers=authenticated_headers,
    )

    assert [item["title"] for item in listed.json()["items"]] == [
        "Second Education",
        "First Education",
    ]


def test_education_reorder_rejects_duplicate_ids(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    education = create_education_record(db_session)

    response = client.post(
        "/api/v1/educations/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": education.id,
                    "display_order": 0,
                },
                {
                    "id": education.id,
                    "display_order": 1,
                },
            ]
        },
    )

    assert response.status_code == 409


def test_admin_can_delete_education(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    education = create_education_record(db_session)
    education_id = education.id

    response = client.delete(
        f"/api/v1/educations/{education_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert db_session.get(Education, education_id) is None


def test_public_endpoint_returns_only_active_educations_in_order(
    client: TestClient,
    db_session: Session,
) -> None:
    create_education_record(
        db_session,
        title="Second Public Education",
        display_order=1,
    )

    create_education_record(
        db_session,
        title="First Public Education",
        display_order=0,
    )

    create_education_record(
        db_session,
        title="Hidden Education",
        is_active=False,
        display_order=2,
    )

    response = client.get("/api/v1/public/educations")

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == [
        "First Public Education",
        "Second Public Education",
    ]

    item = body["items"][0]

    assert "id" not in item
    assert "is_active" not in item
    assert "display_order" not in item
    assert "certification_media_asset_id" not in item
    assert item["start_date"] == "2021-08-01"
    assert item["end_date"] == "2025-05-01"
    assert item["is_current"] is False


def test_public_education_exposes_certificate_url(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = create_pdf_asset(db_session)

    create_education_record(
        db_session,
        title="Certified Education",
        certification_media_asset=asset,
    )

    monkeypatch.setattr(
        "app.api.v1.public_educations.r2_storage.public_url",
        lambda key: f"https://media.example.com/{key}",
    )

    response = client.get("/api/v1/public/educations")

    assert response.status_code == 200

    item = response.json()["items"][0]

    assert item["certification_filename"] == "certificate.pdf"
    assert item["certification_url"] == (
        "https://media.example.com/media/documents/certificate.pdf"
    )


def test_education_certificate_is_reported_as_media_usage(
    db_session: Session,
) -> None:
    asset = create_pdf_asset(db_session)

    create_education_record(
        db_session,
        certification_media_asset=asset,
    )

    usages = get_media_asset_usages(
        db_session,
        asset_id=asset.id,
    )

    assert "an education certification document" in usages
