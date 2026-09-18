from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class TestimonialWrite(BaseModel):
    person_name: str = Field(min_length=1, max_length=200)
    testimonial_text: str = Field(min_length=1)
    profile_media_asset_id: int | None = Field(
        default=None,
        gt=0,
    )
    linkedin_url: HttpUrl | None = None
    is_active: bool = True

    @field_validator(
        "person_name",
        "testimonial_text",
        mode="before",
    )
    @classmethod
    def strip_required_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator(
        "linkedin_url",
        mode="before",
    )
    @classmethod
    def empty_url_to_none(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class TestimonialCreate(TestimonialWrite):
    pass


class TestimonialUpdate(TestimonialWrite):
    pass


class TestimonialRead(BaseModel):
    id: int
    person_name: str
    testimonial_text: str
    profile_media_asset_id: int | None
    profile_image_url: str | None = None
    profile_thumbnail_url: str | None = None
    linkedin_url: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class TestimonialList(BaseModel):
    items: list[TestimonialRead]
    total: int
    limit: int
    offset: int


class TestimonialOrderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0)


class TestimonialReorder(BaseModel):
    items: list[TestimonialOrderItem] = Field(min_length=1)


class PublicTestimonialRead(BaseModel):
    person_name: str
    testimonial_text: str
    profile_image_url: str | None = None
    profile_thumbnail_url: str | None = None
    linkedin_url: str | None


class PublicTestimonialList(BaseModel):
    items: list[PublicTestimonialRead]
    total: int
