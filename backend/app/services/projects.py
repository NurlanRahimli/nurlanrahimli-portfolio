import re
import unicodedata
from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    MediaAsset,
    Project,
    ProjectFeature,
    ProjectImage,
    ProjectTag,
    ProjectTechGroup,
    ProjectTechItem,
)
from app.schemas.project import ProjectWrite


class ProjectConflictError(ValueError):
    pass


class ProjectMediaError(ValueError):
    pass


def project_load_options():
    return (
        selectinload(Project.cover_media_asset).selectinload(MediaAsset.variants),
        selectinload(Project.tags),
        selectinload(Project.images)
        .selectinload(ProjectImage.media_asset)
        .selectinload(MediaAsset.variants),
        selectinload(Project.features),
        selectinload(Project.tech_groups).selectinload(ProjectTechGroup.items),
        selectinload(Project.video),
    )


def get_project(
    db: Session,
    project_id: int,
) -> Project | None:
    statement = (
        select(Project).where(Project.id == project_id).options(*project_load_options())
    )
    return db.scalar(statement)


def get_project_by_slug(
    db: Session,
    slug: str,
) -> Project | None:
    statement = (
        select(Project).where(Project.slug == slug).options(*project_load_options())
    )
    return db.scalar(statement)


def list_projects(
    db: Session,
    *,
    search: str | None = None,
    is_published: bool | None = None,
    is_featured: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Project], int]:
    filters = []

    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Project.title.ilike(term),
                Project.slug.ilike(term),
                Project.project_type.ilike(term),
                Project.short_description.ilike(term),
            )
        )

    if is_published is not None:
        filters.append(Project.is_published == is_published)

    if is_featured is not None:
        filters.append(Project.is_featured == is_featured)

    count_statement = select(func.count(Project.id))
    statement: Select[tuple[Project]] = select(Project)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement.options(*project_load_options())
        .order_by(
            Project.display_order.asc(),
            Project.project_date.desc(),
            Project.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )
    ascii_value = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        ascii_value.lower(),
    ).strip("-")

    return slug or "project"


def _slug_exists(
    db: Session,
    *,
    slug: str,
    project_id: int | None = None,
) -> bool:
    statement = select(Project.id).where(Project.slug == slug)

    if project_id is not None:
        statement = statement.where(Project.id != project_id)

    return db.scalar(statement) is not None


def _validate_slug(
    db: Session,
    *,
    slug: str,
    project_id: int | None = None,
) -> None:
    if _slug_exists(
        db,
        slug=slug,
        project_id=project_id,
    ):
        raise ProjectConflictError("A project with this slug already exists.")


def _generate_unique_slug(
    db: Session,
    *,
    title: str,
) -> str:
    base = _slugify(title)
    candidate = base
    suffix = 2

    while _slug_exists(
        db,
        slug=candidate,
    ):
        candidate = f"{base}-{suffix}"
        suffix += 1

    return candidate


def _get_image_assets(
    db: Session,
    payload: ProjectWrite,
) -> dict[int, MediaAsset]:
    asset_ids = {item.media_asset_id for item in payload.images}

    if payload.cover_media_asset_id is not None:
        asset_ids.add(payload.cover_media_asset_id)

    if not asset_ids:
        return {}

    assets = db.scalars(select(MediaAsset).where(MediaAsset.id.in_(asset_ids))).all()
    by_id = {asset.id: asset for asset in assets}

    missing = sorted(asset_ids - set(by_id))
    if missing:
        raise ProjectMediaError(
            "Media asset not found: " + ", ".join(str(asset_id) for asset_id in missing)
        )

    non_images = sorted(asset.id for asset in assets if asset.file_type != "image")
    if non_images:
        raise ProjectMediaError(
            "Projects can only use image media assets: "
            + ", ".join(str(asset_id) for asset_id in non_images)
        )

    return by_id


def _validate_nested_uniqueness(
    payload: ProjectWrite,
) -> None:
    tag_labels = [item.label.strip().casefold() for item in payload.tags]
    if len(tag_labels) != len(set(tag_labels)):
        raise ProjectConflictError("Project tags must be unique.")

    image_ids = [item.media_asset_id for item in payload.images]
    if len(image_ids) != len(set(image_ids)):
        raise ProjectConflictError("Project images must be unique.")

    group_labels = [group.label.strip().casefold() for group in payload.tech_groups]
    if len(group_labels) != len(set(group_labels)):
        raise ProjectConflictError("Tech stack group labels must be unique.")

    for group in payload.tech_groups:
        names = [item.name.strip().casefold() for item in group.items]
        if len(names) != len(set(names)):
            raise ProjectConflictError(
                f'Technologies in "{group.label}" must be unique.'
            )


def _validate_publish_requirements(
    payload: ProjectWrite,
) -> None:
    if payload.project_date is not None and payload.project_date.day != 1:
        raise ProjectConflictError("Project date must use the first day of the month.")

    image_ids = {image.media_asset_id for image in payload.images}

    if not payload.is_published:
        if (
            payload.cover_media_asset_id is not None
            and payload.cover_media_asset_id not in image_ids
        ):
            raise ProjectConflictError(
                "The cover image must also be included in the project gallery."
            )
        return

    required_text = (
        (
            "project type",
            payload.project_type,
        ),
        (
            "short description",
            payload.short_description,
        ),
        (
            "long description",
            payload.long_description,
        ),
    )

    for label, value in required_text:
        if not value:
            raise ProjectConflictError(f"A published project requires a {label}.")

    if payload.project_date is None:
        raise ProjectConflictError("A published project requires a project date.")

    if not payload.images:
        raise ProjectConflictError(
            "A published project requires at least one gallery image."
        )

    if payload.cover_media_asset_id is None:
        raise ProjectConflictError("A published project requires a cover image.")

    if payload.cover_media_asset_id not in image_ids:
        raise ProjectConflictError(
            "The cover image must also be included in the project gallery."
        )

    if not payload.features:
        raise ProjectConflictError(
            "A published project requires at least one key feature."
        )

    if not payload.tech_groups:
        raise ProjectConflictError(
            "A published project requires at least one tech stack group."
        )

    for group in payload.tech_groups:
        if not group.items:
            raise ProjectConflictError(
                f'Tech stack group "{group.label}" requires at least one technology.'
            )

    if payload.show_github_link and payload.github_url is None:
        raise ProjectConflictError(
            "A GitHub URL is required when the GitHub link is enabled."
        )


def _clear_nested_content(project: Project) -> None:
    project.tags.clear()
    project.images.clear()
    project.features.clear()
    project.tech_groups.clear()


def _replace_nested_content(
    project: Project,
    payload: ProjectWrite,
    assets: dict[int, MediaAsset],
) -> None:
    for index, item in enumerate(payload.tags):
        project.tags.append(
            ProjectTag(
                label=item.label.strip(),
                display_order=index,
            )
        )

    for index, item in enumerate(payload.images):
        project.images.append(
            ProjectImage(
                media_asset=assets[item.media_asset_id],
                label=item.label.strip() if item.label else None,
                display_order=index,
            )
        )

    for index, item in enumerate(payload.features):
        project.features.append(
            ProjectFeature(
                text=item.text.strip(),
                display_order=index,
            )
        )

    for group_index, group in enumerate(payload.tech_groups):
        tech_group = ProjectTechGroup(
            label=group.label.strip(),
            display_order=group_index,
        )

        for item_index, item in enumerate(group.items):
            tech_group.items.append(
                ProjectTechItem(
                    name=item.name.strip(),
                    display_order=item_index,
                )
            )

        project.tech_groups.append(tech_group)


def _apply_project_fields(
    project: Project,
    payload: ProjectWrite,
    assets: dict[int, MediaAsset],
) -> None:
    if payload.slug is not None:
        project.slug = payload.slug

    project.title = payload.title
    project.project_type = payload.project_type
    project.short_description = payload.short_description
    project.long_description = payload.long_description
    project.project_date = payload.project_date

    project.cover_media_asset = (
        assets.get(payload.cover_media_asset_id)
        if payload.cover_media_asset_id is not None
        else None
    )

    project.github_url = (
        str(payload.github_url) if payload.github_url is not None else None
    )
    project.show_github_link = payload.show_github_link
    project.demo_url = str(payload.demo_url) if payload.demo_url is not None else None

    project.is_featured = payload.is_featured
    project.is_published = payload.is_published


def create_project(
    db: Session,
    *,
    payload: ProjectWrite,
) -> Project:
    slug = (
        payload.slug
        if payload.slug is not None
        else _generate_unique_slug(
            db,
            title=payload.title,
        )
    )

    if payload.slug is not None:
        _validate_slug(
            db,
            slug=slug,
        )

    _validate_nested_uniqueness(payload)
    _validate_publish_requirements(payload)

    assets = _get_image_assets(
        db,
        payload,
    )

    max_order = db.scalar(select(func.max(Project.display_order)))

    display_order = (max_order if max_order is not None else -1) + 1

    project = Project(
        slug=slug,
        title=payload.title,
        project_type=payload.project_type,
        short_description=payload.short_description,
        long_description=payload.long_description,
        project_date=payload.project_date,
        display_order=display_order,
    )

    _apply_project_fields(
        project,
        payload,
        assets,
    )
    _replace_nested_content(
        project,
        payload,
        assets,
    )

    db.add(project)
    db.commit()

    return get_project(
        db,
        project.id,
    )  # type: ignore[return-value]


def update_project(
    db: Session,
    *,
    project: Project,
    payload: ProjectWrite,
) -> Project:
    if payload.slug is not None:
        _validate_slug(
            db,
            slug=payload.slug,
            project_id=project.id,
        )

    _validate_nested_uniqueness(payload)
    _validate_publish_requirements(payload)

    assets = _get_image_assets(
        db,
        payload,
    )

    _apply_project_fields(
        project,
        payload,
        assets,
    )
    _clear_nested_content(project)
    db.flush()

    _replace_nested_content(
        project,
        payload,
        assets,
    )

    db.commit()

    return get_project(
        db,
        project.id,
    )  # type: ignore[return-value]


def delete_project(
    db: Session,
    *,
    project: Project,
) -> None:
    db.delete(project)
    db.commit()


def reorder_projects(
    db: Session,
    *,
    ordered_items: Sequence[tuple[int, int]],
) -> None:
    ids = [project_id for project_id, _ in ordered_items]

    if len(ids) != len(set(ids)):
        raise ProjectConflictError(
            "Each project can only appear once in a reorder request."
        )

    projects = db.scalars(select(Project).where(Project.id.in_(ids))).all()
    by_id = {project.id: project for project in projects}

    missing = sorted(set(ids) - set(by_id))
    if missing:
        raise ProjectConflictError(
            "Project not found: " + ", ".join(str(project_id) for project_id in missing)
        )

    for project_id, display_order in ordered_items:
        by_id[project_id].display_order = display_order

    db.commit()


def list_published_projects(
    db: Session,
) -> Sequence[Project]:
    statement = (
        select(Project)
        .where(Project.is_published.is_(True))
        .options(*project_load_options())
        .order_by(
            Project.display_order.asc(),
            Project.project_date.desc(),
            Project.id.asc(),
        )
    )
    return db.scalars(statement).all()


def get_published_project_by_slug(
    db: Session,
    slug: str,
) -> Project | None:
    statement = (
        select(Project)
        .where(
            Project.slug == slug,
            Project.is_published.is_(True),
        )
        .options(*project_load_options())
    )
    return db.scalar(statement)


def get_published_project_neighbors(
    db: Session,
    project: Project,
) -> tuple[Project | None, Project | None]:
    projects = list(list_published_projects(db))

    if len(projects) <= 1:
        return None, None

    current_index = next(
        (index for index, item in enumerate(projects) if item.id == project.id),
        None,
    )

    if current_index is None:
        return None, None

    previous_project = projects[(current_index - 1) % len(projects)]
    next_project = projects[(current_index + 1) % len(projects)]

    return previous_project, next_project


def remove_project_video(
    db: Session,
    *,
    project: Project,
) -> Project:
    if project.video is None:
        raise ProjectConflictError("This project does not have a video.")

    db.delete(project.video)
    db.commit()

    return get_project(db, project.id)  # type: ignore[return-value]


def create_project_video_upload(
    db: Session,
    *,
    project: Project,
    original_filename: str,
    mux_upload_id: str,
) -> Project:
    from app.models import ProjectVideo

    filename = original_filename.strip()

    if project.video is None:
        project.video = ProjectVideo(
            mux_upload_id=mux_upload_id,
            status="uploading",
            original_filename=filename,
        )
        db.commit()
        return get_project(db, project.id)  # type: ignore[return-value]

    video = project.video

    if video.status != "ready":
        raise ProjectConflictError(
            "The current project video has not finished processing yet."
        )

    if video.pending_mux_upload_id is not None:
        raise ProjectConflictError(
            "A replacement video is already uploading or processing."
        )

    if (
        video.cleanup_mux_upload_id is not None
        or video.cleanup_mux_asset_id is not None
    ):
        raise ProjectConflictError(
            "The previous video replacement still has cleanup pending."
        )

    video.pending_mux_upload_id = mux_upload_id
    video.pending_mux_asset_id = None
    video.pending_mux_playback_id = None
    video.pending_status = "uploading"
    video.pending_duration_seconds = None
    video.pending_aspect_ratio = None
    video.pending_original_filename = filename
    video.pending_error_message = None

    db.commit()
    return get_project(db, project.id)  # type: ignore[return-value]


def clear_project_video_cleanup_state(
    db: Session,
    *,
    project: Project,
) -> Project:
    if project.video is None:
        raise ProjectConflictError("This project does not have a video.")

    video = project.video
    video.cleanup_mux_upload_id = None
    video.cleanup_mux_asset_id = None
    video.cleanup_error_message = None

    db.commit()
    return get_project(db, project.id)  # type: ignore[return-value]


def clear_pending_project_video(
    db: Session,
    *,
    project: Project,
) -> Project:
    if project.video is None or project.video.pending_mux_upload_id is None:
        raise ProjectConflictError(
            "This project does not have a pending replacement video."
        )

    video = project.video
    video.pending_mux_upload_id = None
    video.pending_mux_asset_id = None
    video.pending_mux_playback_id = None
    video.pending_status = None
    video.pending_duration_seconds = None
    video.pending_aspect_ratio = None
    video.pending_original_filename = None
    video.pending_error_message = None

    db.commit()
    return get_project(db, project.id)  # type: ignore[return-value]
