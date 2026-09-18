from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import MediaAsset, Testimonial as TestimonialModel
from app.services.media_library import (
    get_media_asset_usages,
)


def test_testimonial_profile_blocks_media_deletion() -> None:
    engine = create_engine("sqlite://")

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        asset = MediaAsset(
            filename="profile.webp",
            original_filename="profile.webp",
            storage_key="media/images/test/profile.webp",
            mime_type="image/webp",
            file_type="image",
            file_size=100,
            width=400,
            height=400,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        testimonial = TestimonialModel(
            person_name="Jane Doe",
            testimonial_text="Excellent work.",
            profile_media_asset_id=asset.id,
            display_order=0,
        )
        db.add(testimonial)
        db.commit()

        usages = get_media_asset_usages(
            db,
            asset_id=asset.id,
        )

        assert "a testimonial profile image" in usages

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
