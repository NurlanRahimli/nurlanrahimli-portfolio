from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.v1.projects import media_urls
from app.db.deps import get_db
from app.models import AdminUser, Skill
from app.schemas.skill import (
    SkillCreate,
    SkillList,
    SkillRead,
    SkillReorder,
    SkillUpdate,
)
from app.services.skills import (
    SkillConflictError,
    SkillMediaError,
    create_skill,
    delete_skill,
    get_skill,
    list_skills,
    reorder_skills,
    update_skill,
)


router = APIRouter(
    prefix="/skills",
    tags=["skills"],
)


def serialize_skill(skill: Skill) -> SkillRead:
    image_url, thumbnail_url = media_urls(skill.media_asset)

    return SkillRead(
        id=skill.id,
        name=skill.name,
        media_asset_id=skill.media_asset_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        is_active=skill.is_active,
        display_order=skill.display_order,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


@router.get("", response_model=SkillList)
def get_skills(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SkillList:
    del current_admin

    items, total = list_skills(
        db,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return SkillList(
        items=[serialize_skill(skill) for skill in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{skill_id}", response_model=SkillRead)
def get_skill_detail(
    skill_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> SkillRead:
    del current_admin

    skill = get_skill(db, skill_id)

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    return serialize_skill(skill)


@router.post(
    "",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_endpoint(
    payload: SkillCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> SkillRead:
    del current_admin

    try:
        skill = create_skill(
            db,
            payload=payload,
        )
    except SkillMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_skill(skill)


@router.put("/{skill_id}", response_model=SkillRead)
def update_skill_endpoint(
    skill_id: int,
    payload: SkillUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> SkillRead:
    del current_admin

    skill = get_skill(db, skill_id)

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    try:
        skill = update_skill(
            db,
            skill=skill,
            payload=payload,
        )
    except SkillMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_skill(skill)


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_skill(
    skill_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    skill = get_skill(db, skill_id)

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    delete_skill(
        db,
        skill=skill,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reorder_skills_endpoint(
    payload: SkillReorder,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    try:
        reorder_skills(
            db,
            ordered_items=[
                (item.id, item.display_order)
                for item in payload.items
            ],
        )
    except SkillConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
