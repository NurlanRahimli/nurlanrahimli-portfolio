from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.about import AboutContent, AboutSocialLink, AboutSoftwareField
from app.models.media import MediaAsset
from app.schemas.about import AboutContentUpdate
from app.services.rich_text import sanitize_rich_text


class AboutMediaError(Exception):
    pass


def about_load_options():
    return (
        selectinload(AboutContent.profile_media_asset).selectinload(
            MediaAsset.variants
        ),
        selectinload(AboutContent.resume_media_asset).selectinload(
            MediaAsset.variants
        ),
        selectinload(AboutContent.software_fields),
        selectinload(AboutContent.social_links),
    )


def get_about_content(db: Session) -> AboutContent | None:
    statement = (
        select(AboutContent)
        .options(*about_load_options())
        .where(AboutContent.id == 1)
    )
    return db.scalar(statement)


def _get_profile_asset(
    db: Session,
    asset_id: int | None,
) -> MediaAsset | None:
    if asset_id is None:
        return None

    asset = db.get(MediaAsset, asset_id)

    if asset is None:
        raise AboutMediaError("The selected profile image does not exist.")

    if asset.file_type != "image":
        raise AboutMediaError("The About profile media must be an image.")

    return asset


def _get_resume_asset(
    db: Session,
    asset_id: int | None,
) -> MediaAsset | None:
    if asset_id is None:
        return None

    asset = db.get(MediaAsset, asset_id)

    if asset is None:
        raise AboutMediaError("The selected resume document does not exist.")

    if asset.file_type != "document":
        raise AboutMediaError("The About resume media must be a PDF document.")

    if asset.mime_type != "application/pdf":
        raise AboutMediaError("The About resume media must be a PDF document.")

    return asset


def update_about_content(
    db: Session,
    *,
    payload: AboutContentUpdate,
) -> AboutContent:
    _get_profile_asset(db, payload.profile_media_asset_id)
    _get_resume_asset(db, payload.resume_media_asset_id)

    about = get_about_content(db)

    if about is None:
        about = AboutContent(
            id=1,
            full_name=payload.full_name,
        )
        db.add(about)
        db.flush()

    about.full_name = payload.full_name
    about.profile_media_asset_id = payload.profile_media_asset_id
    about.resume_media_asset_id = payload.resume_media_asset_id
    about.about_html = sanitize_rich_text(payload.about_html)
    about.experience_years = payload.experience_years
    about.location = payload.location
    about.is_available = payload.is_available
    about.availability_modes = list(payload.availability_modes)

    about.software_fields.clear()
    db.flush()

    for display_order, item in enumerate(payload.software_fields):
        about.software_fields.append(
            AboutSoftwareField(
                name=item.name,
                display_order=display_order,
            )
        )

    about.social_links.clear()
    db.flush()

    for display_order, item in enumerate(payload.social_links):
        about.social_links.append(
            AboutSocialLink(
                platform=item.platform,
                url=str(item.url),
                display_order=display_order,
            )
        )

    db.add(about)
    db.commit()

    return get_about_content(db) or about
