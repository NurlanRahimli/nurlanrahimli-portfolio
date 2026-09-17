from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.media import MediaAsset, MediaVariant


def make_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record,
    ) -> None:
        del connection_record

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def test_media_asset_persists() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        asset = MediaAsset(
            filename="portfolio-image.png",
            original_filename="Portfolio Image.png",
            storage_key="media/originals/portfolio-image.png",
            mime_type="image/png",
            file_type="image",
            file_size=1024,
            width=1200,
            height=800,
            alt_text="Portfolio project screenshot",
        )

        session.add(asset)
        session.commit()

        stored = session.scalar(
            select(MediaAsset).where(
                MediaAsset.storage_key == "media/originals/portfolio-image.png"
            )
        )

        assert stored is not None
        assert stored.filename == "portfolio-image.png"
        assert stored.file_type == "image"
        assert stored.width == 1200
        assert stored.height == 800
        assert stored.alt_text == "Portfolio project screenshot"


def test_media_asset_owns_variants() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        asset = MediaAsset(
            filename="hero.jpg",
            original_filename="Hero.jpg",
            storage_key="media/originals/hero.jpg",
            mime_type="image/jpeg",
            file_type="image",
            file_size=5000,
            width=3000,
            height=2000,
        )

        asset.variants.extend(
            [
                MediaVariant(
                    variant_name="thumbnail",
                    storage_key=("media/variants/hero-thumbnail.webp"),
                    mime_type="image/webp",
                    file_size=1000,
                    width=400,
                    height=267,
                ),
                MediaVariant(
                    variant_name="small",
                    storage_key="media/variants/hero-small.webp",
                    mime_type="image/webp",
                    file_size=2000,
                    width=800,
                    height=533,
                ),
            ]
        )

        session.add(asset)
        session.commit()

        stored = session.scalar(
            select(MediaAsset).where(MediaAsset.filename == "hero.jpg")
        )

        assert stored is not None
        assert len(stored.variants) == 2
        assert stored.variants[0].variant_name == "thumbnail"
        assert stored.variants[1].variant_name == "small"


def test_deleting_asset_deletes_variants() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        asset = MediaAsset(
            filename="delete-me.png",
            original_filename="Delete Me.png",
            storage_key="media/originals/delete-me.png",
            mime_type="image/png",
            file_type="image",
            file_size=1000,
            width=1000,
            height=600,
        )

        asset.variants.append(
            MediaVariant(
                variant_name="thumbnail",
                storage_key=("media/variants/delete-me-thumbnail.webp"),
                mime_type="image/webp",
                file_size=500,
                width=400,
                height=240,
            )
        )

        session.add(asset)
        session.commit()

        asset_id = asset.id

        session.delete(asset)
        session.commit()

        assert session.get(MediaAsset, asset_id) is None
        assert session.scalar(select(MediaVariant)) is None


def test_document_asset_has_no_dimensions() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        asset = MediaAsset(
            filename="resume.pdf",
            original_filename="Nurlan Rahimli Resume.pdf",
            storage_key="media/documents/resume.pdf",
            mime_type="application/pdf",
            file_type="document",
            file_size=4096,
            width=None,
            height=None,
        )

        session.add(asset)
        session.commit()

        stored = session.scalar(
            select(MediaAsset).where(MediaAsset.file_type == "document")
        )

        assert stored is not None
        assert stored.mime_type == "application/pdf"
        assert stored.width is None
        assert stored.height is None
        assert stored.variants == []
