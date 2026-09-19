from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import MediaAsset, Skill
from app.schemas.skill import SkillWrite


class SkillConflictError(ValueError):
    pass


class SkillMediaError(ValueError):
    pass


def skill_load_options():
    return (
        selectinload(Skill.media_asset).selectinload(MediaAsset.variants),
    )


def get_skill(
    db: Session,
    skill_id: int,
) -> Skill | None:
    statement = (
        select(Skill)
        .where(Skill.id == skill_id)
        .options(*skill_load_options())
    )
    return db.scalar(statement)


def list_skills(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Skill], int]:
    filters = []

    if search:
        filters.append(Skill.name.ilike(f"%{search.strip()}%"))

    if is_active is not None:
        filters.append(Skill.is_active == is_active)

    count_statement = select(func.count(Skill.id))
    statement: Select[tuple[Skill]] = select(Skill)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement.options(*skill_load_options())
        .order_by(
            Skill.display_order.asc(),
            Skill.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total


def _get_skill_asset(
    db: Session,
    media_asset_id: int,
) -> MediaAsset:
    asset = db.get(MediaAsset, media_asset_id)

    if asset is None:
        raise SkillMediaError("The selected skill logo does not exist.")

    if asset.file_type != "image":
        raise SkillMediaError("Skill logos must use image media assets.")

    return asset


def _apply_skill_fields(
    skill: Skill,
    payload: SkillWrite,
    media_asset: MediaAsset,
) -> None:
    skill.name = payload.name
    skill.media_asset = media_asset
    skill.is_active = payload.is_active


def create_skill(
    db: Session,
    *,
    payload: SkillWrite,
) -> Skill:
    media_asset = _get_skill_asset(db, payload.media_asset_id)

    max_order = db.scalar(select(func.max(Skill.display_order)))
    display_order = (max_order if max_order is not None else -1) + 1

    skill = Skill(
        name=payload.name,
        media_asset=media_asset,
        is_active=payload.is_active,
        display_order=display_order,
    )

    db.add(skill)
    db.commit()

    return get_skill(db, skill.id)  # type: ignore[return-value]


def update_skill(
    db: Session,
    *,
    skill: Skill,
    payload: SkillWrite,
) -> Skill:
    media_asset = _get_skill_asset(db, payload.media_asset_id)

    _apply_skill_fields(
        skill,
        payload,
        media_asset,
    )

    db.commit()

    return get_skill(db, skill.id)  # type: ignore[return-value]


def delete_skill(
    db: Session,
    *,
    skill: Skill,
) -> None:
    db.delete(skill)
    db.commit()


def reorder_skills(
    db: Session,
    *,
    ordered_items: Sequence[tuple[int, int]],
) -> None:
    ids = [skill_id for skill_id, _ in ordered_items]

    if len(ids) != len(set(ids)):
        raise SkillConflictError(
            "Each skill can only appear once in a reorder request."
        )

    skills = db.scalars(
        select(Skill).where(Skill.id.in_(ids))
    ).all()

    by_id = {skill.id: skill for skill in skills}
    missing = sorted(set(ids) - set(by_id))

    if missing:
        raise SkillConflictError(
            "Skill not found: "
            + ", ".join(str(skill_id) for skill_id in missing)
        )

    for skill_id, display_order in ordered_items:
        by_id[skill_id].display_order = display_order

    db.commit()


def list_active_skills(
    db: Session,
) -> Sequence[Skill]:
    statement = (
        select(Skill)
        .where(Skill.is_active.is_(True))
        .options(*skill_load_options())
        .order_by(
            Skill.display_order.asc(),
            Skill.id.asc(),
        )
    )

    return db.scalars(statement).all()
