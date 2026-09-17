from collections.abc import Generator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models import AdminUser, MediaAsset, MediaVariant
from app.services import media_library
from app.services.r2_storage import r2_storage


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def upload(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        self.objects[key] = (content, content_type)

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def public_url(self, key: str) -> str:
        return f"https://media.test/{key}"


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
def fake_storage(monkeypatch: pytest.MonkeyPatch) -> FakeStorage:
    storage = FakeStorage()

    monkeypatch.setattr(
        media_library,
        "r2_storage",
        storage,
    )

    monkeypatch.setattr(
        r2_storage,
        "public_url",
        storage.public_url,
    )

    return storage


@pytest.fixture
def client(
    db_session: Session,
    fake_storage: FakeStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient]:
    del fake_storage

    def override_get_db() -> Generator[Session]:
        yield db_session

    original_create = media_library.create_media_asset
    original_delete = media_library.delete_media_asset

    def create_with_fake_storage(
        db: Session,
        *,
        content: bytes,
        original_filename: str,
        mime_type: str,
        alt_text: str | None = None,
    ):
        return original_create(
            db,
            content=content,
            original_filename=original_filename,
            mime_type=mime_type,
            alt_text=alt_text,
            storage=media_library.r2_storage,
        )

    def delete_with_fake_storage(
        db: Session,
        *,
        asset: MediaAsset,
    ) -> None:
        original_delete(
            db,
            asset=asset,
            storage=media_library.r2_storage,
        )

    monkeypatch.setattr(
        "app.api.v1.media.create_media_asset",
        create_with_fake_storage,
    )

    monkeypatch.setattr(
        "app.api.v1.media.delete_media_asset",
        delete_with_fake_storage,
    )

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_headers(
    db_session: Session,
) -> dict[str, str]:
    admin = AdminUser(
        email="media-admin@example.com",
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


def make_test_image(
    *,
    width: int = 1600,
    height: int = 900,
) -> bytes:
    output = BytesIO()

    Image.new(
        "RGB",
        (width, height),
        "white",
    ).save(
        output,
        format="PNG",
    )

    return output.getvalue()


def upload_test_image(
    client: TestClient,
    headers: dict[str, str],
    *,
    filename: str = "Portfolio Hero Image.png",
    alt_text: str = "Portfolio hero",
):
    return client.post(
        "/api/v1/media",
        headers=headers,
        files={
            "file": (
                filename,
                make_test_image(),
                "image/png",
            ),
        },
        data={
            "alt_text": alt_text,
        },
    )


def test_media_list_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/media")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }


def test_media_upload_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/media",
        files={
            "file": (
                "test.png",
                make_test_image(),
                "image/png",
            ),
        },
    )

    assert response.status_code == 401


def test_upload_image_creates_asset_and_variants(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    fake_storage: FakeStorage,
) -> None:
    response = upload_test_image(
        client,
        authenticated_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["filename"] == "portfolio-hero-image.png"
    assert body["original_filename"] == "Portfolio Hero Image.png"
    assert body["mime_type"] == "image/png"
    assert body["file_type"] == "image"
    assert body["width"] == 1600
    assert body["height"] == 900
    assert body["alt_text"] == "Portfolio hero"

    assert body["url"].startswith("https://media.test/media/images/")

    assert len(body["variants"]) == 4

    variants = {item["variant_name"]: item for item in body["variants"]}

    assert variants["thumbnail"]["width"] == 400
    assert variants["small"]["width"] == 800
    assert variants["medium"]["width"] == 1400
    assert variants["large"]["width"] == 1600

    assert all(item["mime_type"] == "image/webp" for item in body["variants"])

    asset = db_session.get(
        MediaAsset,
        body["id"],
    )

    assert asset is not None
    assert len(fake_storage.objects) == 5


def test_media_list_supports_search_and_filter(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    upload_response = upload_test_image(
        client,
        authenticated_headers,
        filename="Project Screenshot.png",
        alt_text="Dashboard project preview",
    )

    assert upload_response.status_code == 201

    response = client.get(
        "/api/v1/media",
        headers=authenticated_headers,
        params={
            "search": "dashboard",
            "file_type": "image",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert len(body["items"]) == 1

    assert body["items"][0]["original_filename"] == "Project Screenshot.png"


def test_media_detail_returns_asset(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    upload_response = upload_test_image(
        client,
        authenticated_headers,
    )

    asset_id = upload_response.json()["id"]

    response = client.get(
        f"/api/v1/media/{asset_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == asset_id


def test_media_detail_returns_404_for_missing_asset(
    client: TestClient,
    authenticated_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/media/999999",
        headers=authenticated_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Media asset not found.",
    }


def test_patch_media_alt_text(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
) -> None:
    upload_response = upload_test_image(
        client,
        authenticated_headers,
    )

    asset_id = upload_response.json()["id"]

    response = client.patch(
        f"/api/v1/media/{asset_id}",
        headers=authenticated_headers,
        json={
            "alt_text": "Updated portfolio preview",
        },
    )

    assert response.status_code == 200
    assert response.json()["alt_text"] == "Updated portfolio preview"

    asset = db_session.get(
        MediaAsset,
        asset_id,
    )

    assert asset is not None
    assert asset.alt_text == "Updated portfolio preview"


def test_delete_media_removes_database_and_storage(
    client: TestClient,
    authenticated_headers: dict[str, str],
    db_session: Session,
    fake_storage: FakeStorage,
) -> None:
    upload_response = upload_test_image(
        client,
        authenticated_headers,
    )

    assert upload_response.status_code == 201

    asset_id = upload_response.json()["id"]

    assert len(fake_storage.objects) == 5

    response = client.delete(
        f"/api/v1/media/{asset_id}",
        headers=authenticated_headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    db_session.expire_all()

    assert (
        db_session.get(
            MediaAsset,
            asset_id,
        )
        is None
    )

    remaining_variants = db_session.scalars(
        select(MediaVariant).where(MediaVariant.media_asset_id == asset_id)
    ).all()

    assert remaining_variants == []
    assert fake_storage.objects == {}
