import re
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.media import MediaAsset, MediaVariant
from app.models.project import Project, ProjectImage
from app.services.image_processing import create_image_variants
from app.services.media_validation import ValidatedMedia, validate_media
from app.services.r2_storage import R2Storage, r2_storage


def sanitize_filename(filename: str) -> str:
    original = Path(filename).name.strip()
    stem = Path(original).stem
    suffix = Path(original).suffix.lower()

    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem)
    safe_stem = safe_stem.strip("-_").lower()

    if not safe_stem:
        safe_stem = "file"

    return f"{safe_stem}{suffix}"


def build_storage_key(
    *,
    file_type: str,
    filename: str,
) -> str:
    identifier = uuid4().hex
    folder = "images" if file_type == "image" else "documents"

    return f"media/{folder}/{identifier}/{filename}"


def build_variant_key(
    *,
    original_key: str,
    variant_name: str,
) -> str:
    path = Path(original_key)

    return str(path.parent / "variants" / f"{path.stem}-{variant_name}.webp")


def get_media_asset(
    db: Session,
    asset_id: int,
) -> MediaAsset | None:
    statement = (
        select(MediaAsset)
        .options(selectinload(MediaAsset.variants))
        .where(MediaAsset.id == asset_id)
    )

    return db.scalar(statement)


def list_media_assets(
    db: Session,
    *,
    search: str | None = None,
    file_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[MediaAsset], int]:
    filters = []

    if search:
        normalized = search.strip()

        if normalized:
            pattern = f"%{normalized}%"
            filters.append(
                or_(
                    MediaAsset.filename.ilike(pattern),
                    MediaAsset.original_filename.ilike(pattern),
                    MediaAsset.alt_text.ilike(pattern),
                )
            )

    if file_type:
        filters.append(MediaAsset.file_type == file_type)

    count_statement = select(func.count(MediaAsset.id))

    if filters:
        count_statement = count_statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        select(MediaAsset)
        .options(selectinload(MediaAsset.variants))
        .order_by(MediaAsset.created_at.desc(), MediaAsset.id.desc())
        .limit(limit)
        .offset(offset)
    )

    if filters:
        statement = statement.where(*filters)

    assets = list(db.scalars(statement).unique().all())

    return assets, total


def create_media_asset(
    db: Session,
    *,
    content: bytes,
    original_filename: str,
    mime_type: str,
    alt_text: str | None = None,
    storage: R2Storage = r2_storage,
) -> MediaAsset:
    validated = validate_media(
        content,
        mime_type,
    )

    filename = sanitize_filename(original_filename)

    original_key = build_storage_key(
        file_type=validated.file_type,
        filename=filename,
    )

    uploaded_keys: list[str] = []

    try:
        storage.upload(
            key=original_key,
            content=content,
            content_type=validated.mime_type,
        )
        uploaded_keys.append(original_key)

        asset = _build_asset(
            validated=validated,
            filename=filename,
            original_filename=original_filename,
            storage_key=original_key,
            alt_text=alt_text,
        )

        if validated.file_type == "image":
            for variant in create_image_variants(content):
                variant_key = build_variant_key(
                    original_key=original_key,
                    variant_name=variant.name,
                )

                storage.upload(
                    key=variant_key,
                    content=variant.content,
                    content_type=variant.mime_type,
                )
                uploaded_keys.append(variant_key)

                asset.variants.append(
                    MediaVariant(
                        variant_name=variant.name,
                        storage_key=variant_key,
                        mime_type=variant.mime_type,
                        file_size=len(variant.content),
                        width=variant.width,
                        height=variant.height,
                    )
                )

        db.add(asset)
        db.commit()
        db.refresh(asset)

        return get_media_asset(db, asset.id) or asset

    except Exception:
        db.rollback()

        for key in reversed(uploaded_keys):
            try:
                storage.delete(key)
            except Exception:
                pass

        raise


def _build_asset(
    *,
    validated: ValidatedMedia,
    filename: str,
    original_filename: str,
    storage_key: str,
    alt_text: str | None,
) -> MediaAsset:
    normalized_alt_text = (
        alt_text.strip() if alt_text is not None and alt_text.strip() else None
    )

    return MediaAsset(
        filename=filename,
        original_filename=original_filename,
        storage_key=storage_key,
        mime_type=validated.mime_type,
        file_type=validated.file_type,
        file_size=validated.file_size,
        width=validated.width,
        height=validated.height,
        alt_text=normalized_alt_text,
    )


def update_media_asset(
    db: Session,
    *,
    asset: MediaAsset,
    alt_text: str | None,
) -> MediaAsset:
    asset.alt_text = (
        alt_text.strip() if alt_text is not None and alt_text.strip() else None
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return get_media_asset(db, asset.id) or asset


class MediaAssetInUseError(Exception):
    """Raised when a media asset is still referenced by application content."""

    def __init__(self, usages: list[str]) -> None:
        self.usages = usages
        if len(usages) == 1:
            detail = f"This media asset is currently used as {usages[0]}."
        else:
            detail = (
                "This media asset is currently in use: "
                + ", ".join(usages)
                + "."
            )
        super().__init__(detail)


def get_media_asset_usages(
    db: Session,
    *,
    asset_id: int,
) -> list[str]:
    """Return human-readable locations that currently reference an asset."""

    usages: list[str] = []

    cover_project = db.scalar(
        select(Project.id)
        .where(Project.cover_media_asset_id == asset_id)
        .limit(1)
    )
    if cover_project is not None:
        usages.append("a project cover image")

    gallery_project = db.scalar(
        select(ProjectImage.id)
        .where(ProjectImage.media_asset_id == asset_id)
        .limit(1)
    )
    if gallery_project is not None:
        usages.append("a project gallery image")

    return usages


def delete_media_asset(
    db: Session,
    *,
    asset: MediaAsset,
    storage: R2Storage = r2_storage,
) -> None:
    usages = get_media_asset_usages(
        db,
        asset_id=asset.id,
    )
    if usages:
        raise MediaAssetInUseError(usages)

    keys = [variant.storage_key for variant in asset.variants]
    keys.append(asset.storage_key)

    for key in keys:
        storage.delete(key)

    db.delete(asset)
    db.commit()
