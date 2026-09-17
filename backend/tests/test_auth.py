from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import AdminUser

TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "correct-test-password"


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestingSessionLocal() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_test_admin(
    db_session: Session,
    *,
    is_active: bool = True,
) -> AdminUser:
    admin = AdminUser(
        email=TEST_EMAIL,
        hashed_password=hash_password(TEST_PASSWORD),
        is_active=is_active,
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin


def test_login_returns_access_token(
    client: TestClient,
    db_session: Session,
) -> None:
    admin = create_test_admin(db_session)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]

    db_session.refresh(admin)

    assert admin.last_login_at is not None


def test_login_rejects_wrong_password(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_admin(db_session)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "definitely-wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_unknown_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_login_rejects_inactive_admin(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_admin(
        db_session,
        is_active=False,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin account is inactive"}


def test_me_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_authenticated_admin(
    client: TestClient,
    db_session: Session,
) -> None:
    admin = create_test_admin(db_session)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == admin.id
    assert body["email"] == TEST_EMAIL
    assert body["is_active"] is True
    assert body["last_login_at"] is not None
    assert "hashed_password" not in body


def test_me_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer definitely-not-a-jwt",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_me_rejects_token_for_missing_admin(
    client: TestClient,
) -> None:
    token = create_access_token("999999")

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


def test_me_rejects_inactive_admin_token(
    client: TestClient,
    db_session: Session,
) -> None:
    admin = create_test_admin(
        db_session,
        is_active=False,
    )

    token = create_access_token(str(admin.id))

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


def test_password_is_stored_as_argon2_hash(
    db_session: Session,
) -> None:
    admin = create_test_admin(db_session)

    stored_admin = db_session.scalar(select(AdminUser).where(AdminUser.id == admin.id))

    assert stored_admin is not None
    assert stored_admin.hashed_password != TEST_PASSWORD
    assert stored_admin.hashed_password.startswith("$argon2")
