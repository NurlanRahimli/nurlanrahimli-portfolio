from collections.abc import Generator
from datetime import date
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import (
    AdminUser,
    MediaAsset,
    Project,
    ProjectFeature,
    ProjectImage,
    ProjectTag,
    ProjectTechGroup,
    ProjectTechItem,
    ProjectVideo,
)
from app.services.mux_video import MuxAPIError, MuxConfigurationError


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
        email="projects-admin@example.com",
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


def create_media_asset(
    db_session: Session,
    *,
    filename: str,
    file_type: str = "image",
    mime_type: str = "image/png",
) -> MediaAsset:
    asset = MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/test/{filename}",
        mime_type=mime_type,
        file_type=file_type,
        file_size=1024,
        width=1600 if file_type == "image" else None,
        height=900 if file_type == "image" else None,
        alt_text=f"{filename} alt text",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def draft_payload(
    *,
    slug: str = "bookaify",
    title: str = "Bookaify",
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "project_type": "Web Application",
        "short_description": "AI-powered bookkeeping platform.",
        "long_description": (
            "Bookaify helps businesses understand their finances.\n\n"
            "It combines automation, analytics and AI."
        ),
        "project_date": "2026-06-01",
        "cover_media_asset_id": None,
        "github_url": None,
        "show_github_link": True,
        "demo_url": None,
        "is_featured": False,
        "is_published": False,
        "tags": [],
        "images": [],
        "features": [],
        "tech_groups": [],
    }


def complete_payload(
    cover: MediaAsset,
    screenshot: MediaAsset,
    *,
    slug: str = "bookaify",
    title: str = "Bookaify",
) -> dict:
    payload = draft_payload(
        slug=slug,
        title=title,
    )
    payload.update(
        {
            "cover_media_asset_id": cover.id,
            "github_url": "https://github.com/example/bookaify",
            "show_github_link": True,
            "demo_url": "https://example.com/bookaify",
            "is_featured": True,
            "is_published": True,
            "tags": [
                {"label": "AI"},
                {"label": "Full-Stack"},
            ],
            "images": [
                {
                    "media_asset_id": screenshot.id,
                    "label": "Dashboard",
                },
                {
                    "media_asset_id": cover.id,
                    "label": "Overview",
                },
            ],
            "features": [
                {"text": "Conversational analytics"},
                {"text": "Receipt processing"},
            ],
            "tech_groups": [
                {
                    "label": "Frontend",
                    "items": [
                        {"name": "React"},
                        {"name": "TypeScript"},
                    ],
                },
                {
                    "label": "Backend",
                    "items": [
                        {"name": "FastAPI"},
                        {"name": "PostgreSQL"},
                    ],
                },
            ],
        }
    )
    return payload


def test_projects_require_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/projects")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }


def test_project_create_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/projects",
        json=draft_payload(),
    )

    assert response.status_code == 401


def test_create_title_only_draft_is_allowed(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={"title": "Bookaify"},
    )

    assert response.status_code == 201
    body = response.json()

    assert body["slug"] == "bookaify"
    assert body["title"] == "Bookaify"
    assert body["project_type"] is None
    assert body["short_description"] is None
    assert body["long_description"] is None
    assert body["project_date"] is None
    assert body["cover_media_asset_id"] is None
    assert body["github_url"] is None
    assert body["show_github_link"] is False
    assert body["demo_url"] is None
    assert body["is_published"] is False
    assert body["is_featured"] is False
    assert body["display_order"] == 0
    assert body["tags"] == []
    assert body["images"] == []
    assert body["features"] == []
    assert body["tech_groups"] == []
    assert body["video"] is None

    project = db_session.scalar(select(Project).where(Project.slug == "bookaify"))
    assert project is not None


def test_automatic_slug_collision_uses_numeric_suffix(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    first = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={"title": "Bookaify"},
    )
    second = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={"title": "Bookaify"},
    )
    third = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={"title": "Bookaify"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 201

    assert first.json()["slug"] == "bookaify"
    assert second.json()["slug"] == "bookaify-2"
    assert third.json()["slug"] == "bookaify-3"


def test_automatic_slug_normalizes_title(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={
            "title": "  My Résumé & Portfolio!  ",
        },
    )

    assert response.status_code == 201
    assert response.json()["slug"] == ("my-resume-portfolio")


def test_custom_slug_is_preserved(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={
            "title": "Bookaify",
            "slug": "custom-bookkeeping-app",
        },
    )

    assert response.status_code == 201
    assert response.json()["slug"] == ("custom-bookkeeping-app")


def test_create_complete_published_project(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="bookaify-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="bookaify-dashboard.png",
    )

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=complete_payload(cover, screenshot),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["slug"] == "bookaify"
    assert body["is_published"] is True
    assert body["is_featured"] is True
    assert body["cover_media_asset_id"] == cover.id

    assert [item["label"] for item in body["tags"]] == [
        "AI",
        "Full-Stack",
    ]

    assert [item["label"] for item in body["images"]] == [
        "Dashboard",
        "Overview",
    ]

    assert [item["text"] for item in body["features"]] == [
        "Conversational analytics",
        "Receipt processing",
    ]

    assert [group["label"] for group in body["tech_groups"]] == [
        "Frontend",
        "Backend",
    ]

    assert [item["name"] for item in body["tech_groups"][0]["items"]] == [
        "React",
        "TypeScript",
    ]

    assert body["github_url"] == ("https://github.com/example/bookaify")
    assert body["demo_url"] == ("https://example.com/bookaify")


def test_create_assigns_incrementing_display_order(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    first = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(
            slug="first",
            title="First",
        ),
    )
    second = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(
            slug="second",
            title="Second",
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["display_order"] == 0
    assert second.json()["display_order"] == 1


def test_duplicate_custom_slug_is_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    first = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={
            "title": "Bookaify",
            "slug": "custom-project",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={
            "title": "Another Project",
            "slug": "custom-project",
        },
    )

    assert second.status_code == 409
    assert second.json() == {"detail": ("A project with this slug already exists.")}


def test_invalid_slug_is_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload()
    payload["slug"] = "Bookaify Project!"

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("github_url", "not-a-url"),
        ("demo_url", "definitely-not-a-url"),
    ],
)
def test_invalid_project_urls_are_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
    field: str,
    value: str,
) -> None:
    payload = draft_payload()
    payload[field] = value

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_missing_media_asset_is_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload()
    payload["cover_media_asset_id"] = 999999
    payload["images"] = [
        {
            "media_asset_id": 999999,
            "label": "Missing image",
        }
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Media asset not found:")


def test_document_cannot_be_used_as_project_image(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    document = create_media_asset(
        db_session,
        filename="resume.pdf",
        file_type="document",
        mime_type="application/pdf",
    )

    payload = draft_payload()
    payload["images"] = [
        {
            "media_asset_id": document.id,
            "label": "Not an image",
        }
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"].startswith(
        "Projects can only use image media assets:"
    )


def test_duplicate_tags_are_case_insensitively_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload()
    payload["tags"] = [
        {"label": "AI"},
        {"label": "ai"},
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Project tags must be unique."}


def test_duplicate_images_are_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    asset = create_media_asset(
        db_session,
        filename="duplicate.png",
    )

    payload = draft_payload()
    payload["images"] = [
        {"media_asset_id": asset.id},
        {"media_asset_id": asset.id},
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Project images must be unique."}


def test_duplicate_tech_groups_are_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload()
    payload["tech_groups"] = [
        {
            "label": "Backend",
            "items": [{"name": "FastAPI"}],
        },
        {
            "label": "backend",
            "items": [{"name": "PostgreSQL"}],
        },
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Tech stack group labels must be unique."}


def test_duplicate_technologies_are_rejected(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload()
    payload["tech_groups"] = [
        {
            "label": "Frontend",
            "items": [
                {"name": "React"},
                {"name": "react"},
            ],
        }
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ('Technologies in "Frontend" must be unique.')}


@pytest.mark.parametrize(
    ("field", "expected_detail"),
    [
        (
            "project_type",
            "A published project requires a project type.",
        ),
        (
            "short_description",
            ("A published project requires a short description."),
        ),
        (
            "long_description",
            ("A published project requires a long description."),
        ),
        (
            "project_date",
            "A published project requires a project date.",
        ),
        (
            "cover_media_asset_id",
            "A published project requires a cover image.",
        ),
        (
            "images",
            ("A published project requires at least one gallery image."),
        ),
        (
            "features",
            ("A published project requires at least one key feature."),
        ),
        (
            "tech_groups",
            ("A published project requires at least one tech stack group."),
        ),
    ],
)
def test_published_project_requirements(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    field: str,
    expected_detail: str,
) -> None:
    cover = create_media_asset(
        db_session,
        filename=f"{field}-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename=f"{field}-screenshot.png",
    )

    payload = complete_payload(
        cover,
        screenshot,
        slug=f"missing-{field.replace('_', '-')}",
    )

    if field in {
        "project_type",
        "short_description",
        "long_description",
        "project_date",
        "cover_media_asset_id",
    }:
        payload[field] = None
    else:
        payload[field] = []

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": expected_detail}


def test_published_project_does_not_require_tags(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="no-tags-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="no-tags-shot.png",
    )

    payload = complete_payload(
        cover,
        screenshot,
        slug="published-without-tags",
    )
    payload["tags"] = []

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["tags"] == []


def test_published_project_requires_technology_item(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="empty-tech-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="empty-tech-shot.png",
    )

    payload = complete_payload(
        cover,
        screenshot,
        slug="empty-technologies",
    )
    payload["tech_groups"] = [
        {
            "label": "Frontend",
            "items": [],
        }
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": ('Tech stack group "Frontend" requires at least one technology.')
    }


def test_cover_must_be_in_project_gallery(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="outside-gallery-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="inside-gallery-shot.png",
    )

    payload = complete_payload(
        cover,
        screenshot,
        slug="invalid-cover-gallery",
    )
    payload["images"] = [
        {
            "media_asset_id": screenshot.id,
            "label": "Only gallery image",
        }
    ]

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("The cover image must also be included in the project gallery.")
    }


def test_github_url_required_when_link_enabled(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="github-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="github-shot.png",
    )

    payload = complete_payload(
        cover,
        screenshot,
        slug="github-required",
    )
    payload["github_url"] = None
    payload["show_github_link"] = True

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("A GitHub URL is required when the GitHub link is enabled.")
    }


def test_github_url_not_required_when_link_hidden(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="hidden-github-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="hidden-github-shot.png",
    )

    payload = complete_payload(
        cover,
        screenshot,
        slug="hidden-github",
    )
    payload["github_url"] = None
    payload["show_github_link"] = False

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["github_url"] is None
    assert response.json()["show_github_link"] is False


def test_project_date_must_use_first_day_of_month(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload(
        slug="invalid-project-date",
    )
    payload["project_date"] = "2026-06-18"

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("Project date must use the first day of the month.")
    }


def test_get_project_returns_nested_content(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="get-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="get-shot.png",
    )

    created = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=complete_payload(cover, screenshot),
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == project_id
    assert len(body["tags"]) == 2
    assert len(body["images"]) == 2
    assert len(body["features"]) == 2
    assert len(body["tech_groups"]) == 2


def test_get_missing_project_returns_404(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/projects/999999",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found."}


def test_update_project_replaces_nested_content(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    first_cover = create_media_asset(
        db_session,
        filename="first-cover.png",
    )
    first_shot = create_media_asset(
        db_session,
        filename="first-shot.png",
    )

    created = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=complete_payload(
            first_cover,
            first_shot,
        ),
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    second_cover = create_media_asset(
        db_session,
        filename="second-cover.png",
    )
    second_shot = create_media_asset(
        db_session,
        filename="second-shot.png",
    )

    payload = complete_payload(
        second_cover,
        second_shot,
        slug="bookaify-v2",
        title="Bookaify V2",
    )
    payload["tags"] = [{"label": "FinTech"}]
    payload["features"] = [{"text": "Updated feature"}]
    payload["tech_groups"] = [
        {
            "label": "Infrastructure",
            "items": [
                {"name": "Cloudflare"},
            ],
        }
    ]

    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["slug"] == "bookaify-v2"
    assert body["title"] == "Bookaify V2"
    assert [tag["label"] for tag in body["tags"]] == ["FinTech"]
    assert [feature["text"] for feature in body["features"]] == ["Updated feature"]
    assert [group["label"] for group in body["tech_groups"]] == ["Infrastructure"]

    assert db_session.scalar(select(ProjectTag).where(ProjectTag.label == "AI")) is None

    assert (
        db_session.scalar(
            select(ProjectFeature).where(
                ProjectFeature.text == "Conversational analytics"
            )
        )
        is None
    )

    assert (
        db_session.scalar(
            select(ProjectTechGroup).where(ProjectTechGroup.label == "Frontend")
        )
        is None
    )

    assert (
        db_session.scalar(
            select(ProjectTechItem).where(ProjectTechItem.name == "React")
        )
        is None
    )


def test_update_title_preserves_slug_when_omitted(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(
            slug="stable-project-slug",
            title="Original Project Title",
        ),
    )

    assert created.status_code == 201
    project_id = created.json()["id"]

    payload = draft_payload(
        slug="stable-project-slug",
        title="Updated Project Title",
    )
    payload.pop("slug")

    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["title"] == ("Updated Project Title")
    assert response.json()["slug"] == ("stable-project-slug")


def test_list_searches_and_filters_projects(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="filter-cover.png",
    )
    shot = create_media_asset(
        db_session,
        filename="filter-shot.png",
    )

    published = complete_payload(
        cover,
        shot,
        slug="ai-finance",
        title="AI Finance",
    )

    first = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=published,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(
            slug="portfolio-site",
            title="Portfolio Site",
        ),
    )
    assert second.status_code == 201

    response = client.get(
        "/api/v1/projects",
        headers=authenticated_headers,
        params={
            "search": "finance",
            "is_published": True,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 1
    assert [item["slug"] for item in body["items"]] == ["ai-finance"]

    response = client.get(
        "/api/v1/projects",
        headers=authenticated_headers,
        params={"is_published": False},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["slug"] == ("portfolio-site")


def test_list_item_contains_flat_technology_names(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="technology-cover.png",
    )
    shot = create_media_asset(
        db_session,
        filename="technology-shot.png",
    )

    created = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=complete_payload(cover, shot),
    )
    assert created.status_code == 201

    response = client.get(
        "/api/v1/projects",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["technologies"] == [
        "React",
        "TypeScript",
        "FastAPI",
        "PostgreSQL",
    ]


def test_reorder_projects(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    first = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(
            slug="first",
            title="First",
        ),
    )
    second = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(
            slug="second",
            title="Second",
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_id = first.json()["id"]
    second_id = second.json()["id"]

    response = client.put(
        "/api/v1/projects/reorder/all",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": first_id,
                    "display_order": 1,
                },
                {
                    "id": second_id,
                    "display_order": 0,
                },
            ]
        },
    )

    assert response.status_code == 204

    listed = client.get(
        "/api/v1/projects",
        headers=authenticated_headers,
    )

    assert listed.status_code == 200
    assert [item["slug"] for item in listed.json()["items"]] == [
        "second",
        "first",
    ]


def test_reorder_rejects_duplicate_project_ids(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=draft_payload(),
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    response = client.put(
        "/api/v1/projects/reorder/all",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": project_id,
                    "display_order": 0,
                },
                {
                    "id": project_id,
                    "display_order": 1,
                },
            ]
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("Each project can only appear once in a reorder request.")
    }


def test_delete_project_preserves_media_assets(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="delete-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="delete-shot.png",
    )

    created = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=complete_payload(cover, screenshot),
    )

    assert created.status_code == 201

    project_id = created.json()["id"]
    cover_id = cover.id
    screenshot_id = screenshot.id

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204

    assert db_session.get(Project, project_id) is None
    assert db_session.get(MediaAsset, cover_id) is not None
    assert db_session.get(MediaAsset, screenshot_id) is not None
    assert db_session.scalar(select(ProjectImage)) is None


def test_delete_missing_project_returns_404(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.delete(
        "/api/v1/projects/999999",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found."}


def test_project_date_is_returned_as_iso_date(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    payload = draft_payload()
    payload["project_date"] = date(
        2026,
        6,
        1,
    ).isoformat()

    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["project_date"] == "2026-06-01"


def test_delete_project_deletes_mux_asset_before_project(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="mux-delete-project",
        title="Mux Delete Project",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="delete-project-upload",
        mux_asset_id="delete-project-asset",
        mux_playback_id="delete-project-playback",
        status="ready",
        original_filename="demo.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id

    cleanup_calls: list[dict[str, str | None]] = []

    def fake_delete_asset(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        assert db_session.get(Project, project_id) is not None
        assert db_session.get(ProjectVideo, video_id) is not None
        cleanup_calls.append(
            {
                "upload_id": upload_id,
                "asset_id": asset_id,
            }
        )

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_delete_asset,
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert cleanup_calls == [
        {
            "upload_id": "delete-project-upload",
            "asset_id": "delete-project-asset",
        }
    ]
    assert db_session.get(Project, project_id) is None
    assert db_session.get(ProjectVideo, video_id) is None


def test_delete_project_preserves_project_when_mux_delete_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="mux-failure-project",
        title="Mux Failure Project",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="failure-upload",
        mux_asset_id="failure-asset",
        mux_playback_id="failure-playback",
        status="ready",
        original_filename="demo.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxAPIError("Mux unavailable.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Mux unavailable."}
    assert db_session.get(Project, project_id) is not None
    assert db_session.get(ProjectVideo, video_id) is not None


def test_delete_project_preserves_project_when_mux_unconfigured(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="mux-unconfigured-project",
        title="Mux Unconfigured Project",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="unconfigured-upload",
        mux_asset_id="unconfigured-asset",
        mux_playback_id="unconfigured-playback",
        status="ready",
        original_filename="demo.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxConfigurationError("Mux is not configured.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Mux is not configured."}
    assert db_session.get(Project, project_id) is not None
    assert db_session.get(ProjectVideo, video_id) is not None


def test_delete_project_reconciles_upload_only_video_before_project_delete(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="pending-video-project",
        title="Pending Video Project",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="pending-project-upload",
        mux_asset_id=None,
        status="uploading",
        original_filename="pending.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id

    cleanup_calls: list[dict[str, str | None]] = []

    def fake_cleanup_project_video(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        assert db_session.get(Project, project_id) is not None
        assert db_session.get(ProjectVideo, video_id) is not None
        cleanup_calls.append(
            {
                "upload_id": upload_id,
                "asset_id": asset_id,
            }
        )

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup_project_video,
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert cleanup_calls == [
        {
            "upload_id": "pending-project-upload",
            "asset_id": None,
        }
    ]
    assert db_session.get(Project, project_id) is None
    assert db_session.get(ProjectVideo, video_id) is None


def test_delete_project_preserves_upload_only_video_when_mux_cleanup_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="pending-video-failure-project",
        title="Pending Video Failure Project",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="pending-failure-upload",
        mux_asset_id=None,
        status="uploading",
        original_filename="pending.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxAPIError("Could not safely clean up Mux upload.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not safely clean up Mux upload."}

    assert db_session.get(Project, project_id) is not None
    assert db_session.get(ProjectVideo, video_id) is not None


def test_update_project_can_retain_same_nested_values(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_media_asset(
        db_session,
        filename="retained-cover.png",
    )
    screenshot = create_media_asset(
        db_session,
        filename="retained-screenshot.png",
    )

    create_response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json=complete_payload(cover, screenshot),
    )

    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    payload = complete_payload(cover, screenshot)
    payload["title"] = "Bookaify Updated"
    payload["images"][0]["label"] = "Updated dashboard"
    payload["features"][0]["text"] = "Updated conversational analytics"

    update_response = client.put(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
        json=payload,
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["title"] == "Bookaify Updated"
    assert body["cover_media_asset_id"] == cover.id

    assert [image["media_asset_id"] for image in body["images"]] == [
        screenshot.id,
        cover.id,
    ]
    assert [image["label"] for image in body["images"]] == [
        "Updated dashboard",
        "Overview",
    ]

    assert [tag["label"] for tag in body["tags"]] == [
        "AI",
        "Full-Stack",
    ]

    assert [feature["text"] for feature in body["features"]] == [
        "Updated conversational analytics",
        "Receipt processing",
    ]

    assert [group["label"] for group in body["tech_groups"]] == [
        "Frontend",
        "Backend",
    ]
    assert [item["name"] for item in body["tech_groups"][0]["items"]] == [
        "React",
        "TypeScript",
    ]


def test_create_project_allows_empty_title_for_draft(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/projects",
        headers=authenticated_headers,
        json={"title": ""},
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["title"] == ""
    assert payload["slug"] == "project"
    assert payload["is_published"] is False


def test_delete_project_cleans_pending_then_active_before_database_delete(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="delete-project-with-replacement",
        title="Delete Project With Replacement",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="active-upload",
        mux_asset_id="active-asset",
        mux_playback_id="active-playback",
        status="ready",
        original_filename="active.mp4",
        pending_mux_upload_id="replacement-upload",
        pending_mux_asset_id="replacement-asset",
        pending_status="processing",
        pending_original_filename="replacement.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id
    cleanup_calls: list[tuple[str | None, str | None]] = []

    def fake_cleanup(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        assert db_session.get(Project, project_id) is not None
        assert db_session.get(ProjectVideo, video_id) is not None
        cleanup_calls.append((upload_id, asset_id))

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
        ("active-upload", "active-asset"),
    ]
    assert db_session.get(Project, project_id) is None
    assert db_session.get(ProjectVideo, video_id) is None


def test_delete_project_preserves_project_when_pending_cleanup_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        slug="delete-project-pending-failure",
        title="Delete Project Pending Failure",
        project_type="Web Application",
        short_description="Short description",
        long_description="Long description",
        project_date=date(2026, 6, 1),
        is_published=False,
        display_order=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="active-upload",
        mux_asset_id="active-asset",
        mux_playback_id="active-playback",
        status="ready",
        original_filename="active.mp4",
        pending_mux_upload_id="replacement-upload",
        pending_mux_asset_id="replacement-asset",
        pending_status="processing",
        pending_original_filename="replacement.mp4",
    )
    db_session.add(video)
    db_session.commit()

    project_id = project.id
    video_id = video.id
    cleanup_calls: list[tuple[str | None, str | None]] = []

    def fake_cleanup(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        cleanup_calls.append((upload_id, asset_id))
        raise MuxAPIError("Pending replacement cleanup failed.")

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Pending replacement cleanup failed."}
    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
    ]

    preserved_project = db_session.get(Project, project_id)
    preserved_video = db_session.get(ProjectVideo, video_id)

    assert preserved_project is not None
    assert preserved_video is not None
    assert preserved_video.mux_asset_id == "active-asset"
    assert preserved_video.status == "ready"
    assert preserved_video.pending_mux_upload_id == "replacement-upload"
    assert preserved_video.pending_mux_asset_id == "replacement-asset"
