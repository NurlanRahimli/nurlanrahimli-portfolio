from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.experience import Experience, ExperienceHighlight
from app.schemas.experience import ExperienceWrite


class ExperienceConflictError(ValueError):
    pass


def experience_load_options():
    return (selectinload(Experience.highlights),)


def get_experience(
    db: Session,
    experience_id: int,
) -> Experience | None:
    statement = (
        select(Experience)
        .where(Experience.id == experience_id)
        .options(*experience_load_options())
    )
    return db.scalar(statement)


def list_experiences(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Experience], int]:
    filters = []

    if search:
        term = f"%{search.strip()}%"
        highlight_match = (
            select(ExperienceHighlight.id)
            .where(
                ExperienceHighlight.experience_id == Experience.id,
                ExperienceHighlight.text.ilike(term),
            )
            .exists()
        )

        filters.append(
            or_(
                Experience.job_title.ilike(term),
                Experience.company.ilike(term),
                Experience.location.ilike(term),
                highlight_match,
            )
        )

    if is_active is not None:
        filters.append(Experience.is_active == is_active)

    count_statement = select(func.count(Experience.id))
    statement: Select[tuple[Experience]] = select(Experience)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement.options(*experience_load_options())
        .order_by(
            Experience.display_order.asc(),
            Experience.start_date.desc(),
            Experience.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total


def _replace_highlights(
    experience: Experience,
    payload: ExperienceWrite,
) -> None:
    experience.highlights.clear()

    for index, item in enumerate(payload.highlights):
        experience.highlights.append(
            ExperienceHighlight(
                text=item.text,
                display_order=index,
            )
        )


def _apply_experience_fields(
    experience: Experience,
    payload: ExperienceWrite,
) -> None:
    experience.job_title = payload.job_title
    experience.company = payload.company
    experience.location = payload.location
    experience.start_date = payload.start_date
    experience.end_date = payload.end_date
    experience.is_current = payload.is_current
    experience.is_active = payload.is_active


def create_experience(
    db: Session,
    *,
    payload: ExperienceWrite,
) -> Experience:
    max_order = db.scalar(select(func.max(Experience.display_order)))
    display_order = (max_order if max_order is not None else -1) + 1

    experience = Experience(
        job_title=payload.job_title,
        company=payload.company,
        location=payload.location,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        is_active=payload.is_active,
        display_order=display_order,
    )

    _replace_highlights(experience, payload)

    db.add(experience)
    db.commit()

    return get_experience(db, experience.id) or experience


def update_experience(
    db: Session,
    *,
    experience: Experience,
    payload: ExperienceWrite,
) -> Experience:
    _apply_experience_fields(experience, payload)
    _replace_highlights(experience, payload)

    db.commit()

    return get_experience(db, experience.id) or experience


def delete_experience(
    db: Session,
    *,
    experience: Experience,
) -> None:
    db.delete(experience)
    db.commit()


def reorder_experiences(
    db: Session,
    *,
    ordered_items: Sequence[tuple[int, int]],
) -> None:
    ids = [experience_id for experience_id, _ in ordered_items]

    if len(ids) != len(set(ids)):
        raise ExperienceConflictError(
            "Each experience can only appear once in a reorder request."
        )

    experiences = db.scalars(
        select(Experience).where(Experience.id.in_(ids))
    ).all()

    by_id = {
        experience.id: experience
        for experience in experiences
    }

    missing = sorted(set(ids) - set(by_id))

    if missing:
        raise ExperienceConflictError(
            "Experience not found: "
            + ", ".join(str(experience_id) for experience_id in missing)
        )

    for experience_id, display_order in ordered_items:
        by_id[experience_id].display_order = display_order

    db.commit()


def list_active_experiences(
    db: Session,
) -> Sequence[Experience]:
    statement = (
        select(Experience)
        .where(Experience.is_active.is_(True))
        .options(*experience_load_options())
        .order_by(
            Experience.display_order.asc(),
            Experience.start_date.desc(),
            Experience.id.asc(),
        )
    )

    return db.scalars(statement).all()
