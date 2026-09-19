from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models import Service
from app.schemas.service import ServiceWrite


class ServiceConflictError(ValueError):
    pass


def get_service(
    db: Session,
    service_id: int,
) -> Service | None:
    return db.get(Service, service_id)


def list_services(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Service], int]:
    filters = []

    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Service.title.ilike(term),
                Service.description.ilike(term),
            )
        )

    if is_active is not None:
        filters.append(Service.is_active == is_active)

    count_statement = select(func.count(Service.id))
    statement: Select[tuple[Service]] = select(Service)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement.order_by(
            Service.display_order.asc(),
            Service.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total


def _apply_service_fields(
    service: Service,
    payload: ServiceWrite,
) -> None:
    service.icon = payload.icon
    service.title = payload.title
    service.description = payload.description
    service.is_active = payload.is_active


def create_service(
    db: Session,
    *,
    payload: ServiceWrite,
) -> Service:
    max_order = db.scalar(select(func.max(Service.display_order)))
    display_order = (max_order if max_order is not None else -1) + 1

    service = Service(
        icon=payload.icon,
        title=payload.title,
        description=payload.description,
        is_active=payload.is_active,
        display_order=display_order,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


def update_service(
    db: Session,
    *,
    service: Service,
    payload: ServiceWrite,
) -> Service:
    _apply_service_fields(service, payload)

    db.commit()
    db.refresh(service)

    return service


def delete_service(
    db: Session,
    *,
    service: Service,
) -> None:
    db.delete(service)
    db.commit()


def reorder_services(
    db: Session,
    *,
    ordered_items: Sequence[tuple[int, int]],
) -> None:
    ids = [service_id for service_id, _ in ordered_items]

    if len(ids) != len(set(ids)):
        raise ServiceConflictError(
            "Each service can only appear once in a reorder request."
        )

    services = db.scalars(select(Service).where(Service.id.in_(ids))).all()

    by_id = {service.id: service for service in services}
    missing = sorted(set(ids) - set(by_id))

    if missing:
        raise ServiceConflictError(
            "Service not found: " + ", ".join(str(service_id) for service_id in missing)
        )

    for service_id, display_order in ordered_items:
        by_id[service_id].display_order = display_order

    db.commit()


def list_active_services(
    db: Session,
) -> Sequence[Service]:
    statement = (
        select(Service)
        .where(Service.is_active.is_(True))
        .order_by(
            Service.display_order.asc(),
            Service.id.asc(),
        )
    )

    return db.scalars(statement).all()
