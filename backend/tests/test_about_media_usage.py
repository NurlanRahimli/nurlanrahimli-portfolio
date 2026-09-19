from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import AboutContent, MediaAsset
from app.services.media_library import get_media_asset_usages


def create_asset(
    db: Session,
    *,
    filename: str,
    file_type: str,
    mime_type: str,
) -> MediaAsset:
    asset = MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/{file_type}s/test/{filename}",
        mime_type=mime_type,
        file_type=file_type,
        file_size=100,
        width=400 if file_type == "image" else None,
        height=400 if file_type == "image" else None,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def test_about_media_references_block_media_deletion() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        profile = create_asset(
            db,
            filename="profile.webp",
            file_type="image",
            mime_type="image/webp",
        )

        resume = create_asset(
            db,
            filename="resume.pdf",
            file_type="document",
            mime_type="application/pdf",
        )

        about = AboutContent(
            full_name="Nurlan Rahimli",
            profile_media_asset_id=profile.id,
            resume_media_asset_id=resume.id,
            about_html="<p>About me</p>",
            experience_years=3,
            location="Sacramento, California",
            is_available=True,
            availability_modes=["remote"],
        )

        db.add(about)
        db.commit()

        profile_usages = get_media_asset_usages(
            db,
            asset_id=profile.id,
        )

        resume_usages = get_media_asset_usages(
            db,
            asset_id=resume.id,
        )

        assert "the About profile image" in profile_usages
        assert "the About resume document" in resume_usages

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
