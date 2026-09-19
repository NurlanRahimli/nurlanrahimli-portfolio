from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator, field_validator


class ExperienceHighlightWrite(BaseModel):
    text: str = Field(min_length=1, max_length=1000)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ExperienceHighlightRead(BaseModel):
    id: int
    text: str
    display_order: int


class ExperienceWrite(BaseModel):
    job_title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    is_active: bool = True
    highlights: list[ExperienceHighlightWrite] = Field(default_factory=list)

    @field_validator("job_title", "company", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date.day != 1:
            raise ValueError("Start date must use the first day of the month.")

        if self.is_current:
            if self.end_date is not None:
                raise ValueError(
                    "A current experience cannot have an end date."
                )
            return self

        if self.end_date is None:
            raise ValueError(
                "An end date is required when the experience is not current."
            )

        if self.end_date.day != 1:
            raise ValueError("End date must use the first day of the month.")

        if self.end_date < self.start_date:
            raise ValueError(
                "End date cannot be before the start date."
            )

        return self


class ExperienceCreate(ExperienceWrite):
    pass


class ExperienceUpdate(ExperienceWrite):
    pass


class ExperienceRead(BaseModel):
    id: int
    job_title: str
    company: str
    location: str | None
    start_date: date
    end_date: date | None
    is_current: bool
    is_active: bool
    display_order: int
    highlights: list[ExperienceHighlightRead]
    created_at: datetime
    updated_at: datetime


class ExperienceList(BaseModel):
    items: list[ExperienceRead]
    total: int
    limit: int
    offset: int


class ExperienceOrderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0)


class ExperienceReorder(BaseModel):
    items: list[ExperienceOrderItem] = Field(min_length=1)


class PublicExperienceHighlightRead(BaseModel):
    text: str


class PublicExperienceRead(BaseModel):
    job_title: str
    company: str
    location: str | None
    start_date: date
    end_date: date | None
    is_current: bool
    highlights: list[PublicExperienceHighlightRead]


class PublicExperienceList(BaseModel):
    items: list[PublicExperienceRead]
    total: int
