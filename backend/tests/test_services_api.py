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
from app.models import AdminUser, Service


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
        email="services-admin@example.com",
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


def service_payload(
    *,
    icon: str = "Lightbulb",
    title: str = "Full-Stack Development",
    description: str = (
        "Building complete web applications from polished frontend "
        "interfaces to reliable APIs and backend systems."
    ),
    is_active: bool = True,
) -> dict[str, object]:
    return {
        "icon": icon,
        "title": title,
        "description": description,
        "is_active": is_active,
    }


def create_service_record(
    db_session: Session,
    *,
    icon: str = "Lightbulb",
    title: str = "Full-Stack Development",
    description: str = "Building complete web applications.",
    is_active: bool = True,
    display_order: int = 0,
) -> Service:
    service = Service(
        icon=icon,
        title=title,
        description=description,
        is_active=is_active,
        display_order=display_order,
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


def test_admin_services_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/services")

    assert response.status_code == 401


def test_admin_can_create_service(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(),
    )

    assert response.status_code == 201

    body = response.json()
    assert body["icon"] == "Lightbulb"
    assert body["title"] == "Full-Stack Development"
    assert body["is_active"] is True
    assert body["display_order"] == 0
    assert body["id"] > 0
    assert body["created_at"]
    assert body["updated_at"]


def test_service_text_is_trimmed(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(
            title="  API Development  ",
            description="  Reliable backend systems.  ",
        ),
    )

    assert response.status_code == 201
    assert response.json()["title"] == "API Development"
    assert response.json()["description"] == "Reliable backend systems."


def test_service_requires_title_and_description(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(
            title="   ",
            description="   ",
        ),
    )

    assert response.status_code == 422


def test_service_accepts_extended_icon_catalog(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(
            icon="Rocket",
            title="Product Engineering",
        ),
    )

    assert response.status_code == 201
    assert response.json()["icon"] == "Rocket"


def test_service_rejects_unknown_icon(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(icon="DefinitelyNotAnIcon"),
    )

    assert response.status_code == 422


def test_new_services_append_to_display_order(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    first = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(title="First"),
    )
    second = client.post(
        "/api/v1/services",
        headers=authenticated_headers,
        json=service_payload(
            icon="Code2",
            title="Second",
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["display_order"] == 0
    assert second.json()["display_order"] == 1


def test_admin_can_list_search_and_filter_services(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    create_service_record(
        db_session,
        title="Full-Stack Development",
        description="Frontend and backend systems.",
        display_order=1,
    )
    create_service_record(
        db_session,
        icon="BrainCircuit",
        title="AI Engineering",
        description="Applied AI systems.",
        is_active=False,
        display_order=0,
    )

    response = client.get(
        "/api/v1/services",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == [
        "AI Engineering",
        "Full-Stack Development",
    ]

    search_response = client.get(
        "/api/v1/services",
        headers=authenticated_headers,
        params={"search": "frontend"},
    )

    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1
    assert search_response.json()["items"][0]["title"] == "Full-Stack Development"

    active_response = client.get(
        "/api/v1/services",
        headers=authenticated_headers,
        params={"is_active": True},
    )

    assert active_response.status_code == 200
    assert active_response.json()["total"] == 1
    assert active_response.json()["items"][0]["title"] == "Full-Stack Development"


def test_admin_can_get_service_detail(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    service = create_service_record(db_session)

    response = client.get(
        f"/api/v1/services/{service.id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == service.id


def test_missing_service_returns_404(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/services/999999",
        headers=authenticated_headers,
    )

    assert response.status_code == 404


def test_admin_can_update_service(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    service = create_service_record(db_session)

    response = client.put(
        f"/api/v1/services/{service.id}",
        headers=authenticated_headers,
        json=service_payload(
            icon="BrainCircuit",
            title="AI Engineering",
            description="Building production AI systems.",
            is_active=False,
        ),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["icon"] == "BrainCircuit"
    assert body["title"] == "AI Engineering"
    assert body["description"] == "Building production AI systems."
    assert body["is_active"] is False
    assert body["display_order"] == 0


def test_admin_can_delete_service(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    service = create_service_record(db_session)

    response = client.delete(
        f"/api/v1/services/{service.id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert db_session.get(Service, service.id) is None


def test_admin_can_reorder_services(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    first = create_service_record(
        db_session,
        title="First",
        display_order=0,
    )
    second = create_service_record(
        db_session,
        icon="Code2",
        title="Second",
        display_order=1,
    )

    response = client.post(
        "/api/v1/services/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": first.id, "display_order": 1},
                {"id": second.id, "display_order": 0},
            ]
        },
    )

    assert response.status_code == 204

    db_session.refresh(first)
    db_session.refresh(second)

    assert first.display_order == 1
    assert second.display_order == 0


def test_reorder_rejects_duplicate_service_ids(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    service = create_service_record(db_session)

    response = client.post(
        "/api/v1/services/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": service.id, "display_order": 0},
                {"id": service.id, "display_order": 1},
            ]
        },
    )

    assert response.status_code == 409


def test_reorder_rejects_missing_service(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/services/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": 999999, "display_order": 0},
            ]
        },
    )

    assert response.status_code == 409


def test_public_services_do_not_require_auth(
    client: TestClient,
    db_session: Session,
) -> None:
    create_service_record(
        db_session,
        icon="Code2",
        title="Full-Stack Development",
        description="Complete web applications.",
        is_active=True,
    )

    response = client.get("/api/v1/public/services")

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 1
    assert body["items"] == [
        {
            "icon": "Code2",
            "title": "Full-Stack Development",
            "description": "Complete web applications.",
        }
    ]


def test_public_services_only_return_active_items_in_order(
    client: TestClient,
    db_session: Session,
) -> None:
    create_service_record(
        db_session,
        icon="Cloud",
        title="Cloud Engineering",
        description="Cloud infrastructure.",
        is_active=True,
        display_order=2,
    )
    create_service_record(
        db_session,
        icon="BrainCircuit",
        title="Hidden AI",
        description="Hidden service.",
        is_active=False,
        display_order=0,
    )
    create_service_record(
        db_session,
        icon="Code2",
        title="Full-Stack Development",
        description="Complete applications.",
        is_active=True,
        display_order=1,
    )

    response = client.get("/api/v1/public/services")

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == [
        "Full-Stack Development",
        "Cloud Engineering",
    ]


def test_public_service_payload_hides_admin_fields(
    client: TestClient,
    db_session: Session,
) -> None:
    create_service_record(db_session)

    response = client.get("/api/v1/public/services")

    assert response.status_code == 200

    item = response.json()["items"][0]

    assert set(item) == {
        "icon",
        "title",
        "description",
    }
