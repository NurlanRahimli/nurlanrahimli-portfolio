from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContactContent(Base):
    __tablename__ = "contact_content"
    __table_args__ = (
        CheckConstraint(
            "id = 1",
            name="ck_contact_content_singleton_id",
        ),
        CheckConstraint(
            "projects_built >= 0",
            name="ck_contact_content_projects_built_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    projects_built: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    phone_number: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
