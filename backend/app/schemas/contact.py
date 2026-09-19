from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactContentWrite(BaseModel):
    projects_built: int = Field(default=0, ge=0)
    email: EmailStr
    phone_number: str = Field(min_length=1, max_length=80)

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ContactContentUpdate(ContactContentWrite):
    pass


class ContactContentRead(BaseModel):
    id: int
    projects_built: int
    email: str
    phone_number: str
    created_at: datetime
    updated_at: datetime


class PublicContactContentRead(BaseModel):
    projects_built: int
    email: str
    phone_number: str
