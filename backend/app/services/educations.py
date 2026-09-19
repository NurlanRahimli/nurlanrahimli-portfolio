from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import MediaAsset
from app.models.education import Education
from app.schemas.education import EducationWrite


class EducationConflictError(ValueError):
    pass


class EducationMediaError(ValueError):
    pass


def education_load_options():
    return (
        selectinload(Education.certification_media_asset).selectinload(
            MediaAsset.variants
        ),
    )


def get_education(
    db: Session,
    education_id: int,
) -> Education | None:
    statement = (
        select(Education)
        .where(Education.id == education_id)
        .options(*education_load_options())
    )
    return db.scalar(statement)


def list_educations(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Education], int]:
    filters = []

    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Education.title.ilike(term),
                Education.location.ilike(term),
                Education.description.ilike(term),
            )
        )

    if is_active is not None:
        filters.append(Education.is_active == is_active)

    count_statement = select(func.count(Education.id))
    statement: Select[tuple[Education]] = select(Education)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement.options(*education_load_options())
        .order_by(
            Education.display_order.asc(),
            Education.start_date.desc(),
            Education.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total


def _get_certification_asset(
    db: Session,
    media_asset_id: int | None,
) -> MediaAsset | None:
    if media_asset_id is None:
        return None

    asset = db.get(MediaAsset, media_asset_id)

    if asset is None:
        raise EducationMediaError("The selected certification document does not exist.")

    if asset.file_type != "document":
        raise EducationMediaError(
            "Education certifications must use document media assets."
        )

    if asset.mime_type != "application/pdf":
        raise EducationMediaError("Education certifications must be PDF documents.")

    return asset


def _apply_education_fields(
    education: Education,
    payload: EducationWrite,
    certification_asset: MediaAsset | None,
) -> None:
    education.title = payload.title
    education.location = payload.location
    education.start_date = payload.start_date
    education.end_date = payload.end_date
    education.is_current = payload.is_current
    education.description = payload.description
    education.certification_media_asset = certification_asset
    education.is_active = payload.is_active


def create_education(
    db: Session,
    *,
    payload: EducationWrite,
) -> Education:
    certification_asset = _get_certification_asset(
        db,
        payload.certification_media_asset_id,
    )

    max_order = db.scalar(select(func.max(Education.display_order)))
    display_order = (max_order if max_order is not None else -1) + 1

    education = Education(
        title=payload.title,
        location=payload.location,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        description=payload.description,
        certification_media_asset=certification_asset,
        is_active=payload.is_active,
        display_order=display_order,
    )

    db.add(education)
    db.commit()

    return get_education(db, education.id) or education


def update_education(
    db: Session,
    *,
    education: Education,
    payload: EducationWrite,
) -> Education:
    certification_asset = _get_certification_asset(
        db,
        payload.certification_media_asset_id,
    )

    _apply_education_fields(
        education,
        payload,
        certification_asset,
    )

    db.commit()

    return get_education(db, education.id) or education


def delete_education(
    db: Session,
    *,
    education: Education,
) -> None:
    db.delete(education)
    db.commit()


def reorder_educations(
    db: Session,
    *,
    ordered_items: Sequence[tuple[int, int]],
) -> None:
    ids = [education_id for education_id, _ in ordered_items]

    if len(ids) != len(set(ids)):
        raise EducationConflictError(
            "Each education entry can only appear once in a reorder request."
        )

    educations = db.scalars(select(Education).where(Education.id.in_(ids))).all()

    by_id = {education.id: education for education in educations}

    missing = sorted(set(ids) - set(by_id))

    if missing:
        raise EducationConflictError(
            "Education entry not found: "
            + ", ".join(str(education_id) for education_id in missing)
        )

    for education_id, display_order in ordered_items:
        by_id[education_id].display_order = display_order

    db.commit()


def list_active_educations(
    db: Session,
) -> Sequence[Education]:
    statement = (
        select(Education)
        .where(Education.is_active.is_(True))
        .options(*education_load_options())
        .order_by(
            Education.display_order.asc(),
            Education.start_date.desc(),
            Education.id.asc(),
        )
    )

    return db.scalars(statement).all()
