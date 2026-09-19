from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.deps import get_db
from app.models import AdminUser
from app.models.experience import Experience
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceHighlightRead,
    ExperienceList,
    ExperienceRead,
    ExperienceReorder,
    ExperienceUpdate,
)
from app.services.experiences import (
    ExperienceConflictError,
    create_experience,
    delete_experience,
    get_experience,
    list_experiences,
    reorder_experiences,
    update_experience,
)


router = APIRouter(
    prefix="/experiences",
    tags=["experiences"],
)


def serialize_experience(
    experience: Experience,
) -> ExperienceRead:
    return ExperienceRead(
        id=experience.id,
        job_title=experience.job_title,
        company=experience.company,
        location=experience.location,
        start_date=experience.start_date,
        end_date=experience.end_date,
        is_current=experience.is_current,
        is_active=experience.is_active,
        display_order=experience.display_order,
        highlights=[
            ExperienceHighlightRead(
                id=highlight.id,
                text=highlight.text,
                display_order=highlight.display_order,
            )
            for highlight in experience.highlights
        ],
        created_at=experience.created_at,
        updated_at=experience.updated_at,
    )


@router.get("", response_model=ExperienceList)
def get_experiences(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ExperienceList:
    del current_admin

    items, total = list_experiences(
        db,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return ExperienceList(
        items=[serialize_experience(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{experience_id}", response_model=ExperienceRead)
def get_experience_detail(
    experience_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> ExperienceRead:
    del current_admin

    experience = get_experience(db, experience_id)

    if experience is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found.",
        )

    return serialize_experience(experience)


@router.post(
    "",
    response_model=ExperienceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_experience_endpoint(
    payload: ExperienceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> ExperienceRead:
    del current_admin

    return serialize_experience(
        create_experience(
            db,
            payload=payload,
        )
    )


@router.put("/{experience_id}", response_model=ExperienceRead)
def update_experience_endpoint(
    experience_id: int,
    payload: ExperienceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> ExperienceRead:
    del current_admin

    experience = get_experience(db, experience_id)

    if experience is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found.",
        )

    return serialize_experience(
        update_experience(
            db,
            experience=experience,
            payload=payload,
        )
    )


@router.delete(
    "/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_experience(
    experience_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    experience = get_experience(db, experience_id)

    if experience is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found.",
        )

    delete_experience(
        db,
        experience=experience,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reorder_experiences_endpoint(
    payload: ExperienceReorder,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    try:
        reorder_experiences(
            db,
            ordered_items=[
                (item.id, item.display_order)
                for item in payload.items
            ],
        )
    except ExperienceConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
