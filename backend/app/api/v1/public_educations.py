from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.education import Education
from app.schemas.education import (
    PublicEducationList,
    PublicEducationRead,
)
from app.services.educations import list_active_educations
from app.services.r2_storage import r2_storage


router = APIRouter(
    prefix="/public/educations",
    tags=["public-educations"],
)


def serialize_public_education(
    education: Education,
) -> PublicEducationRead:
    asset = education.certification_media_asset

    return PublicEducationRead(
        title=education.title,
        location=education.location,
        start_date=education.start_date,
        end_date=education.end_date,
        is_current=education.is_current,
        description=education.description,
        certification_filename=(asset.original_filename if asset is not None else None),
        certification_url=(
            r2_storage.public_url(asset.storage_key) if asset is not None else None
        ),
    )


@router.get("", response_model=PublicEducationList)
def get_public_educations(
    db: Annotated[Session, Depends(get_db)],
) -> PublicEducationList:
    items = list_active_educations(db)

    return PublicEducationList(
        items=[serialize_public_education(item) for item in items],
        total=len(items),
    )
