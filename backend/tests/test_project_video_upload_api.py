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
from app.models import AdminUser, Project, ProjectVideo
from app.services.mux_video import (
    MuxAPIError,
    MuxConfigurationError,
    MuxDirectUpload,
)


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
        email="video-admin@example.com",
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


def create_project(
    db_session: Session,
    *,
    slug: str = "bookaify",
) -> Project:
    project = Project(
        slug=slug,
        title="Bookaify",
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
    return project


def mock_direct_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> Mock:
    mocked = Mock(
        return_value=MuxDirectUpload(
            upload_id="mux-upload-123",
            upload_url=("https://storage.video.mux.com/direct-upload-url"),
            status="waiting",
        )
    )

    monkeypatch.setattr(
        "app.api.v1.projects.create_direct_upload",
        mocked,
    )

    return mocked


def test_video_upload_requires_authentication(
    client: TestClient,
    db_session: Session,
) -> None:
    project = create_project(db_session)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        json={
            "original_filename": "bookaify-demo.mp4",
        },
    )

    assert response.status_code == 401


def test_video_upload_rejects_missing_project(
    client: TestClient,
    authenticated_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        "/api/v1/projects/999999/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "demo.mp4",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found."}
    mocked.assert_not_called()


def test_video_upload_creates_project_video(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "bookaify-demo.mp4",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body == {
        "project_id": project.id,
        "upload_id": "mux-upload-123",
        "upload_url": ("https://storage.video.mux.com/direct-upload-url"),
        "status": "uploading",
    }

    mocked.assert_called_once_with(
        project_id=project.id,
    )

    video = db_session.scalar(
        select(ProjectVideo).where(ProjectVideo.project_id == project.id)
    )

    assert video is not None
    assert video.mux_upload_id == "mux-upload-123"
    assert video.mux_asset_id is None
    assert video.mux_playback_id is None
    assert video.status == "uploading"
    assert video.original_filename == ("bookaify-demo.mp4")


def test_video_upload_rejects_second_video_before_mux_call(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    db_session.add(
        ProjectVideo(
            project_id=project.id,
            mux_upload_id="existing-upload",
            status="processing",
            original_filename="existing.mp4",
        )
    )
    db_session.commit()

    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "replacement.mp4",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "This project already has a video."}
    mocked.assert_not_called()


def test_video_upload_rejects_empty_filename(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "",
        },
    )

    assert response.status_code == 422
    mocked.assert_not_called()


def test_video_upload_handles_missing_mux_configuration(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    mocked = Mock(
        side_effect=MuxConfigurationError(
            "Mux is not configured. Missing: MUX_TOKEN_ID"
        )
    )

    monkeypatch.setattr(
        "app.api.v1.projects.create_direct_upload",
        mocked,
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "demo.mp4",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": ("Mux is not configured. Missing: MUX_TOKEN_ID")
    }

    assert (
        db_session.scalar(
            select(ProjectVideo).where(ProjectVideo.project_id == project.id)
        )
        is None
    )


def test_video_upload_handles_mux_api_failure(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    mocked = Mock(side_effect=MuxAPIError("Could not connect to Mux."))

    monkeypatch.setattr(
        "app.api.v1.projects.create_direct_upload",
        mocked,
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "demo.mp4",
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not connect to Mux."}

    assert (
        db_session.scalar(
            select(ProjectVideo).where(ProjectVideo.project_id == project.id)
        )
        is None
    )


def test_video_upload_rejects_whitespace_filename(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "   ",
        },
    )

    assert response.status_code == 422
    mocked.assert_not_called()


def add_ready_video(
    db_session: Session,
    *,
    project: Project,
    asset_id: str = "mux-asset-123",
) -> ProjectVideo:
    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="mux-upload-ready",
        mux_asset_id=asset_id,
        mux_playback_id="mux-playback-123",
        status="ready",
        original_filename="demo.mp4",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


def test_remove_video_requires_authentication(
    client: TestClient,
    db_session: Session,
) -> None:
    project = create_project(db_session)
    add_ready_video(db_session, project=project)

    response = client.delete(f"/api/v1/projects/{project.id}/video")

    assert response.status_code == 401


def test_remove_video_rejects_missing_project(
    client: TestClient,
    authenticated_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocked = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        mocked,
    )

    response = client.delete(
        "/api/v1/projects/999999/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found."}
    mocked.assert_not_called()


def test_remove_video_rejects_project_without_video(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    mocked = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        mocked,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "This project does not have a video."}
    mocked.assert_not_called()


def test_remove_video_deletes_mux_asset_before_database_record(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="asset-to-delete",
    )
    video_id = video.id

    mocked = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        mocked,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    mocked.assert_called_once_with(
        upload_id="mux-upload-ready",
        asset_id="asset-to-delete",
    )
    assert db_session.get(ProjectVideo, video_id) is None
    assert db_session.get(Project, project.id) is not None


def test_remove_video_without_asset_id_reconciles_mux_before_database_delete(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="upload-only",
        status="uploading",
        original_filename="unfinished.mp4",
    )
    db_session.add(video)
    db_session.commit()
    video_id = video.id

    cleanup = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    cleanup.assert_called_once_with(
        upload_id="upload-only",
        asset_id=None,
    )
    assert db_session.get(ProjectVideo, video_id) is None
    assert db_session.get(Project, project.id) is not None


def test_remove_video_preserves_upload_only_record_when_mux_cleanup_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="upload-still-active",
        status="uploading",
        original_filename="unfinished.mp4",
    )
    db_session.add(video)
    db_session.commit()
    video_id = video.id

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxAPIError("Could not safely clean up Mux upload.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not safely clean up Mux upload."}
    assert db_session.get(ProjectVideo, video_id) is not None
    assert db_session.get(Project, project.id) is not None


def test_remove_video_preserves_database_record_when_mux_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="asset-still-needed",
    )
    video_id = video.id

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxAPIError("Mux unavailable.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Mux unavailable."}
    assert db_session.get(ProjectVideo, video_id) is not None
    assert db_session.get(Project, project.id) is not None


def test_remove_video_preserves_database_record_when_mux_unconfigured(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="asset-still-needed",
    )
    video_id = video.id

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxConfigurationError("Mux is not configured.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Mux is not configured."}
    assert db_session.get(ProjectVideo, video_id) is not None
    assert db_session.get(Project, project.id) is not None
