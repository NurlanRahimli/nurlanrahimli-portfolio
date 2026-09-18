from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.projects import media_urls
from app.db.deps import get_db
from app.models import AdminUser, Testimonial
from app.schemas.testimonial import (
    TestimonialCreate,
    TestimonialList,
    TestimonialRead,
    TestimonialReorder,
    TestimonialUpdate,
)
from app.api.deps import get_current_admin
from app.services.testimonials import (
    TestimonialConflictError,
    TestimonialMediaError,
    create_testimonial,
    delete_testimonial,
    get_testimonial,
    list_testimonials,
    reorder_testimonials,
    update_testimonial,
)

router = APIRouter(
    prefix="/testimonials",
    tags=["testimonials"],
)


def serialize_testimonial(
    testimonial: Testimonial,
) -> TestimonialRead:
    profile_image_url, profile_thumbnail_url = media_urls(
        testimonial.profile_media_asset
    )

    return TestimonialRead(
        id=testimonial.id,
        person_name=testimonial.person_name,
        testimonial_text=testimonial.testimonial_text,
        profile_media_asset_id=testimonial.profile_media_asset_id,
        profile_image_url=profile_image_url,
        profile_thumbnail_url=profile_thumbnail_url,
        linkedin_url=testimonial.linkedin_url,
        is_active=testimonial.is_active,
        display_order=testimonial.display_order,
        created_at=testimonial.created_at,
        updated_at=testimonial.updated_at,
    )


@router.get(
    "",
    response_model=TestimonialList,
)
def get_testimonials(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
    search: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TestimonialList:
    del current_admin

    items, total = list_testimonials(
        db,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return TestimonialList(
        items=[serialize_testimonial(testimonial) for testimonial in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{testimonial_id}",
    response_model=TestimonialRead,
)
def get_testimonial_detail(
    testimonial_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> TestimonialRead:
    del current_admin

    testimonial = get_testimonial(
        db,
        testimonial_id,
    )

    if testimonial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found.",
        )

    return serialize_testimonial(testimonial)


@router.post(
    "",
    response_model=TestimonialRead,
    status_code=status.HTTP_201_CREATED,
)
def create_testimonial_endpoint(
    payload: TestimonialCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> TestimonialRead:
    del current_admin

    try:
        testimonial = create_testimonial(
            db,
            payload=payload,
        )
    except TestimonialMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_testimonial(testimonial)


@router.put(
    "/{testimonial_id}",
    response_model=TestimonialRead,
)
def update_testimonial_endpoint(
    testimonial_id: int,
    payload: TestimonialUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> TestimonialRead:
    del current_admin

    testimonial = get_testimonial(
        db,
        testimonial_id,
    )

    if testimonial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found.",
        )

    try:
        testimonial = update_testimonial(
            db,
            testimonial=testimonial,
            payload=payload,
        )
    except TestimonialMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return serialize_testimonial(testimonial)


@router.delete(
    "/{testimonial_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_testimonial(
    testimonial_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    testimonial = get_testimonial(
        db,
        testimonial_id,
    )

    if testimonial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found.",
        )

    delete_testimonial(
        db,
        testimonial=testimonial,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reorder_testimonials_endpoint(
    payload: TestimonialReorder,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    try:
        reorder_testimonials(
            db,
            ordered_items=[(item.id, item.display_order) for item in payload.items],
        )
    except TestimonialConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
