from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


AvailabilityMode = Literal["remote", "onsite", "hybrid"]


class AboutSoftwareFieldWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class AboutSocialLinkWrite(BaseModel):
    platform: str = Field(min_length=1, max_length=80)
    url: HttpUrl

    @field_validator("platform", mode="before")
    @classmethod
    def normalize_platform(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class AboutContentWrite(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    profile_media_asset_id: int | None = Field(default=None, gt=0)
    resume_media_asset_id: int | None = Field(default=None, gt=0)
    about_html: str = ""
    experience_years: int = Field(default=0, ge=0, le=100)
    location: str = Field(default="", max_length=255)
    is_available: bool = True
    availability_modes: list[AvailabilityMode] = Field(default_factory=list)
    software_fields: list[AboutSoftwareFieldWrite] = Field(
        min_length=1,
        max_length=4,
    )
    social_links: list[AboutSocialLinkWrite] = Field(default_factory=list)

    @field_validator("full_name", "location", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("availability_modes")
    @classmethod
    def unique_availability_modes(
        cls,
        value: list[AvailabilityMode],
    ) -> list[AvailabilityMode]:
        if len(value) != len(set(value)):
            raise ValueError("Availability modes must be unique.")
        return value

    @field_validator("software_fields")
    @classmethod
    def unique_software_fields(
        cls,
        value: list[AboutSoftwareFieldWrite],
    ) -> list[AboutSoftwareFieldWrite]:
        normalized = [item.name.casefold() for item in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Software fields must be unique.")
        return value

    @field_validator("social_links")
    @classmethod
    def unique_social_platforms(
        cls,
        value: list[AboutSocialLinkWrite],
    ) -> list[AboutSocialLinkWrite]:
        normalized = [item.platform.casefold() for item in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Social platforms must be unique.")
        return value

    @model_validator(mode="after")
    def validate_availability(self) -> "AboutContentWrite":
        if self.is_available and not self.availability_modes:
            raise ValueError(
                "Select at least one availability mode when availability is enabled."
            )
        return self


class AboutContentUpdate(AboutContentWrite):
    pass


class AboutSoftwareFieldRead(BaseModel):
    id: int
    name: str
    display_order: int


class AboutSocialLinkRead(BaseModel):
    id: int
    platform: str
    url: str
    display_order: int


class AboutContentRead(BaseModel):
    id: int
    full_name: str
    profile_media_asset_id: int | None
    profile_image_url: str | None = None
    profile_thumbnail_url: str | None = None
    resume_media_asset_id: int | None
    resume_url: str | None = None
    resume_filename: str | None = None
    about_html: str
    experience_years: int
    location: str
    is_available: bool
    availability_modes: list[AvailabilityMode]
    software_fields: list[AboutSoftwareFieldRead]
    social_links: list[AboutSocialLinkRead]
    created_at: datetime
    updated_at: datetime


class PublicAboutSoftwareField(BaseModel):
    name: str


class PublicAboutSocialLink(BaseModel):
    platform: str
    url: str


class PublicAboutContentRead(BaseModel):
    full_name: str
    profile_image_url: str | None = None
    profile_thumbnail_url: str | None = None
    resume_url: str | None = None
    about_html: str
    experience_years: int
    location: str
    is_available: bool
    availability_modes: list[AvailabilityMode]
    software_fields: list[PublicAboutSoftwareField]
    social_links: list[PublicAboutSocialLink]
