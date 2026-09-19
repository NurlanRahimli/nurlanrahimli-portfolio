from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SkillWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    media_asset_id: int = Field(gt=0)
    is_active: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class SkillCreate(SkillWrite):
    pass


class SkillUpdate(SkillWrite):
    pass


class SkillRead(BaseModel):
    id: int
    name: str
    media_asset_id: int
    image_url: str | None = None
    thumbnail_url: str | None = None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class SkillList(BaseModel):
    items: list[SkillRead]
    total: int
    limit: int
    offset: int


class SkillOrderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0)


class SkillReorder(BaseModel):
    items: list[SkillOrderItem] = Field(min_length=1)


class PublicSkillRead(BaseModel):
    name: str
    image_url: str | None = None
    thumbnail_url: str | None = None


class PublicSkillList(BaseModel):
    items: list[PublicSkillRead]
    total: int
