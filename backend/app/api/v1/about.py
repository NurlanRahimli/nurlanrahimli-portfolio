from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.v1.projects import media_urls
from app.db.deps import get_db
from app.models import AdminUser, AboutContent
from app.schemas.about import (
    AboutContentRead,
    AboutContentUpdate,
    AboutSocialLinkRead,
    AboutSoftwareFieldRead,
)
from app.services.about import (
    AboutMediaError,
    get_about_content,
    update_about_content,
)
from app.services.r2_storage import r2_storage


router = APIRouter(
    prefix="/about",
    tags=["about"],
)


def serialize_about(about: AboutContent) -> AboutContentRead:
    profile_image_url, profile_thumbnail_url = media_urls(
        about.profile_media_asset
    )

    resume_url = None
    resume_filename = None

    if about.resume_media_asset is not None:
        resume_url = r2_storage.public_url(
            about.resume_media_asset.storage_key
        )
        resume_filename = about.resume_media_asset.original_filename

    return AboutContentRead(
        id=about.id,
        full_name=about.full_name,
        profile_media_asset_id=about.profile_media_asset_id,
        profile_image_url=profile_image_url,
        profile_thumbnail_url=profile_thumbnail_url,
        resume_media_asset_id=about.resume_media_asset_id,
        resume_url=resume_url,
        resume_filename=resume_filename,
        about_html=about.about_html,
        experience_years=about.experience_years,
        location=about.location,
        is_available=about.is_available,
        availability_modes=about.availability_modes,
        software_fields=[
            AboutSoftwareFieldRead(
                id=item.id,
                name=item.name,
                display_order=item.display_order,
            )
            for item in about.software_fields
        ],
        social_links=[
            AboutSocialLinkRead(
                id=item.id,
                platform=item.platform,
                url=item.url,
                display_order=item.display_order,
            )
            for item in about.social_links
        ],
        created_at=about.created_at,
        updated_at=about.updated_at,
    )


@router.get(
    "",
    response_model=AboutContentRead | None,
)
def get_about(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> AboutContentRead | None:
    del current_admin

    about = get_about_content(db)

    if about is None:
        return None

    return serialize_about(about)


@router.put(
    "",
    response_model=AboutContentRead,
)
def update_about(
    payload: AboutContentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> AboutContentRead:
    del current_admin

    try:
        about = update_about_content(
            db,
            payload=payload,
        )
    except AboutMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_about(about)
