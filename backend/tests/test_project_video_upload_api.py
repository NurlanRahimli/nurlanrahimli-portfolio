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
    assert response.json() == {
        "detail": "The current project video has not finished processing yet."
    }
    mocked.assert_not_called()


def test_video_upload_creates_pending_replacement_for_ready_video(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="active-upload",
        mux_asset_id="active-asset",
        mux_playback_id="active-playback",
        status="ready",
        duration_seconds=12.5,
        aspect_ratio="16:9",
        original_filename="active.mp4",
    )
    db_session.add(video)
    db_session.commit()

    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "replacement.mp4",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "project_id": project.id,
        "upload_id": "mux-upload-123",
        "upload_url": "https://storage.video.mux.com/direct-upload-url",
        "status": "uploading",
    }

    mocked.assert_called_once_with(
        project_id=project.id,
    )

    db_session.refresh(video)

    # Active video remains completely untouched.
    assert video.mux_upload_id == "active-upload"
    assert video.mux_asset_id == "active-asset"
    assert video.mux_playback_id == "active-playback"
    assert video.status == "ready"
    assert video.duration_seconds == pytest.approx(12.5)
    assert video.aspect_ratio == "16:9"
    assert video.original_filename == "active.mp4"

    # Replacement lives only in pending state.
    assert video.pending_mux_upload_id == "mux-upload-123"
    assert video.pending_mux_asset_id is None
    assert video.pending_mux_playback_id is None
    assert video.pending_status == "uploading"
    assert video.pending_duration_seconds is None
    assert video.pending_aspect_ratio is None
    assert video.pending_original_filename == "replacement.mp4"
    assert video.pending_error_message is None


def test_video_upload_rejects_second_pending_replacement_before_mux_call(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id="active-upload",
        mux_asset_id="active-asset",
        mux_playback_id="active-playback",
        status="ready",
        original_filename="active.mp4",
        pending_mux_upload_id="pending-upload",
        pending_status="uploading",
        pending_original_filename="pending.mp4",
    )
    db_session.add(video)
    db_session.commit()

    mocked = mock_direct_upload(monkeypatch)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={
            "original_filename": "another-replacement.mp4",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A replacement video is already uploading or processing."
    }

    mocked.assert_not_called()

    db_session.refresh(video)

    assert video.mux_asset_id == "active-asset"
    assert video.mux_playback_id == "active-playback"
    assert video.status == "ready"

    assert video.pending_mux_upload_id == "pending-upload"
    assert video.pending_status == "uploading"
    assert video.pending_original_filename == "pending.mp4"


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


def test_cancel_video_replacement_requires_authentication(
    client: TestClient,
    db_session: Session,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )
    video.pending_mux_upload_id = "replacement-upload"
    video.pending_status = "uploading"
    video.pending_original_filename = "replacement.mp4"
    db_session.commit()

    response = client.delete(f"/api/v1/projects/{project.id}/video/replacement")

    assert response.status_code == 401


def test_cancel_video_replacement_rejects_missing_project(
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
        "/api/v1/projects/999999/video/replacement",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found."}
    mocked.assert_not_called()


def test_cancel_video_replacement_rejects_project_without_pending_video(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    mocked = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        mocked,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video/replacement",
        headers=authenticated_headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "This project does not have a pending replacement video."
    }
    mocked.assert_not_called()


def test_cancel_video_replacement_cleans_pending_only(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    active_upload_id = video.mux_upload_id
    active_asset_id = video.mux_asset_id
    active_playback_id = video.mux_playback_id
    active_filename = video.original_filename

    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"
    db_session.commit()

    cleanup = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video/replacement",
        headers=authenticated_headers,
    )

    assert response.status_code == 204

    cleanup.assert_called_once_with(
        upload_id="replacement-upload",
        asset_id="replacement-asset",
    )

    db_session.refresh(video)

    # Active video remains untouched.
    assert video.mux_upload_id == active_upload_id
    assert video.mux_asset_id == active_asset_id
    assert video.mux_playback_id == active_playback_id
    assert video.status == "ready"
    assert video.original_filename == active_filename

    # Pending replacement is completely cleared.
    assert video.pending_mux_upload_id is None
    assert video.pending_mux_asset_id is None
    assert video.pending_mux_playback_id is None
    assert video.pending_status is None
    assert video.pending_duration_seconds is None
    assert video.pending_aspect_ratio is None
    assert video.pending_original_filename is None
    assert video.pending_error_message is None


def test_cancel_video_replacement_preserves_pending_when_mux_cleanup_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    active_asset_id = video.mux_asset_id
    active_playback_id = video.mux_playback_id

    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"
    db_session.commit()

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxAPIError("Mux unavailable.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video/replacement",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Mux unavailable."}

    db_session.refresh(video)

    # Active video remains untouched.
    assert video.mux_asset_id == active_asset_id
    assert video.mux_playback_id == active_playback_id
    assert video.status == "ready"

    # Pending state remains so cleanup can be retried.
    assert video.pending_mux_upload_id == "replacement-upload"
    assert video.pending_mux_asset_id == "replacement-asset"
    assert video.pending_status == "processing"
    assert video.pending_original_filename == "replacement.mp4"


def test_cancel_video_replacement_preserves_pending_when_mux_unconfigured(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    video.pending_mux_upload_id = "replacement-upload"
    video.pending_status = "uploading"
    video.pending_original_filename = "replacement.mp4"
    db_session.commit()

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxConfigurationError("Mux is not configured.")),
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video/replacement",
        headers=authenticated_headers,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Mux is not configured."}

    db_session.refresh(video)

    assert video.status == "ready"
    assert video.pending_mux_upload_id == "replacement-upload"
    assert video.pending_status == "uploading"
    assert video.pending_original_filename == "replacement.mp4"


def test_remove_video_cleans_pending_then_active_before_database_delete(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )
    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"
    db_session.commit()

    video_id = video.id
    cleanup_calls: list[tuple[str | None, str | None]] = []

    def fake_cleanup(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        assert db_session.get(ProjectVideo, video_id) is not None
        cleanup_calls.append((upload_id, asset_id))

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
        ("mux-upload-ready", "active-asset"),
    ]
    assert db_session.get(ProjectVideo, video_id) is None
    assert db_session.get(Project, project.id) is not None


def test_remove_video_preserves_active_and_pending_when_pending_cleanup_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )
    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"
    db_session.commit()

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
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Pending replacement cleanup failed."}
    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
    ]

    preserved = db_session.get(ProjectVideo, video_id)
    assert preserved is not None
    assert preserved.mux_asset_id == "active-asset"
    assert preserved.status == "ready"
    assert preserved.pending_mux_upload_id == "replacement-upload"
    assert preserved.pending_mux_asset_id == "replacement-asset"
    assert db_session.get(Project, project.id) is not None


def test_remove_video_cleans_pending_cleanup_then_active_and_clears_each_slot(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Previous cleanup failed."

    db_session.commit()

    video_id = video.id
    cleanup_calls: list[tuple[str | None, str | None]] = []

    def fake_cleanup(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        current = db_session.get(ProjectVideo, video_id)
        assert current is not None

        if not cleanup_calls:
            assert current.pending_mux_upload_id == "replacement-upload"
            assert current.cleanup_mux_upload_id == "old-upload"
            assert current.mux_asset_id == "active-asset"
        elif len(cleanup_calls) == 1:
            # Pending cleanup already succeeded and was durably cleared.
            assert current.pending_mux_upload_id is None
            assert current.pending_mux_asset_id is None
            assert current.cleanup_mux_upload_id == "old-upload"
            assert current.cleanup_mux_asset_id == "old-asset"
            assert current.mux_asset_id == "active-asset"
        elif len(cleanup_calls) == 2:
            # Cleanup-old also succeeded and was durably cleared.
            assert current.pending_mux_upload_id is None
            assert current.cleanup_mux_upload_id is None
            assert current.cleanup_mux_asset_id is None
            assert current.cleanup_error_message is None
            assert current.mux_asset_id == "active-asset"

        cleanup_calls.append((upload_id, asset_id))

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
        ("old-upload", "old-asset"),
        ("mux-upload-ready", "active-asset"),
    ]

    assert db_session.get(ProjectVideo, video_id) is None
    assert db_session.get(Project, project.id) is not None


def test_remove_video_preserves_truthful_state_when_cleanup_old_fails(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Previous cleanup failed."

    db_session.commit()

    video_id = video.id
    cleanup_calls: list[tuple[str | None, str | None]] = []

    def fake_cleanup(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        cleanup_calls.append((upload_id, asset_id))

        if upload_id == "old-upload":
            raise MuxAPIError("Old cleanup retry failed.")

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Old cleanup retry failed.",
    }

    # Active cleanup must never run after cleanup-old fails.
    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
        ("old-upload", "old-asset"),
    ]

    preserved = db_session.get(ProjectVideo, video_id)
    assert preserved is not None

    # Pending was successfully deleted remotely, so its DB state must
    # already be gone.
    assert preserved.pending_mux_upload_id is None
    assert preserved.pending_mux_asset_id is None
    assert preserved.pending_status is None
    assert preserved.pending_original_filename is None

    # Cleanup-old failed, so those IDs must remain retryable.
    assert preserved.cleanup_mux_upload_id == "old-upload"
    assert preserved.cleanup_mux_asset_id == "old-asset"
    assert preserved.cleanup_error_message == "Previous cleanup failed."

    # Active video was never touched.
    assert preserved.mux_asset_id == "active-asset"
    assert preserved.status == "ready"
    assert db_session.get(Project, project.id) is not None


def test_remove_video_preserves_only_active_when_active_cleanup_fails_last(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    video.pending_mux_upload_id = "replacement-upload"
    video.pending_mux_asset_id = "replacement-asset"
    video.pending_status = "processing"
    video.pending_original_filename = "replacement.mp4"

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Previous cleanup failed."

    db_session.commit()

    video_id = video.id
    cleanup_calls: list[tuple[str | None, str | None]] = []

    def fake_cleanup(
        *,
        upload_id: str | None,
        asset_id: str | None,
    ) -> None:
        cleanup_calls.append((upload_id, asset_id))

        if asset_id == "active-asset":
            raise MuxAPIError("Active cleanup failed.")

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        fake_cleanup,
    )

    response = client.delete(
        f"/api/v1/projects/{project.id}/video",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Active cleanup failed.",
    }

    assert cleanup_calls == [
        ("replacement-upload", "replacement-asset"),
        ("old-upload", "old-asset"),
        ("mux-upload-ready", "active-asset"),
    ]

    preserved = db_session.get(ProjectVideo, video_id)
    assert preserved is not None

    # Both non-active resources were successfully removed.
    assert preserved.pending_mux_upload_id is None
    assert preserved.pending_mux_asset_id is None
    assert preserved.cleanup_mux_upload_id is None
    assert preserved.cleanup_mux_asset_id is None
    assert preserved.cleanup_error_message is None

    # Active cleanup failed, so the active resource remains represented.
    assert preserved.mux_asset_id == "active-asset"
    assert preserved.status == "ready"
    assert db_session.get(Project, project.id) is not None


def test_create_video_upload_rejects_cleanup_pending_before_mux_upload(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Old cleanup failed."
    db_session.commit()

    create_upload = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.create_direct_upload",
        create_upload,
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/upload",
        headers=authenticated_headers,
        json={"original_filename": "new-replacement.mp4"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "The previous video replacement still has cleanup pending.",
    }

    # Critical: rejection happened before any new remote Mux upload existed.
    create_upload.assert_not_called()

    db_session.refresh(video)

    assert video.mux_asset_id == "active-asset"
    assert video.status == "ready"
    assert video.cleanup_mux_upload_id == "old-upload"
    assert video.cleanup_mux_asset_id == "old-asset"
    assert video.cleanup_error_message == "Old cleanup failed."
    assert video.pending_mux_upload_id is None
    assert video.pending_mux_asset_id is None


def test_retry_video_cleanup_requires_authentication(
    client: TestClient,
    db_session: Session,
) -> None:
    project = create_project(db_session)

    response = client.post(
        f"/api/v1/projects/{project.id}/video/cleanup/retry",
    )

    assert response.status_code == 401


def test_retry_video_cleanup_returns_404_for_missing_project(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/projects/999999/video/cleanup/retry",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found."}


def test_retry_video_cleanup_rejects_when_no_cleanup_is_pending(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    project = create_project(db_session)

    add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/cleanup/retry",
        headers=authenticated_headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "This project does not have video cleanup pending.",
    }


def test_retry_video_cleanup_cleans_only_old_resource_and_clears_state(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    active_upload_id = video.mux_upload_id
    active_asset_id = video.mux_asset_id
    active_playback_id = video.mux_playback_id

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Previous cleanup failed."
    db_session.commit()

    cleanup = Mock()
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        cleanup,
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/cleanup/retry",
        headers=authenticated_headers,
    )

    assert response.status_code == 204

    cleanup.assert_called_once_with(
        upload_id="old-upload",
        asset_id="old-asset",
    )

    db_session.refresh(video)

    assert video.cleanup_mux_upload_id is None
    assert video.cleanup_mux_asset_id is None
    assert video.cleanup_error_message is None

    # Current active playback must be completely untouched.
    assert video.mux_upload_id == active_upload_id
    assert video.mux_asset_id == active_asset_id
    assert video.mux_playback_id == active_playback_id
    assert video.status == "ready"


def test_retry_video_cleanup_failure_preserves_ids_and_updates_error(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    active_upload_id = video.mux_upload_id
    active_asset_id = video.mux_asset_id

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Previous cleanup failed."
    db_session.commit()

    cleanup = Mock(side_effect=MuxAPIError("Old Mux asset cleanup failed again."))
    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        cleanup,
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/cleanup/retry",
        headers=authenticated_headers,
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Old Mux asset cleanup failed again.",
    }

    cleanup.assert_called_once_with(
        upload_id="old-upload",
        asset_id="old-asset",
    )

    db_session.refresh(video)

    # Failed cleanup remains retryable.
    assert video.cleanup_mux_upload_id == "old-upload"
    assert video.cleanup_mux_asset_id == "old-asset"
    assert video.cleanup_error_message == "Old Mux asset cleanup failed again."

    # Current active playback remains untouched.
    assert video.mux_upload_id == active_upload_id
    assert video.mux_asset_id == active_asset_id
    assert video.status == "ready"


def test_retry_video_cleanup_unconfigured_preserves_ids_and_updates_error(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = create_project(db_session)
    video = add_ready_video(
        db_session,
        project=project,
        asset_id="active-asset",
    )

    video.cleanup_mux_upload_id = "old-upload"
    video.cleanup_mux_asset_id = "old-asset"
    video.cleanup_error_message = "Previous cleanup failed."
    db_session.commit()

    monkeypatch.setattr(
        "app.api.v1.projects.cleanup_project_video",
        Mock(side_effect=MuxConfigurationError("Mux is not configured.")),
    )

    response = client.post(
        f"/api/v1/projects/{project.id}/video/cleanup/retry",
        headers=authenticated_headers,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Mux is not configured.",
    }

    db_session.refresh(video)

    assert video.cleanup_mux_upload_id == "old-upload"
    assert video.cleanup_mux_asset_id == "old-asset"
    assert video.cleanup_error_message == "Mux is not configured."
    assert video.mux_asset_id == "active-asset"
    assert video.status == "ready"
