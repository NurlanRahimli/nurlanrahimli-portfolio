from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import MediaAsset, Skill
from app.services.media_library import get_media_asset_usages


def test_skill_logo_is_reported_as_media_usage() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            asset = MediaAsset(
                filename="python.png",
                original_filename="python.png",
                storage_key="media/images/python.png",
                mime_type="image/png",
                file_type="image",
                file_size=1024,
                width=512,
                height=512,
            )
            db.add(asset)
            db.flush()

            skill = Skill(
                name="Python",
                media_asset_id=asset.id,
                is_active=True,
                display_order=0,
            )
            db.add(skill)
            db.commit()

            usages = get_media_asset_usages(
                db,
                asset_id=asset.id,
            )

            assert "a skill logo" in usages
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
