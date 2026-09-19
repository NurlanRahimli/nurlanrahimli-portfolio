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
from app.models import AdminUser, Experience, ExperienceHighlight


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
        email="experience-admin@example.com",
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


def experience_payload(
    *,
    job_title: str = "Software Engineer",
    company: str = "Example Company",
    location: str | None = "Sacramento, CA",
    start_date: str = "2024-01-01",
    end_date: str | None = "2025-01-01",
    is_current: bool = False,
    is_active: bool = True,
    highlights: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "job_title": job_title,
        "company": company,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "is_current": is_current,
        "is_active": is_active,
        "highlights": (
            highlights
            if highlights is not None
            else [
                {"text": "Built production web applications."},
                {"text": "Improved backend reliability and performance."},
            ]
        ),
    }


def create_experience_record(
    db_session: Session,
    *,
    job_title: str = "Software Engineer",
    company: str = "Example Company",
    is_active: bool = True,
    display_order: int = 0,
) -> Experience:
    from datetime import date

    experience = Experience(
        job_title=job_title,
        company=company,
        location="Sacramento, CA",
        start_date=date(2024, 1, 1),
        end_date=date(2025, 1, 1),
        is_current=False,
        is_active=is_active,
        display_order=display_order,
    )
    experience.highlights.append(
        ExperienceHighlight(
            text="Built scalable APIs.",
            display_order=0,
        )
    )

    db_session.add(experience)
    db_session.commit()
    db_session.refresh(experience)

    return experience


def test_admin_experiences_require_auth(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/experiences")
    assert response.status_code == 401


def test_admin_can_create_experience(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(),
    )

    assert response.status_code == 201

    body = response.json()
    assert body["job_title"] == "Software Engineer"
    assert body["company"] == "Example Company"
    assert body["start_date"] == "2024-01-01"
    assert body["end_date"] == "2025-01-01"
    assert body["is_current"] is False
    assert body["is_active"] is True
    assert body["display_order"] == 0
    assert [item["text"] for item in body["highlights"]] == [
        "Built production web applications.",
        "Improved backend reliability and performance.",
    ]


def test_experience_text_is_trimmed(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(
            job_title="  Backend Engineer  ",
            company="  Acme Inc.  ",
            location="  Remote  ",
            highlights=[{"text": "  Built reliable APIs.  "}],
        ),
    )

    assert response.status_code == 201

    body = response.json()
    assert body["job_title"] == "Backend Engineer"
    assert body["company"] == "Acme Inc."
    assert body["location"] == "Remote"
    assert body["highlights"][0]["text"] == "Built reliable APIs."


def test_current_experience_requires_no_end_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    valid = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(
            is_current=True,
            end_date=None,
        ),
    )
    assert valid.status_code == 201

    invalid = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(
            is_current=True,
            end_date="2025-01-01",
        ),
    )
    assert invalid.status_code == 422


def test_completed_experience_requires_end_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(
            is_current=False,
            end_date=None,
        ),
    )

    assert response.status_code == 422


def test_experience_rejects_invalid_date_range(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(
            start_date="2025-01-01",
            end_date="2024-01-01",
        ),
    )

    assert response.status_code == 422


def test_experience_requires_month_dates(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/experiences",
        headers=authenticated_headers,
        json=experience_payload(
            start_date="2024-01-15",
        ),
    )

    assert response.status_code == 422


def test_admin_can_list_search_and_filter_experiences(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    create_experience_record(
        db_session,
        job_title="Backend Engineer",
        company="Acme",
        display_order=1,
    )

    hidden = create_experience_record(
        db_session,
        job_title="Frontend Engineer",
        company="Example",
        is_active=False,
        display_order=0,
    )
    hidden.highlights[0].text = "Built React interfaces."
    db_session.commit()

    response = client.get(
        "/api/v1/experiences",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [
        item["job_title"]
        for item in response.json()["items"]
    ] == [
        "Frontend Engineer",
        "Backend Engineer",
    ]

    search_response = client.get(
        "/api/v1/experiences",
        headers=authenticated_headers,
        params={"search": "React"},
    )

    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1
    assert (
        search_response.json()["items"][0]["job_title"]
        == "Frontend Engineer"
    )

    active_response = client.get(
        "/api/v1/experiences",
        headers=authenticated_headers,
        params={"is_active": True},
    )

    assert active_response.status_code == 200
    assert active_response.json()["total"] == 1
    assert (
        active_response.json()["items"][0]["job_title"]
        == "Backend Engineer"
    )


def test_admin_can_update_experience_and_replace_highlights(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    experience = create_experience_record(db_session)

    response = client.put(
        f"/api/v1/experiences/{experience.id}",
        headers=authenticated_headers,
        json=experience_payload(
            job_title="Senior Software Engineer",
            is_current=True,
            end_date=None,
            highlights=[
                {"text": "Led backend architecture."},
                {"text": "Mentored engineers."},
                {"text": "Improved deployment workflows."},
            ],
        ),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["job_title"] == "Senior Software Engineer"
    assert body["is_current"] is True
    assert body["end_date"] is None
    assert [item["text"] for item in body["highlights"]] == [
        "Led backend architecture.",
        "Mentored engineers.",
        "Improved deployment workflows.",
    ]


def test_admin_can_reorder_experiences(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    first = create_experience_record(
        db_session,
        job_title="First",
        display_order=0,
    )
    second = create_experience_record(
        db_session,
        job_title="Second",
        display_order=1,
    )

    response = client.post(
        "/api/v1/experiences/reorder",
        headers=authenticated_headers,
        json={
            "items": [
                {"id": second.id, "display_order": 0},
                {"id": first.id, "display_order": 1},
            ]
        },
    )

    assert response.status_code == 204

    listed = client.get(
        "/api/v1/experiences",
        headers=authenticated_headers,
    )

    assert [
        item["job_title"]
        for item in listed.json()["items"]
    ] == ["Second", "First"]


def test_admin_can_delete_experience_and_highlights(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    experience = create_experience_record(db_session)
    experience_id = experience.id

    response = client.delete(
        f"/api/v1/experiences/{experience_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert db_session.get(Experience, experience_id) is None

    remaining = db_session.query(ExperienceHighlight).filter(
        ExperienceHighlight.experience_id == experience_id
    ).count()

    assert remaining == 0


def test_public_endpoint_returns_only_active_experiences(
    client: TestClient,
    db_session: Session,
) -> None:
    create_experience_record(
        db_session,
        job_title="Public Experience",
        display_order=1,
    )

    create_experience_record(
        db_session,
        job_title="Hidden Experience",
        is_active=False,
        display_order=0,
    )

    response = client.get("/api/v1/public/experiences")

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["job_title"] == "Public Experience"
    assert "id" not in body["items"][0]
    assert "is_active" not in body["items"][0]
    assert "display_order" not in body["items"][0]
    assert "id" not in body["items"][0]["highlights"][0]
