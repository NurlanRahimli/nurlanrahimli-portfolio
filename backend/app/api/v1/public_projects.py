from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.projects import media_urls, serialize_project
from app.db.deps import get_db
from app.models import Project
from app.schemas.project import (
    PublicProjectList,
    PublicProjectListItem,
    PublicProjectNavigation,
    PublicProjectRead,
)
from app.services.projects import (
    get_published_project_by_slug,
    get_published_project_neighbors,
    list_published_projects,
)

router = APIRouter(
    prefix="/public/projects",
    tags=["public-projects"],
)


def visible_github_url(
    project: Project,
) -> str | None:
    if not project.show_github_link:
        return None
    return project.github_url


def serialize_public_list_item(
    project: Project,
) -> PublicProjectListItem:
    full = serialize_project(project)
    cover_url, cover_thumbnail_url = media_urls(
        project.cover_media_asset
    )

    return PublicProjectListItem(
        slug=project.slug,
        title=project.title,
        project_type=project.project_type,
        short_description=project.short_description,
        project_date=project.project_date,
        cover_url=cover_url,
        cover_thumbnail_url=cover_thumbnail_url,
        github_url=visible_github_url(project),
        demo_url=project.demo_url,
        is_featured=project.is_featured,
        display_order=project.display_order,
        tags=full.tags,
        technologies=[
            item.name
            for group in project.tech_groups
            for item in group.items
        ],
    )


def navigation_item(
    project: Project | None,
) -> PublicProjectNavigation | None:
    if project is None:
        return None

    return PublicProjectNavigation(
        slug=project.slug,
        title=project.title,
    )


@router.get(
    "",
    response_model=PublicProjectList,
)
def get_public_projects(
    db: Annotated[Session, Depends(get_db)],
    search: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
) -> PublicProjectList:
    projects = list(list_published_projects(db))

    if search:
        normalized = search.strip().casefold()

        projects = [
            project
            for project in projects
            if normalized in project.title.casefold()
            or normalized in project.project_type.casefold()
            or normalized in project.short_description.casefold()
            or any(
                normalized in tag.label.casefold()
                for tag in project.tags
            )
            or any(
                normalized in item.name.casefold()
                for group in project.tech_groups
                for item in group.items
            )
        ]

    return PublicProjectList(
        items=[
            serialize_public_list_item(project)
            for project in projects
        ],
        total=len(projects),
    )


@router.get(
    "/{slug}",
    response_model=PublicProjectRead,
)
def get_public_project(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
) -> PublicProjectRead:
    project = get_published_project_by_slug(
        db,
        slug,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    full = serialize_project(project)
    previous_project, next_project = (
        get_published_project_neighbors(
            db,
            project,
        )
    )

    return PublicProjectRead(
        slug=project.slug,
        title=project.title,
        project_type=project.project_type,
        short_description=project.short_description,
        long_description=project.long_description,
        project_date=project.project_date,
        cover_url=full.cover_url,
        cover_thumbnail_url=full.cover_thumbnail_url,
        github_url=visible_github_url(project),
        demo_url=project.demo_url,
        is_featured=project.is_featured,
        display_order=project.display_order,
        tags=full.tags,
        images=full.images,
        features=full.features,
        tech_groups=full.tech_groups,
        video=full.video,
        previous_project=navigation_item(
            previous_project
        ),
        next_project=navigation_item(
            next_project
        ),
    )
