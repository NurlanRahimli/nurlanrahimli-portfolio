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
from app.models import AdminUser, MediaAsset


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
        email="public-projects@example.com",
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


def create_asset(
    db_session: Session,
    filename: str,
) -> MediaAsset:
    asset = MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/test/{filename}",
        mime_type="image/png",
        file_type="image",
        file_size=1024,
        width=1600,
        height=900,
        alt_text=f"{filename} alt",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def payload(
    cover: MediaAsset,
    shot: MediaAsset,
    *,
    slug: str,
    title: str,
    published: bool = True,
    show_github: bool = True,
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "project_type": "Web Application",
        "short_description": (f"{title} short description"),
        "long_description": (f"{title} long description"),
        "project_date": "2026-06-01",
        "cover_media_asset_id": cover.id,
        "github_url": (f"https://github.com/example/{slug}"),
        "show_github_link": show_github,
        "demo_url": f"https://example.com/{slug}",
        "is_featured": False,
        "is_published": published,
        "tags": [
            {"label": "AI"},
            {"label": "Full-Stack"},
        ],
        "images": [
            {
                "media_asset_id": cover.id,
                "label": "Cover",
            },
            {
                "media_asset_id": shot.id,
                "label": "Dashboard",
            },
        ],
        "features": [
            {"text": "Feature one"},
        ],
        "tech_groups": [
            {
                "label": "Frontend",
                "items": [
                    {"name": "React"},
                    {"name": "TypeScript"},
                ],
            }
        ],
    }


def create_project(
    client: TestClient,
    headers: dict[str, str],
    body: dict,
) -> dict:
    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json=body,
    )
    assert response.status_code == 201
    return response.json()


def test_public_projects_do_not_require_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/public/projects")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
    }


def test_public_list_excludes_drafts(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_asset(db_session, "cover.png")
    shot = create_asset(db_session, "shot.png")

    create_project(
        client,
        authenticated_headers,
        payload(
            cover,
            shot,
            slug="published",
            title="Published",
        ),
    )

    draft = payload(
        cover,
        shot,
        slug="draft",
        title="Draft",
        published=False,
    )

    create_project(
        client,
        authenticated_headers,
        draft,
    )

    response = client.get("/api/v1/public/projects")

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 1
    assert [item["slug"] for item in body["items"]] == ["published"]


def test_public_detail_hides_draft(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_asset(
        db_session,
        "draft-cover.png",
    )
    shot = create_asset(
        db_session,
        "draft-shot.png",
    )

    create_project(
        client,
        authenticated_headers,
        payload(
            cover,
            shot,
            slug="private-draft",
            title="Private Draft",
            published=False,
        ),
    )

    response = client.get("/api/v1/public/projects/private-draft")

    assert response.status_code == 404


def test_public_detail_returns_project_content(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_asset(
        db_session,
        "detail-cover.png",
    )
    shot = create_asset(
        db_session,
        "detail-shot.png",
    )

    create_project(
        client,
        authenticated_headers,
        payload(
            cover,
            shot,
            slug="bookaify",
            title="Bookaify",
        ),
    )

    response = client.get("/api/v1/public/projects/bookaify")

    assert response.status_code == 200
    body = response.json()

    assert body["slug"] == "bookaify"
    assert body["title"] == "Bookaify"
    assert body["github_url"] == ("https://github.com/example/bookaify")
    assert body["demo_url"] == ("https://example.com/bookaify")
    assert [tag["label"] for tag in body["tags"]] == [
        "AI",
        "Full-Stack",
    ]
    assert [image["label"] for image in body["images"]] == [
        "Cover",
        "Dashboard",
    ]
    assert body["features"][0]["text"] == ("Feature one")
    assert body["tech_groups"][0]["label"] == ("Frontend")


def test_public_api_hides_github_when_disabled(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_asset(
        db_session,
        "hidden-github-cover.png",
    )
    shot = create_asset(
        db_session,
        "hidden-github-shot.png",
    )

    create_project(
        client,
        authenticated_headers,
        payload(
            cover,
            shot,
            slug="private-code",
            title="Private Code",
            show_github=False,
        ),
    )

    list_response = client.get("/api/v1/public/projects")
    detail_response = client.get("/api/v1/public/projects/private-code")

    assert list_response.status_code == 200
    assert detail_response.status_code == 200

    assert list_response.json()["items"][0]["github_url"] is None
    assert detail_response.json()["github_url"] is None


def test_public_search_includes_tags_and_technologies(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_asset(
        db_session,
        "search-cover.png",
    )
    shot = create_asset(
        db_session,
        "search-shot.png",
    )

    create_project(
        client,
        authenticated_headers,
        payload(
            cover,
            shot,
            slug="searchable",
            title="Searchable",
        ),
    )

    tag_response = client.get(
        "/api/v1/public/projects",
        params={"search": "full-stack"},
    )
    tech_response = client.get(
        "/api/v1/public/projects",
        params={"search": "typescript"},
    )

    assert tag_response.status_code == 200
    assert tag_response.json()["total"] == 1

    assert tech_response.status_code == 200
    assert tech_response.json()["total"] == 1


def test_public_previous_next_uses_display_order(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    projects = []

    for name in ["First", "Second", "Third"]:
        slug = name.lower()
        cover = create_asset(
            db_session,
            f"{slug}-cover.png",
        )
        shot = create_asset(
            db_session,
            f"{slug}-shot.png",
        )

        projects.append(
            create_project(
                client,
                authenticated_headers,
                payload(
                    cover,
                    shot,
                    slug=slug,
                    title=name,
                ),
            )
        )

    reorder = client.put(
        "/api/v1/projects/reorder/all",
        headers=authenticated_headers,
        json={
            "items": [
                {
                    "id": projects[0]["id"],
                    "display_order": 2,
                },
                {
                    "id": projects[1]["id"],
                    "display_order": 0,
                },
                {
                    "id": projects[2]["id"],
                    "display_order": 1,
                },
            ]
        },
    )
    assert reorder.status_code == 204

    response = client.get("/api/v1/public/projects/third")

    assert response.status_code == 200
    body = response.json()

    assert body["previous_project"] == {
        "slug": "second",
        "title": "Second",
    }
    assert body["next_project"] == {
        "slug": "first",
        "title": "First",
    }


def test_public_navigation_wraps_around(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    for name in ["First", "Second"]:
        slug = name.lower()

        cover = create_asset(
            db_session,
            f"wrap-{slug}-cover.png",
        )
        shot = create_asset(
            db_session,
            f"wrap-{slug}-shot.png",
        )

        create_project(
            client,
            authenticated_headers,
            payload(
                cover,
                shot,
                slug=slug,
                title=name,
            ),
        )

    first = client.get("/api/v1/public/projects/first")
    second = client.get("/api/v1/public/projects/second")

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["previous_project"]["slug"] == ("second")
    assert first.json()["next_project"]["slug"] == ("second")

    assert second.json()["previous_project"]["slug"] == ("first")
    assert second.json()["next_project"]["slug"] == ("first")


def test_single_public_project_has_no_neighbors(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    cover = create_asset(
        db_session,
        "single-cover.png",
    )
    shot = create_asset(
        db_session,
        "single-shot.png",
    )

    create_project(
        client,
        authenticated_headers,
        payload(
            cover,
            shot,
            slug="single",
            title="Single",
        ),
    )

    response = client.get("/api/v1/public/projects/single")

    assert response.status_code == 200
    assert response.json()["previous_project"] is None
    assert response.json()["next_project"] is None
