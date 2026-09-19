from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.projects import media_urls
from app.db.deps import get_db
from app.models import Skill
from app.schemas.skill import PublicSkillList, PublicSkillRead
from app.services.skills import list_active_skills


router = APIRouter(
    prefix="/public/skills",
    tags=["public-skills"],
)


def serialize_public_skill(skill: Skill) -> PublicSkillRead:
    image_url, thumbnail_url = media_urls(skill.media_asset)

    return PublicSkillRead(
        name=skill.name,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
    )


@router.get("", response_model=PublicSkillList)
def get_public_skills(
    db: Annotated[Session, Depends(get_db)],
) -> PublicSkillList:
    skills = list(list_active_skills(db))

    return PublicSkillList(
        items=[serialize_public_skill(skill) for skill in skills],
        total=len(skills),
    )
