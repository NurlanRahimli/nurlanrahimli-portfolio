"""add project video replacement state

Revision ID: 8e1c5a7d9b20
Revises: 6c7d93e82f41
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "8e1c5a7d9b20"
down_revision: str | None = "6c7d93e82f41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_mux_upload_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_mux_asset_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_mux_playback_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_status",
            sa.String(length=40),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_duration_seconds",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_aspect_ratio",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_original_filename",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "pending_error_message",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_unique_constraint(
        "uq_project_videos_pending_mux_upload_id",
        "project_videos",
        ["pending_mux_upload_id"],
    )
    op.create_unique_constraint(
        "uq_project_videos_pending_mux_asset_id",
        "project_videos",
        ["pending_mux_asset_id"],
    )
    op.create_unique_constraint(
        "uq_project_videos_pending_mux_playback_id",
        "project_videos",
        ["pending_mux_playback_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_videos_pending_mux_playback_id",
        "project_videos",
        type_="unique",
    )
    op.drop_constraint(
        "uq_project_videos_pending_mux_asset_id",
        "project_videos",
        type_="unique",
    )
    op.drop_constraint(
        "uq_project_videos_pending_mux_upload_id",
        "project_videos",
        type_="unique",
    )

    op.drop_column(
        "project_videos",
        "pending_error_message",
    )
    op.drop_column(
        "project_videos",
        "pending_original_filename",
    )
    op.drop_column(
        "project_videos",
        "pending_aspect_ratio",
    )
    op.drop_column(
        "project_videos",
        "pending_duration_seconds",
    )
    op.drop_column(
        "project_videos",
        "pending_status",
    )
    op.drop_column(
        "project_videos",
        "pending_mux_playback_id",
    )
    op.drop_column(
        "project_videos",
        "pending_mux_asset_id",
    )
    op.drop_column(
        "project_videos",
        "pending_mux_upload_id",
    )
