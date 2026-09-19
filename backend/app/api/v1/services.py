from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.deps import get_db
from app.models import AdminUser, Service
from app.schemas.service import (
    ServiceCreate,
    ServiceList,
    ServiceRead,
    ServiceReorder,
    ServiceUpdate,
)
from app.services.services import (
    ServiceConflictError,
    create_service,
    delete_service,
    get_service,
    list_services,
    reorder_services,
    update_service,
)


router = APIRouter(
    prefix="/services",
    tags=["services"],
)


def serialize_service(service: Service) -> ServiceRead:
    return ServiceRead(
        id=service.id,
        icon=service.icon,
        title=service.title,
        description=service.description,
        is_active=service.is_active,
        display_order=service.display_order,
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


@router.get("", response_model=ServiceList)
def get_services(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ServiceList:
    del current_admin

    items, total = list_services(
        db,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return ServiceList(
        items=[serialize_service(service) for service in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{service_id}", response_model=ServiceRead)
def get_service_detail(
    service_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> ServiceRead:
    del current_admin

    service = get_service(db, service_id)

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    return serialize_service(service)


@router.post(
    "",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_service_endpoint(
    payload: ServiceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> ServiceRead:
    del current_admin

    service = create_service(
        db,
        payload=payload,
    )

    return serialize_service(service)


@router.put("/{service_id}", response_model=ServiceRead)
def update_service_endpoint(
    service_id: int,
    payload: ServiceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> ServiceRead:
    del current_admin

    service = get_service(db, service_id)

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    service = update_service(
        db,
        service=service,
        payload=payload,
    )

    return serialize_service(service)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_service(
    service_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    service = get_service(db, service_id)

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    delete_service(
        db,
        service=service,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reorder_services_endpoint(
    payload: ServiceReorder,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> Response:
    del current_admin

    try:
        reorder_services(
            db,
            ordered_items=[(item.id, item.display_order) for item in payload.items],
        )
    except ServiceConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
