from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.deps import get_db
from app.models.admin_user import AdminUser
from app.schemas.media import (
    MediaAssetList,
    MediaAssetRead,
    MediaAssetUpdate,
    MediaVariantRead,
)
from app.services.media_library import (
    MediaAssetInUseError,
    create_media_asset,
    delete_media_asset,
    get_media_asset,
    list_media_assets,
    update_media_asset,
)
from app.services.r2_storage import R2ConfigurationError, r2_storage

router = APIRouter(
    prefix="/media",
    tags=["media"],
)


def serialize_media_asset(asset) -> MediaAssetRead:
    try:
        asset_url = r2_storage.public_url(asset.storage_key)
    except R2ConfigurationError:
        asset_url = None

    variants: list[MediaVariantRead] = []

    for variant in asset.variants:
        try:
            variant_url = r2_storage.public_url(variant.storage_key)
        except R2ConfigurationError:
            variant_url = None

        variants.append(
            MediaVariantRead(
                id=variant.id,
                variant_name=variant.variant_name,
                storage_key=variant.storage_key,
                mime_type=variant.mime_type,
                file_size=variant.file_size,
                width=variant.width,
                height=variant.height,
                created_at=variant.created_at,
                url=variant_url,
            )
        )

    return MediaAssetRead(
        id=asset.id,
        filename=asset.filename,
        original_filename=asset.original_filename,
        storage_key=asset.storage_key,
        mime_type=asset.mime_type,
        file_type=asset.file_type,
        file_size=asset.file_size,
        width=asset.width,
        height=asset.height,
        alt_text=asset.alt_text,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        variants=variants,
        url=asset_url,
    )


@router.post(
    "",
    response_model=MediaAssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
    alt_text: Annotated[
        str | None,
        Form(max_length=500),
    ] = None,
) -> MediaAssetRead:
    del current_admin

    content = await file.read()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A filename is required.",
        )

    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A content type is required.",
        )

    try:
        asset = create_media_asset(
            db,
            content=content,
            original_filename=file.filename,
            mime_type=file.content_type,
            alt_text=alt_text,
        )
    except R2ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media storage is not configured.",
        ) from exc

    return serialize_media_asset(asset)


@router.get(
    "",
    response_model=MediaAssetList,
)
def get_media_assets(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
    search: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
    file_type: Annotated[
        Literal["image", "document"] | None,
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
) -> MediaAssetList:
    del current_admin

    assets, total = list_media_assets(
        db,
        search=search,
        file_type=file_type,
        limit=limit,
        offset=offset,
    )

    return MediaAssetList(
        items=[serialize_media_asset(asset) for asset in assets],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{asset_id}",
    response_model=MediaAssetRead,
)
def get_media_asset_by_id(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> MediaAssetRead:
    del current_admin

    asset = get_media_asset(db, asset_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found.",
        )

    return serialize_media_asset(asset)


@router.patch(
    "/{asset_id}",
    response_model=MediaAssetRead,
)
def patch_media_asset(
    asset_id: int,
    payload: MediaAssetUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> MediaAssetRead:
    del current_admin

    asset = get_media_asset(db, asset_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found.",
        )

    asset = update_media_asset(
        db,
        asset=asset,
        alt_text=payload.alt_text,
    )

    return serialize_media_asset(asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_media_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> Response:
    del current_admin

    asset = get_media_asset(db, asset_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found.",
        )

    try:
        delete_media_asset(
            db,
            asset=asset,
        )
    except MediaAssetInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except R2ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media storage is not configured.",
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
