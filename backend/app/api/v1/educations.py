from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.deps import get_db
from app.models import AdminUser
from app.models.education import Education
from app.schemas.education import (
    EducationCreate,
    EducationList,
    EducationRead,
    EducationReorder,
    EducationUpdate,
)
from app.services.r2_storage import r2_storage

from app.services.educations import (
    EducationConflictError,
    EducationMediaError,
    create_education,
    delete_education,
    get_education,
    list_educations,
    reorder_educations,
    update_education,
)


router = APIRouter(
    prefix="/educations",
    tags=["educations"],
)


def get_certification_url(education: Education) -> str | None:
    asset = education.certification_media_asset

    if asset is None:
        return None

    return r2_storage.public_url(asset.storage_key)


def serialize_education(
    education: Education,
) -> EducationRead:
    asset = education.certification_media_asset

    return EducationRead(
        id=education.id,
        title=education.title,
        location=education.location,
        start_date=education.start_date,
        end_date=education.end_date,
        is_current=education.is_current,
        description=education.description,
        certification_media_asset_id=education.certification_media_asset_id,
        certification_filename=(asset.original_filename if asset is not None else None),
        certification_url=get_certification_url(education),
        is_active=education.is_active,
        display_order=education.display_order,
        created_at=education.created_at,
        updated_at=education.updated_at,
    )


@router.get("", response_model=EducationList)
def get_educations(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EducationList:
    del current_admin

    items, total = list_educations(
        db,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return EducationList(
        items=[serialize_education(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{education_id}", response_model=EducationRead)
def get_education_detail(
    education_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> EducationRead:
    del current_admin

    education = get_education(db, education_id)

    if education is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found.",
        )

    return serialize_education(education)


@router.post(
    "",
    response_model=EducationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_education_endpoint(
    payload: EducationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> EducationRead:
    del current_admin

    try:
        education = create_education(
            db,
            payload=payload,
        )
    except EducationMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_education(education)


@router.put("/{education_id}", response_model=EducationRead)
def update_education_endpoint(
    education_id: int,
    payload: EducationUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> EducationRead:
    del current_admin

    education = get_education(db, education_id)

    if education is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found.",
        )

    try:
        education = update_education(
            db,
            education=education,
            payload=payload,
        )
    except EducationMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_education(education)


@router.delete(
    "/{education_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_education(
    education_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    education = get_education(db, education_id)

    if education is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found.",
        )

    delete_education(
        db,
        education=education,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reorder_educations_endpoint(
    payload: EducationReorder,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    try:
        reorder_educations(
            db,
            ordered_items=[(item.id, item.display_order) for item in payload.items],
        )
    except EducationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
