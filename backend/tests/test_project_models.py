from datetime import date

from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    MediaAsset,
    Project,
    ProjectFeature,
    ProjectImage,
    ProjectTag,
    ProjectTechGroup,
    ProjectTechItem,
    ProjectVideo,
)


def make_engine():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record,
    ) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def make_asset(
    *,
    filename: str = "project.png",
) -> MediaAsset:
    return MediaAsset(
        filename=filename,
        original_filename=filename,
        storage_key=f"media/images/{filename}",
        mime_type="image/png",
        file_type="image",
        file_size=1024,
        width=1600,
        height=900,
    )


def make_project(
    *,
    slug: str = "bookaify",
) -> Project:
    return Project(
        slug=slug,
        title="Bookaify",
        project_type="Web Application",
        short_description="AI-powered bookkeeping platform.",
        long_description=(
            "Bookaify turns financial data into useful insights.\n\n"
            "It combines AI workflows with a production backend."
        ),
        project_date=date(2026, 6, 1),
    )


def test_project_persists_with_defaults() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        project = make_project()
        session.add(project)
        session.commit()

        stored = session.scalar(select(Project).where(Project.slug == "bookaify"))

        assert stored is not None
        assert stored.title == "Bookaify"
        assert stored.project_type == "Web Application"
        assert stored.project_date == date(2026, 6, 1)
        assert stored.is_published is False
        assert stored.is_featured is False
        assert stored.show_github_link is False
        assert stored.display_order == 0


def test_project_owns_ordered_content() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        project = make_project()

        project.tags.extend(
            [
                ProjectTag(label="Full-Stack", display_order=1),
                ProjectTag(label="AI", display_order=0),
            ]
        )
        project.features.extend(
            [
                ProjectFeature(
                    text="Receipt OCR",
                    display_order=1,
                ),
                ProjectFeature(
                    text="Conversational analytics",
                    display_order=0,
                ),
            ]
        )

        backend = ProjectTechGroup(
            label="Backend",
            display_order=1,
        )
        backend.items.extend(
            [
                ProjectTechItem(
                    name="PostgreSQL",
                    display_order=1,
                ),
                ProjectTechItem(
                    name="FastAPI",
                    display_order=0,
                ),
            ]
        )

        frontend = ProjectTechGroup(
            label="Frontend",
            display_order=0,
        )
        frontend.items.append(
            ProjectTechItem(
                name="React",
                display_order=0,
            )
        )

        project.tech_groups.extend([backend, frontend])

        session.add(project)
        session.commit()
        session.expire_all()

        stored = session.scalar(select(Project).where(Project.slug == "bookaify"))

        assert stored is not None
        assert [tag.label for tag in stored.tags] == [
            "AI",
            "Full-Stack",
        ]
        assert [feature.text for feature in stored.features] == [
            "Conversational analytics",
            "Receipt OCR",
        ]
        assert [group.label for group in stored.tech_groups] == [
            "Frontend",
            "Backend",
        ]
        assert [item.name for item in stored.tech_groups[1].items] == [
            "FastAPI",
            "PostgreSQL",
        ]


def test_project_images_reference_media_without_owning_it() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        cover = make_asset(filename="cover.png")
        screenshot = make_asset(filename="dashboard.png")

        project = make_project()
        project.cover_media_asset = cover
        project.images.append(
            ProjectImage(
                media_asset=screenshot,
                label="Dashboard",
                display_order=0,
            )
        )

        session.add(project)
        session.commit()

        cover_id = cover.id
        screenshot_id = screenshot.id
        project_id = project.id

        session.delete(project)
        session.commit()

        assert session.get(Project, project_id) is None
        assert session.get(MediaAsset, cover_id) is not None
        assert session.get(MediaAsset, screenshot_id) is not None
        assert session.scalar(select(ProjectImage)) is None


def test_project_video_is_one_to_one() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        project = make_project()
        project.video = ProjectVideo(
            mux_upload_id="upload-123",
            mux_asset_id="asset-123",
            mux_playback_id="playback-123",
            status="ready",
            duration_seconds=134,
            aspect_ratio="16:9",
            original_filename="bookaify-demo.mp4",
        )

        session.add(project)
        session.commit()

        stored = session.scalar(select(Project).where(Project.slug == "bookaify"))

        assert stored is not None
        assert stored.video is not None
        assert stored.video.status == "ready"
        assert stored.video.mux_playback_id == "playback-123"


def test_project_slug_must_be_unique() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(make_project(slug="bookaify"))
        session.commit()

        session.add(make_project(slug="bookaify"))

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("Duplicate project slug was accepted.")


def test_duplicate_project_image_is_rejected() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        asset = make_asset()
        project = make_project()

        project.images.extend(
            [
                ProjectImage(
                    media_asset=asset,
                    display_order=0,
                ),
                ProjectImage(
                    media_asset=asset,
                    display_order=1,
                ),
            ]
        )

        session.add(project)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("Duplicate project/media relationship was accepted.")
