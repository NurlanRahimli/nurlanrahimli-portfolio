"""add project video cleanup state

Revision ID: 9f4c2d7a1e63
Revises: 8e1c5a7d9b20
Create Date: 2026-09-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9f4c2d7a1e63"
down_revision: str | None = "8e1c5a7d9b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project_videos",
        sa.Column(
            "cleanup_mux_upload_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "cleanup_mux_asset_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "project_videos",
        sa.Column(
            "cleanup_error_message",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "project_videos",
        "cleanup_error_message",
    )
    op.drop_column(
        "project_videos",
        "cleanup_mux_asset_id",
    )
    op.drop_column(
        "project_videos",
        "cleanup_mux_upload_id",
    )
