from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import MediaAsset, Testimonial
from app.schemas.testimonial import TestimonialWrite


class TestimonialConflictError(ValueError):
    pass


class TestimonialMediaError(ValueError):
    pass


def testimonial_load_options():
    return (
        selectinload(Testimonial.profile_media_asset).selectinload(MediaAsset.variants),
    )


def get_testimonial(
    db: Session,
    testimonial_id: int,
) -> Testimonial | None:
    statement = (
        select(Testimonial)
        .where(Testimonial.id == testimonial_id)
        .options(*testimonial_load_options())
    )
    return db.scalar(statement)


def list_testimonials(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Testimonial], int]:
    filters = []

    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Testimonial.person_name.ilike(term),
                Testimonial.testimonial_text.ilike(term),
            )
        )

    if is_active is not None:
        filters.append(Testimonial.is_active == is_active)

    count_statement = select(func.count(Testimonial.id))
    statement: Select[tuple[Testimonial]] = select(Testimonial)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement.options(*testimonial_load_options())
        .order_by(
            Testimonial.display_order.asc(),
            Testimonial.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total


def _get_profile_asset(
    db: Session,
    media_asset_id: int | None,
) -> MediaAsset | None:
    if media_asset_id is None:
        return None

    asset = db.get(MediaAsset, media_asset_id)

    if asset is None:
        raise TestimonialMediaError(f"Media asset not found: {media_asset_id}")

    if asset.file_type != "image":
        raise TestimonialMediaError("Testimonials can only use image media assets.")

    return asset


def _apply_testimonial_fields(
    testimonial: Testimonial,
    payload: TestimonialWrite,
    profile_asset: MediaAsset | None,
) -> None:
    testimonial.person_name = payload.person_name
    testimonial.testimonial_text = payload.testimonial_text
    testimonial.profile_media_asset = profile_asset
    testimonial.linkedin_url = (
        str(payload.linkedin_url) if payload.linkedin_url is not None else None
    )
    testimonial.is_active = payload.is_active


def create_testimonial(
    db: Session,
    *,
    payload: TestimonialWrite,
) -> Testimonial:
    profile_asset = _get_profile_asset(
        db,
        payload.profile_media_asset_id,
    )

    max_order = db.scalar(select(func.max(Testimonial.display_order)))
    display_order = (max_order if max_order is not None else -1) + 1

    testimonial = Testimonial(
        person_name=payload.person_name,
        testimonial_text=payload.testimonial_text,
        display_order=display_order,
    )

    _apply_testimonial_fields(
        testimonial,
        payload,
        profile_asset,
    )

    db.add(testimonial)
    db.commit()

    return get_testimonial(
        db,
        testimonial.id,
    )  # type: ignore[return-value]


def update_testimonial(
    db: Session,
    *,
    testimonial: Testimonial,
    payload: TestimonialWrite,
) -> Testimonial:
    profile_asset = _get_profile_asset(
        db,
        payload.profile_media_asset_id,
    )

    _apply_testimonial_fields(
        testimonial,
        payload,
        profile_asset,
    )

    db.commit()

    return get_testimonial(
        db,
        testimonial.id,
    )  # type: ignore[return-value]


def delete_testimonial(
    db: Session,
    *,
    testimonial: Testimonial,
) -> None:
    db.delete(testimonial)
    db.commit()


def reorder_testimonials(
    db: Session,
    *,
    ordered_items: Sequence[tuple[int, int]],
) -> None:
    ids = [testimonial_id for testimonial_id, _ in ordered_items]

    if len(ids) != len(set(ids)):
        raise TestimonialConflictError(
            "Each testimonial can only appear once in a reorder request."
        )

    testimonials = db.scalars(select(Testimonial).where(Testimonial.id.in_(ids))).all()

    by_id = {testimonial.id: testimonial for testimonial in testimonials}

    missing = sorted(set(ids) - set(by_id))

    if missing:
        raise TestimonialConflictError(
            "Testimonial not found: "
            + ", ".join(str(testimonial_id) for testimonial_id in missing)
        )

    for testimonial_id, display_order in ordered_items:
        by_id[testimonial_id].display_order = display_order

    db.commit()


def list_active_testimonials(
    db: Session,
    *,
    limit: int = 3,
) -> Sequence[Testimonial]:
    statement = (
        select(Testimonial)
        .where(Testimonial.is_active.is_(True))
        .options(*testimonial_load_options())
        .order_by(
            Testimonial.display_order.asc(),
            Testimonial.id.asc(),
        )
        .limit(limit)
    )

    return db.scalars(statement).all()
