from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.v1.media import serialize_media_asset
from app.db.deps import get_db
from app.models import AdminUser, MediaAsset, Project, ProjectVideo
from app.schemas.project import (
    ProjectCreate,
    ProjectImageRead,
    ProjectList,
    ProjectListItem,
    ProjectRead,
    ProjectReorder,
    ProjectTagRead,
    ProjectTechGroupRead,
    ProjectTechItemRead,
    ProjectUpdate,
    ProjectVideoUploadCreate,
    ProjectVideoUploadResponse,
)
from app.services.mux_video import (
    MuxAPIError,
    MuxConfigurationError,
    cleanup_project_video,
    create_direct_upload,
)
from app.services.projects import (
    ProjectConflictError,
    ProjectMediaError,
    clear_pending_project_video,
    clear_project_video_cleanup_state,
    create_project,
    create_project_video_upload,
    delete_project,
    get_project,
    list_projects,
    remove_project_video,
    reorder_projects,
    update_project,
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


def media_urls(
    asset: MediaAsset | None,
) -> tuple[str | None, str | None]:
    if asset is None:
        return None, None

    serialized = serialize_media_asset(asset)

    thumbnail = next(
        (
            variant.url
            for variant in serialized.variants
            if variant.variant_name == "thumbnail"
        ),
        serialized.url,
    )

    return serialized.url, thumbnail


def serialize_project(project: Project) -> ProjectRead:
    cover_url, cover_thumbnail_url = media_urls(project.cover_media_asset)

    images: list[ProjectImageRead] = []
    for image in project.images:
        image_url, thumbnail_url = media_urls(image.media_asset)
        images.append(
            ProjectImageRead(
                id=image.id,
                media_asset_id=image.media_asset_id,
                label=image.label,
                display_order=image.display_order,
                media_url=image_url,
                thumbnail_url=thumbnail_url,
                alt_text=image.media_asset.alt_text,
            )
        )

    tech_groups = [
        ProjectTechGroupRead(
            id=group.id,
            label=group.label,
            display_order=group.display_order,
            items=[ProjectTechItemRead.model_validate(item) for item in group.items],
        )
        for group in project.tech_groups
    ]

    return ProjectRead(
        id=project.id,
        slug=project.slug,
        title=project.title,
        project_type=project.project_type,
        short_description=project.short_description,
        long_description=project.long_description,
        project_date=project.project_date,
        cover_media_asset_id=project.cover_media_asset_id,
        cover_url=cover_url,
        cover_thumbnail_url=cover_thumbnail_url,
        github_url=project.github_url,
        show_github_link=project.show_github_link,
        demo_url=project.demo_url,
        is_featured=project.is_featured,
        is_published=project.is_published,
        display_order=project.display_order,
        tags=[ProjectTagRead.model_validate(tag) for tag in project.tags],
        images=images,
        features=project.features,
        tech_groups=tech_groups,
        video=project.video,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def serialize_project_list_item(
    project: Project,
) -> ProjectListItem:
    cover_url, cover_thumbnail_url = media_urls(project.cover_media_asset)

    technologies = [item.name for group in project.tech_groups for item in group.items]

    full = serialize_project(project)

    return ProjectListItem(
        id=project.id,
        slug=project.slug,
        title=project.title,
        project_type=project.project_type,
        short_description=project.short_description,
        project_date=project.project_date,
        cover_media_asset_id=project.cover_media_asset_id,
        cover_url=cover_url,
        cover_thumbnail_url=cover_thumbnail_url,
        github_url=project.github_url,
        show_github_link=project.show_github_link,
        demo_url=project.demo_url,
        is_featured=project.is_featured,
        is_published=project.is_published,
        display_order=project.display_order,
        tags=full.tags,
        technologies=technologies,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def project_error(exc: ValueError) -> HTTPException:
    if isinstance(exc, ProjectMediaError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    )


@router.get(
    "",
    response_model=ProjectList,
)
def get_projects(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
    search: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
    is_published: Annotated[
        bool | None,
        Query(),
    ] = None,
    is_featured: Annotated[
        bool | None,
        Query(),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
) -> ProjectList:
    del current_admin

    projects, total = list_projects(
        db,
        search=search,
        is_published=is_published,
        is_featured=is_featured,
        limit=limit,
        offset=offset,
    )

    return ProjectList(
        items=[serialize_project_list_item(project) for project in projects],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
)
def get_project_by_id(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> ProjectRead:
    del current_admin

    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return serialize_project(project)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def post_project(
    payload: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> ProjectRead:
    del current_admin

    try:
        project = create_project(
            db,
            payload=payload,
        )
    except (ProjectConflictError, ProjectMediaError) as exc:
        raise project_error(exc) from exc

    return serialize_project(project)


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
)
def put_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> ProjectRead:
    del current_admin

    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    try:
        project = update_project(
            db,
            project=project,
            payload=payload,
        )
    except (ProjectConflictError, ProjectMediaError) as exc:
        raise project_error(exc) from exc

    return serialize_project(project)


@router.put(
    "/reorder/all",
    status_code=status.HTTP_204_NO_CONTENT,
)
def put_project_order(
    payload: ProjectReorder,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    try:
        reorder_projects(
            db,
            ordered_items=[(item.id, item.display_order) for item in payload.items],
        )
    except ProjectConflictError as exc:
        raise project_error(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def cleanup_project_video_resources(
    db: Session,
    project: Project,
    *,
    include_active: bool = True,
    include_pending: bool = True,
    include_cleanup: bool = True,
) -> None:
    """Clean Mux resources and durably clear each completed resource slot."""

    video = project.video
    if video is None:
        return

    # Pending is first because it is never publicly active.
    if include_pending and video.pending_mux_upload_id is not None:
        cleanup_project_video(
            upload_id=video.pending_mux_upload_id,
            asset_id=video.pending_mux_asset_id,
        )
        clear_pending_project_video(
            db,
            project=project,
        )
        video = project.video
        if video is None:
            return

    # A previously replaced resource is already detached from public playback.
    if include_cleanup and (
        video.cleanup_mux_upload_id is not None
        or video.cleanup_mux_asset_id is not None
    ):
        cleanup_project_video(
            upload_id=video.cleanup_mux_upload_id,
            asset_id=video.cleanup_mux_asset_id,
        )
        clear_project_video_cleanup_state(
            db,
            project=project,
        )
        video = project.video
        if video is None:
            return

    # The active video is deliberately last. Its row is removed immediately
    # after this helper succeeds when deleting the video/project.
    if include_active:
        cleanup_project_video(
            upload_id=video.mux_upload_id,
            asset_id=video.mux_asset_id,
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.video is not None:
        try:
            cleanup_project_video_resources(
                db,
                project,
                include_active=True,
                include_pending=True,
                include_cleanup=True,
            )
        except MuxConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except MuxAPIError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    delete_project(
        db,
        project=project,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{project_id}/video",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_video(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    project = get_project(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.video is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This project does not have a video.",
        )

    try:
        cleanup_project_video_resources(
            db,
            project,
            include_active=True,
            include_pending=True,
            include_cleanup=True,
        )
    except MuxConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except MuxAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    try:
        remove_project_video(
            db,
            project=project,
        )
    except ProjectConflictError as exc:
        raise project_error(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{project_id}/video/replacement",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_video_replacement(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    project = get_project(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.video is None or project.video.pending_mux_upload_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This project does not have a pending replacement video.",
        )

    try:
        cleanup_project_video_resources(
            db,
            project,
            include_active=False,
            include_pending=True,
            include_cleanup=False,
        )
    except MuxConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except MuxAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/video/cleanup/retry",
    status_code=status.HTTP_204_NO_CONTENT,
)
def retry_video_cleanup(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    project = get_project(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.video is None or (
        project.video.cleanup_mux_upload_id is None
        and project.video.cleanup_mux_asset_id is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This project does not have video cleanup pending.",
        )

    video = project.video

    try:
        cleanup_project_video(
            upload_id=video.cleanup_mux_upload_id,
            asset_id=video.cleanup_mux_asset_id,
        )
    except MuxConfigurationError as exc:
        video.cleanup_error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except MuxAPIError as exc:
        video.cleanup_error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    clear_project_video_cleanup_state(
        db,
        project=project,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/video/upload",
    response_model=ProjectVideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_video_upload(
    project_id: int,
    payload: ProjectVideoUploadCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> ProjectVideoUploadResponse:
    del current_admin

    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.video is not None:
        if project.video.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("The current project video has not finished processing yet."),
            )

        if project.video.pending_mux_upload_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("A replacement video is already uploading or processing."),
            )

        if (
            project.video.cleanup_mux_upload_id is not None
            or project.video.cleanup_mux_asset_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("The previous video replacement still has cleanup pending."),
            )

    try:
        upload = create_direct_upload(
            project_id=project.id,
        )
    except MuxConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except MuxAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    try:
        create_project_video_upload(
            db,
            project=project,
            original_filename=payload.original_filename,
            mux_upload_id=upload.upload_id,
        )
    except ProjectConflictError as exc:
        raise project_error(exc) from exc

    return ProjectVideoUploadResponse(
        project_id=project.id,
        upload_id=upload.upload_id,
        upload_url=upload.upload_url,
        status="uploading",
    )
