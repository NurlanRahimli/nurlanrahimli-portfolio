from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    slug: Mapped[str] = mapped_column(
        String(160),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    project_type: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    short_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    long_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    project_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    cover_media_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    github_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    show_github_link: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    demo_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        index=True,
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

    cover_media_asset: Mapped[MediaAsset | None] = relationship(
        foreign_keys=[cover_media_asset_id],
    )

    tags: Mapped[list[ProjectTag]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectTag.display_order",
    )
    images: Mapped[list[ProjectImage]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectImage.display_order",
    )
    features: Mapped[list[ProjectFeature]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectFeature.display_order",
    )
    tech_groups: Mapped[list[ProjectTechGroup]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectTechGroup.display_order",
    )
    video: Mapped[ProjectVideo | None] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class ProjectTag(Base):
    __tablename__ = "project_tags"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "label",
            name="uq_project_tags_project_label",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        back_populates="tags",
    )


class ProjectImage(Base):
    __tablename__ = "project_images"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "media_asset_id",
            name="uq_project_images_project_asset",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    media_asset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "media_assets.id",
            ondelete="RESTRICT",
        ),
        index=True,
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        back_populates="images",
    )
    media_asset: Mapped[MediaAsset] = relationship()


class ProjectFeature(Base):
    __tablename__ = "project_features"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        back_populates="features",
    )


class ProjectTechGroup(Base):
    __tablename__ = "project_tech_groups"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "label",
            name="uq_project_tech_groups_project_label",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        back_populates="tech_groups",
    )
    items: Mapped[list[ProjectTechItem]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectTechItem.display_order",
    )


class ProjectTechItem(Base):
    __tablename__ = "project_tech_items"
    __table_args__ = (
        UniqueConstraint(
            "tech_group_id",
            "name",
            name="uq_project_tech_items_group_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    tech_group_id: Mapped[int] = mapped_column(
        ForeignKey(
            "project_tech_groups.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    group: Mapped[ProjectTechGroup] = relationship(
        back_populates="items",
    )


class ProjectVideo(Base):
    __tablename__ = "project_videos"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    mux_upload_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    mux_asset_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    mux_playback_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default="uploading",
        server_default="uploading",
        index=True,
        nullable=False,
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    aspect_ratio: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    project: Mapped[Project] = relationship(
        back_populates="video",
    )


# Imported at the bottom to keep the type annotations readable while
# avoiding a circular runtime import between project and media models.
from app.models.media import MediaAsset  # noqa: E402
