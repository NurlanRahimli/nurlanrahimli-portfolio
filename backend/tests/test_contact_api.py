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
from app.models.admin_user import AdminUser


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with SessionLocal() as session:
        yield session

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
        email="contact-admin@example.com",
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


def test_admin_contact_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/contact")

    assert response.status_code == 401


def test_admin_contact_is_initially_empty(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/contact",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json() is None


def test_admin_can_create_contact_content(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": 12,
            "email": "hello@example.com",
            "phone_number": "+1 (916) 555-1234",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["projects_built"] == 12
    assert data["email"] == "hello@example.com"
    assert data["phone_number"] == "+1 (916) 555-1234"
    assert data["created_at"]
    assert data["updated_at"]


def test_admin_can_update_existing_contact_content(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    first = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": 10,
            "email": "old@example.com",
            "phone_number": "+1 111 111 1111",
        },
    )

    assert first.status_code == 200

    second = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": 25,
            "email": "new@example.com",
            "phone_number": "+1 222 222 2222",
        },
    )

    assert second.status_code == 200

    data = second.json()

    assert data["id"] == 1
    assert data["projects_built"] == 25
    assert data["email"] == "new@example.com"
    assert data["phone_number"] == "+1 222 222 2222"

    get_response = client.get(
        "/api/v1/contact",
        headers=authenticated_headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == 1
    assert get_response.json()["projects_built"] == 25


def test_contact_rejects_negative_projects_built(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": -1,
            "email": "hello@example.com",
            "phone_number": "+1 916 555 1234",
        },
    )

    assert response.status_code == 422


def test_contact_rejects_invalid_email(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": 10,
            "email": "not-an-email",
            "phone_number": "+1 916 555 1234",
        },
    )

    assert response.status_code == 422


def test_contact_rejects_blank_phone_number(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": 10,
            "email": "hello@example.com",
            "phone_number": "   ",
        },
    )

    assert response.status_code == 422


def test_public_contact_is_initially_empty(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/public/contact")

    assert response.status_code == 200
    assert response.json() is None


def test_public_contact_exposes_only_public_fields(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    update_response = client.put(
        "/api/v1/contact",
        headers=authenticated_headers,
        json={
            "projects_built": 18,
            "email": "portfolio@example.com",
            "phone_number": "+1 916 555 9876",
        },
    )

    assert update_response.status_code == 200

    response = client.get("/api/v1/public/contact")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "projects_built": 18,
        "email": "portfolio@example.com",
        "phone_number": "+1 916 555 9876",
    }

    assert "id" not in data
    assert "created_at" not in data
    assert "updated_at" not in data
