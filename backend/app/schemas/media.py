from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MediaVariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_name: str
    storage_key: str
    mime_type: str
    file_size: int
    width: int
    height: int
    created_at: datetime
    url: str | None = None


class MediaAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    storage_key: str
    mime_type: str
    file_type: str
    file_size: int
    width: int | None
    height: int | None
    alt_text: str | None
    created_at: datetime
    updated_at: datetime
    variants: list[MediaVariantRead] = Field(
        default_factory=list,
    )
    url: str | None = None


class MediaAssetList(BaseModel):
    items: list[MediaAssetRead]
    total: int
    limit: int
    offset: int


class MediaAssetUpdate(BaseModel):
    alt_text: str | None = Field(
        default=None,
        max_length=500,
    )
