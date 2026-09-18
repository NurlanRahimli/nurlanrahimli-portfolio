from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Project, ProjectVideo
from app.services.mux_webhooks import (
    process_mux_video_event,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

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


def create_video(
    db: Session,
    *,
    status: str = "uploading",
    upload_id: str = "upload-123",
    asset_id: str | None = None,
) -> ProjectVideo:
    project = Project(
        slug="bookaify",
        title="Bookaify",
        is_published=False,
        display_order=0,
    )
    db.add(project)
    db.flush()

    video = ProjectVideo(
        project_id=project.id,
        mux_upload_id=upload_id,
        mux_asset_id=asset_id,
        status=status,
        original_filename="demo.mp4",
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    return video


def test_upload_asset_created_sets_asset_and_processing(
    db_session: Session,
) -> None:
    video = create_video(db_session)

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.upload.asset_created",
            "data": {
                "id": "upload-123",
                "asset_id": "asset-123",
                "status": "asset_created",
            },
        },
    )

    db_session.refresh(video)

    assert handled is True
    assert video.mux_asset_id == "asset-123"
    assert video.status == "processing"
    assert video.error_message is None


def test_upload_asset_created_is_idempotent(
    db_session: Session,
) -> None:
    video = create_video(db_session)

    payload = {
        "type": "video.upload.asset_created",
        "data": {
            "id": "upload-123",
            "asset_id": "asset-123",
        },
    }

    assert (
        process_mux_video_event(
            db_session,
            payload,
        )
        is True
    )

    assert (
        process_mux_video_event(
            db_session,
            payload,
        )
        is True
    )

    db_session.refresh(video)

    assert video.mux_asset_id == "asset-123"
    assert video.status == "processing"


def test_asset_ready_persists_playback_metadata(
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="processing",
        asset_id="asset-123",
    )

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.asset.ready",
            "data": {
                "id": "asset-123",
                "status": "ready",
                "duration": 23.857167,
                "aspect_ratio": "16:9",
                "playback_ids": [
                    {
                        "id": "playback-123",
                        "policy": "public",
                    }
                ],
            },
        },
    )

    db_session.refresh(video)

    assert handled is True
    assert video.status == "ready"
    assert video.mux_playback_id == "playback-123"
    assert video.duration_seconds == pytest.approx(23.857167)
    assert video.aspect_ratio == "16:9"
    assert video.error_message is None


def test_duplicate_ready_event_is_safe(
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="processing",
        asset_id="asset-123",
    )

    payload = {
        "type": "video.asset.ready",
        "data": {
            "id": "asset-123",
            "duration": 10.5,
            "aspect_ratio": "16:9",
            "playback_ids": [
                {
                    "id": "playback-123",
                    "policy": "public",
                }
            ],
        },
    }

    assert (
        process_mux_video_event(
            db_session,
            payload,
        )
        is True
    )
    assert (
        process_mux_video_event(
            db_session,
            payload,
        )
        is True
    )

    db_session.refresh(video)

    assert video.status == "ready"
    assert video.mux_playback_id == "playback-123"
    assert video.duration_seconds == pytest.approx(10.5)


def test_asset_error_sets_error_state(
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="processing",
        asset_id="asset-123",
    )

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.asset.errored",
            "data": {
                "id": "asset-123",
                "errors": {
                    "messages": [
                        "Invalid video file.",
                    ]
                },
            },
        },
    )

    db_session.refresh(video)

    assert handled is True
    assert video.status == "error"
    assert video.error_message == ("Invalid video file.")


def test_upload_error_sets_error_state(
    db_session: Session,
) -> None:
    video = create_video(db_session)

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.upload.errored",
            "data": {
                "id": "upload-123",
                "error": {
                    "message": "Upload failed.",
                },
            },
        },
    )

    db_session.refresh(video)

    assert handled is True
    assert video.status == "error"
    assert video.error_message == "Upload failed."


def test_ready_video_does_not_regress_on_asset_error(
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="ready",
        asset_id="asset-123",
    )
    video.mux_playback_id = "playback-123"
    db_session.commit()

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.asset.errored",
            "data": {
                "id": "asset-123",
                "errors": {
                    "messages": [
                        "Late duplicate error.",
                    ]
                },
            },
        },
    )

    db_session.refresh(video)

    assert handled is True
    assert video.status == "ready"
    assert video.mux_playback_id == "playback-123"
    assert video.error_message is None


def test_ready_video_does_not_regress_on_upload_event(
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="ready",
        asset_id="asset-123",
    )
    video.mux_playback_id = "playback-123"
    db_session.commit()

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.upload.asset_created",
            "data": {
                "id": "upload-123",
                "asset_id": "asset-123",
            },
        },
    )

    db_session.refresh(video)

    assert handled is True
    assert video.status == "ready"
    assert video.mux_playback_id == "playback-123"


def test_unknown_resource_is_ignored(
    db_session: Session,
) -> None:
    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.asset.ready",
            "data": {
                "id": "unknown-asset",
            },
        },
    )

    assert handled is False


def test_unknown_event_is_ignored(
    db_session: Session,
) -> None:
    create_video(db_session)

    handled = process_mux_video_event(
        db_session,
        {
            "type": "video.asset.created",
            "data": {
                "id": "asset-123",
            },
        },
    )

    assert handled is False


def test_malformed_event_is_ignored(
    db_session: Session,
) -> None:
    create_video(db_session)

    assert (
        process_mux_video_event(
            db_session,
            {
                "type": "video.asset.ready",
                "data": None,
            },
        )
        is False
    )
