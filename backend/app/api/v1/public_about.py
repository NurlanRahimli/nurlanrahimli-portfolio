from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.about import serialize_about
from app.db.deps import get_db
from app.schemas.about import (
    PublicAboutContentRead,
    PublicAboutSocialLink,
    PublicAboutSoftwareField,
)
from app.services.about import get_about_content


router = APIRouter(
    prefix="/public/about",
    tags=["public-about"],
)


@router.get(
    "",
    response_model=PublicAboutContentRead | None,
)
def get_public_about(
    db: Annotated[Session, Depends(get_db)],
) -> PublicAboutContentRead | None:
    about = get_about_content(db)

    if about is None:
        return None

    serialized = serialize_about(about)

    return PublicAboutContentRead(
        full_name=serialized.full_name,
        profile_image_url=serialized.profile_image_url,
        profile_thumbnail_url=serialized.profile_thumbnail_url,
        resume_url=serialized.resume_url,
        about_html=serialized.about_html,
        experience_years=serialized.experience_years,
        location=serialized.location,
        is_available=serialized.is_available,
        availability_modes=serialized.availability_modes,
        software_fields=[
            PublicAboutSoftwareField(name=item.name)
            for item in serialized.software_fields
        ],
        social_links=[
            PublicAboutSocialLink(
                platform=item.platform,
                url=item.url,
            )
            for item in serialized.social_links
        ],
    )
