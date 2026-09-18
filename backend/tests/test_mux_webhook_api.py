import hashlib
import hmac
import json
import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import Project, ProjectVideo


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    with testing_session_local() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(
        settings,
        "mux_webhook_secret",
        "test-webhook-secret",
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def encode_payload(
    payload: object,
) -> bytes:
    return json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()


def mux_headers(
    body: bytes,
    *,
    secret: str = "test-webhook-secret",
    timestamp: int | None = None,
) -> dict[str, str]:
    timestamp = int(time.time()) if timestamp is None else timestamp

    signed_payload = str(timestamp).encode("ascii") + b"." + body

    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return {
        "mux-signature": (f"t={timestamp},v1={signature}"),
        "content-type": "application/json",
    }


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


def post_signed(
    client: TestClient,
    payload: object,
) -> object:
    body = encode_payload(payload)

    return client.post(
        "/api/v1/webhooks/mux",
        headers=mux_headers(body),
        content=body,
    )


def test_requires_signature_header(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/webhooks/mux",
        content=b"{}",
        headers={
            "content-type": "application/json",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing Mux webhook signature."}


def test_rejects_invalid_signature(
    client: TestClient,
) -> None:
    body = b"{}"

    response = client.post(
        "/api/v1/webhooks/mux",
        content=body,
        headers=mux_headers(
            body,
            secret="wrong-secret",
        ),
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid Mux webhook signature."}


def test_rejects_stale_signature(
    client: TestClient,
) -> None:
    body = b"{}"

    response = client.post(
        "/api/v1/webhooks/mux",
        content=body,
        headers=mux_headers(
            body,
            timestamp=int(time.time()) - 301,
        ),
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Mux webhook timestamp is too old."}


def test_requires_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "mux_webhook_secret",
        "",
    )

    body = b"{}"

    response = client.post(
        "/api/v1/webhooks/mux",
        headers=mux_headers(body),
        content=body,
    )

    assert response.status_code == 503


def test_rejects_invalid_json_after_signature_verification(
    client: TestClient,
) -> None:
    body = b"{not-json"

    response = client.post(
        "/api/v1/webhooks/mux",
        headers=mux_headers(body),
        content=body,
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Mux webhook body is not valid JSON."}


def test_ignores_unknown_event(
    client: TestClient,
) -> None:
    response = post_signed(
        client,
        {
            "type": "video.asset.created",
            "data": {"id": "asset-123"},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "received": True,
        "handled": False,
    }


def test_updates_upload_to_processing(
    client: TestClient,
    db_session: Session,
) -> None:
    video = create_video(db_session)

    response = post_signed(
        client,
        {
            "type": "video.upload.asset_created",
            "data": {
                "id": "upload-123",
                "asset_id": "asset-123",
            },
        },
    )

    assert response.status_code == 200

    db_session.refresh(video)

    assert video.mux_asset_id == "asset-123"
    assert video.status == "processing"


def test_updates_asset_to_ready(
    client: TestClient,
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="processing",
        asset_id="asset-123",
    )

    response = post_signed(
        client,
        {
            "type": "video.asset.ready",
            "data": {
                "id": "asset-123",
                "duration": 42.75,
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

    assert response.status_code == 200

    db_session.refresh(video)

    assert video.status == "ready"
    assert video.mux_playback_id == "playback-123"
    assert video.duration_seconds == pytest.approx(42.75)
    assert video.aspect_ratio == "16:9"


def test_records_asset_error(
    client: TestClient,
    db_session: Session,
) -> None:
    video = create_video(
        db_session,
        status="processing",
        asset_id="asset-123",
    )

    response = post_signed(
        client,
        {
            "type": "video.asset.errored",
            "data": {
                "id": "asset-123",
                "errors": {
                    "messages": [
                        "Invalid source video.",
                    ]
                },
            },
        },
    )

    assert response.status_code == 200

    db_session.refresh(video)

    assert video.status == "error"
    assert video.error_message == "Invalid source video."
