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
from app.models import AdminUser, MediaAsset, Testimonial as TestimonialModel


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
        email="testimonial-admin@example.com",
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
        width=400,
        height=400,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def create_document_asset(
    db_session: Session,
) -> MediaAsset:
    asset = MediaAsset(
        filename="resume.pdf",
        original_filename="resume.pdf",
        storage_key="media/documents/test/resume.pdf",
        mime_type="application/pdf",
        file_type="document",
        file_size=100,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def add_testimonial(
    db_session: Session,
    *,
    person_name: str,
    text: str,
    order: int,
    active: bool = True,
    profile_media_asset_id: int | None = None,
) -> TestimonialModel:
    testimonial = TestimonialModel(
        person_name=person_name,
        testimonial_text=text,
        profile_media_asset_id=profile_media_asset_id,
        is_active=active,
        display_order=order,
    )
    db_session.add(testimonial)
    db_session.commit()
    db_session.refresh(testimonial)
    return testimonial


def test_admin_list_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/testimonials")

    assert response.status_code == 401


def test_create_testimonial(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    asset = create_image_asset(db_session)

    response = client.post(
        "/api/v1/testimonials",
        headers=authenticated_headers,
        json={
            "person_name": "Jane Doe",
            "testimonial_text": "Excellent work.",
            "profile_media_asset_id": asset.id,
            "linkedin_url": ("https://www.linkedin.com/in/jane-doe/"),
            "is_active": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["person_name"] == "Jane Doe"
    assert body["testimonial_text"] == "Excellent work."
    assert body["profile_media_asset_id"] == asset.id
    assert body["linkedin_url"] == ("https://www.linkedin.com/in/jane-doe/")
    assert body["is_active"] is True
    assert body["display_order"] == 0

    testimonial = db_session.get(
        TestimonialModel,
        body["id"],
    )
    assert testimonial is not None


def test_create_appends_display_order(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    add_testimonial(
        db_session,
        person_name="First",
        text="First recommendation",
        order=4,
    )

    response = client.post(
        "/api/v1/testimonials",
        headers=authenticated_headers,
        json={
            "person_name": "Second",
            "testimonial_text": "Second recommendation",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["display_order"] == 5


def test_create_rejects_document_profile_asset(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    document = create_document_asset(db_session)

    response = client.post(
        "/api/v1/testimonials",
        headers=authenticated_headers,
        json={
            "person_name": "Jane Doe",
            "testimonial_text": "Excellent work.",
            "profile_media_asset_id": document.id,
            "is_active": True,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": ("Testimonials can only use image media assets.")
    }


def test_update_testimonial(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    testimonial = add_testimonial(
        db_session,
        person_name="Before",
        text="Before text",
        order=0,
    )

    response = client.put(
        f"/api/v1/testimonials/{testimonial.id}",
        headers=authenticated_headers,
        json={
            "person_name": "After",
            "testimonial_text": "After text",
            "linkedin_url": "",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["person_name"] == "After"
    assert body["testimonial_text"] == "After text"
    assert body["linkedin_url"] is None
    assert body["is_active"] is False
    assert body["display_order"] == 0


def test_search_and_active_filter(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    add_testimonial(
        db_session,
        person_name="Alice Johnson",
        text="Amazing portfolio work.",
        order=0,
        active=True,
    )
    add_testimonial(
        db_session,
        person_name="Bob Smith",
        text="Strong backend engineering.",
        order=1,
        active=False,
    )

    response = client.get(
        "/api/v1/testimonials",
        headers=authenticated_headers,
        params={
            "search": "Alice",
            "is_active": "true",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["person_name"] == ("Alice Johnson")


def test_reorder_testimonials(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    first = add_testimonial(
        db_session,
        person_name="First",
        text="First",
        order=0,
    )
    second = add_testimonial(
        db_session,
        person_name="Second",
        text="Second",
        order=1,
    )

    response = client.post(
        "/api/v1/testimonials/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": first.id,
                    "display_order": 1,
                },
                {
                    "id": second.id,
                    "display_order": 0,
                },
            ]
        },
    )

    assert response.status_code == 204

    db_session.expire_all()

    assert (
        db_session.get(
            TestimonialModel,
            first.id,
        ).display_order
        == 1
    )
    assert (
        db_session.get(
            TestimonialModel,
            second.id,
        ).display_order
        == 0
    )


def test_reorder_rejects_missing_testimonial(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/testimonials/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": 999999,
                    "display_order": 0,
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Testimonial not found: 999999"}


def test_delete_testimonial_preserves_media_asset(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    asset = create_image_asset(db_session)

    testimonial = add_testimonial(
        db_session,
        person_name="Jane",
        text="Excellent work.",
        order=0,
        profile_media_asset_id=asset.id,
    )

    response = client.delete(
        f"/api/v1/testimonials/{testimonial.id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert (
        db_session.get(
            TestimonialModel,
            testimonial.id,
        )
        is None
    )
    assert db_session.get(MediaAsset, asset.id) is not None


def test_public_returns_only_first_three_active(
    client: TestClient,
    db_session: Session,
) -> None:
    add_testimonial(
        db_session,
        person_name="Fourth",
        text="Fourth",
        order=3,
    )
    add_testimonial(
        db_session,
        person_name="Hidden",
        text="Hidden",
        order=0,
        active=False,
    )
    add_testimonial(
        db_session,
        person_name="Third",
        text="Third",
        order=2,
    )
    add_testimonial(
        db_session,
        person_name="First",
        text="First",
        order=0,
    )
    add_testimonial(
        db_session,
        person_name="Second",
        text="Second",
        order=1,
    )

    response = client.get("/api/v1/public/testimonials")

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 3
    assert [item["person_name"] for item in body["items"]] == [
        "First",
        "Second",
        "Third",
    ]

    for item in body["items"]:
        assert "id" not in item
        assert "is_active" not in item
        assert "display_order" not in item
        assert "profile_media_asset_id" not in item
        assert "created_at" not in item
        assert "updated_at" not in item


def test_public_endpoint_requires_no_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/public/testimonials")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
    }
