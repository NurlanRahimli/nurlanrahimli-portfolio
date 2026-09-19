from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.experience import (
    PublicExperienceHighlightRead,
    PublicExperienceList,
    PublicExperienceRead,
)
from app.services.experiences import list_active_experiences


router = APIRouter(
    prefix="/public/experiences",
    tags=["public-experiences"],
)


@router.get("", response_model=PublicExperienceList)
def get_public_experiences(
    db: Annotated[Session, Depends(get_db)],
) -> PublicExperienceList:
    experiences = list(list_active_experiences(db))

    return PublicExperienceList(
        items=[
            PublicExperienceRead(
                job_title=experience.job_title,
                company=experience.company,
                location=experience.location,
                start_date=experience.start_date,
                end_date=experience.end_date,
                is_current=experience.is_current,
                highlights=[
                    PublicExperienceHighlightRead(
                        text=highlight.text,
                    )
                    for highlight in experience.highlights
                ],
            )
            for experience in experiences
        ],
        total=len(experiences),
    )
