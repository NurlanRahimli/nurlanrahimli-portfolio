from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class EducationWrite(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    location: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    description: str | None = Field(default=None, max_length=5000)
    certification_media_asset_id: int | None = Field(default=None, gt=0)
    is_active: bool = True

    @field_validator("title", "location", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date.day != 1:
            raise ValueError(
                "Education start date must use the first day of the month."
            )

        if self.is_current:
            if self.end_date is not None:
                raise ValueError("A current education entry cannot have an end date.")
            return self

        if self.end_date is None:
            raise ValueError(
                "An end date is required when the education entry is not current."
            )

        if self.end_date.day != 1:
            raise ValueError("Education end date must use the first day of the month.")

        if self.end_date < self.start_date:
            raise ValueError("Education end date cannot be before the start date.")

        return self


class EducationCreate(EducationWrite):
    pass


class EducationUpdate(EducationWrite):
    pass


class EducationRead(BaseModel):
    id: int
    title: str
    location: str
    start_date: date
    end_date: date | None
    is_current: bool
    description: str | None
    certification_media_asset_id: int | None
    certification_filename: str | None = None
    certification_url: str | None = None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class EducationList(BaseModel):
    items: list[EducationRead]
    total: int
    limit: int
    offset: int


class EducationOrderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0)


class EducationReorder(BaseModel):
    items: list[EducationOrderItem] = Field(min_length=1)


class PublicEducationRead(BaseModel):
    title: str
    location: str
    start_date: date
    end_date: date | None
    is_current: bool
    description: str | None
    certification_filename: str | None = None
    certification_url: str | None = None


class PublicEducationList(BaseModel):
    items: list[PublicEducationRead]
    total: int
