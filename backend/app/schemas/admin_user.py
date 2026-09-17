from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
