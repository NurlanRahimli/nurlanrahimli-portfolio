from io import BytesIO

from PIL import Image
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.media import MediaAsset, MediaVariant
from app.services.media_library import (
    create_media_asset,
    delete_media_asset,
    list_media_assets,
    sanitize_filename,
    update_media_asset,
)


class FakeStorage:
    def __init__(self) -> None:
        self.uploaded: dict[str, tuple[bytes, str]] = {}
        self.deleted: list[str] = []

    def upload(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        self.uploaded[key] = (
            content,
            content_type,
        )

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.uploaded.pop(key, None)


def make_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    return engine


def make_image() -> bytes:
    image = Image.new(
        "RGB",
        (1600, 900),
        "white",
    )
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_sanitize_filename() -> None:
    assert sanitize_filename("My Project Screenshot.PNG") == "my-project-screenshot.png"


def test_create_image_uploads_original_and_variants() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)
    storage = FakeStorage()

    with Session(engine) as session:
        asset = create_media_asset(
            session,
            content=make_image(),
            original_filename="Project Screenshot.png",
            mime_type="image/png",
            alt_text="Project dashboard",
            storage=storage,
        )

        assert asset.id is not None
        assert asset.file_type == "image"
        assert asset.alt_text == "Project dashboard"
        assert len(asset.variants) == 4
        assert len(storage.uploaded) == 5

        stored = session.get(
            MediaAsset,
            asset.id,
        )

        assert stored is not None


def test_create_pdf_has_no_variants() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)
    storage = FakeStorage()

    with Session(engine) as session:
        asset = create_media_asset(
            session,
            content=b"%PDF-1.7\nresume",
            original_filename="Nurlan Resume.pdf",
            mime_type="application/pdf",
            storage=storage,
        )

        assert asset.file_type == "document"
        assert asset.variants == []
        assert len(storage.uploaded) == 1


def test_list_media_supports_search_and_filter() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                MediaAsset(
                    filename="portfolio.png",
                    original_filename="Portfolio.png",
                    storage_key="one",
                    mime_type="image/png",
                    file_type="image",
                    file_size=1,
                    width=100,
                    height=100,
                    alt_text="Dashboard screenshot",
                ),
                MediaAsset(
                    filename="resume.pdf",
                    original_filename="Resume.pdf",
                    storage_key="two",
                    mime_type="application/pdf",
                    file_type="document",
                    file_size=1,
                ),
            ]
        )
        session.commit()

        assets, total = list_media_assets(
            session,
            search="dashboard",
            file_type="image",
        )

        assert total == 1
        assert len(assets) == 1
        assert assets[0].filename == "portfolio.png"


def test_update_media_alt_text() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        asset = MediaAsset(
            filename="image.png",
            original_filename="Image.png",
            storage_key="image",
            mime_type="image/png",
            file_type="image",
            file_size=1,
            width=100,
            height=100,
        )

        session.add(asset)
        session.commit()

        updated = update_media_asset(
            session,
            asset=asset,
            alt_text="  Updated description  ",
        )

        assert updated.alt_text == "Updated description"


def test_delete_media_removes_r2_objects_and_database_rows() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)
    storage = FakeStorage()

    with Session(engine) as session:
        asset = MediaAsset(
            filename="delete.png",
            original_filename="Delete.png",
            storage_key="original",
            mime_type="image/png",
            file_type="image",
            file_size=1,
            width=100,
            height=100,
        )

        asset.variants.append(
            MediaVariant(
                variant_name="thumbnail",
                storage_key="thumbnail",
                mime_type="image/webp",
                file_size=1,
                width=50,
                height=50,
            )
        )

        session.add(asset)
        session.commit()

        asset_id = asset.id

        delete_media_asset(
            session,
            asset=asset,
            storage=storage,
        )

        assert (
            session.get(
                MediaAsset,
                asset_id,
            )
            is None
        )

        assert session.scalar(select(MediaVariant)) is None

        assert set(storage.deleted) == {
            "original",
            "thumbnail",
        }
