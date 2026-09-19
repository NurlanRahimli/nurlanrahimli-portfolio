from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AboutContent(Base):
    __tablename__ = "about_content"
    __table_args__ = (
        CheckConstraint(
            "experience_years >= 0",
            name="ck_about_content_experience_years_nonnegative",
        ),
        CheckConstraint(
            "id = 1",
            name="ck_about_content_singleton_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    profile_media_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    resume_media_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    about_html: Mapped[str] = mapped_column(
        Text,
        default="",
        server_default="",
        nullable=False,
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default="",
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    availability_modes: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
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

    profile_media_asset: Mapped[MediaAsset | None] = relationship(
        foreign_keys=[profile_media_asset_id],
    )

    resume_media_asset: Mapped[MediaAsset | None] = relationship(
        foreign_keys=[resume_media_asset_id],
    )

    software_fields: Mapped[list[AboutSoftwareField]] = relationship(
        back_populates="about_content",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AboutSoftwareField.display_order",
    )

    social_links: Mapped[list[AboutSocialLink]] = relationship(
        back_populates="about_content",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AboutSocialLink.display_order",
    )


class AboutSoftwareField(Base):
    __tablename__ = "about_software_fields"
    __table_args__ = (
        UniqueConstraint(
            "about_content_id",
            "display_order",
            name="uq_about_software_fields_content_order",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    about_content_id: Mapped[int] = mapped_column(
        ForeignKey(
            "about_content.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    about_content: Mapped[AboutContent] = relationship(
        back_populates="software_fields",
    )


class AboutSocialLink(Base):
    __tablename__ = "about_social_links"
    __table_args__ = (
        UniqueConstraint(
            "about_content_id",
            "display_order",
            name="uq_about_social_links_content_order",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    about_content_id: Mapped[int] = mapped_column(
        ForeignKey(
            "about_content.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    about_content: Mapped[AboutContent] = relationship(
        back_populates="social_links",
    )


from app.models.media import MediaAsset  # noqa: E402
