"""refine project video lifecycle

Revision ID: 6c7d93e82f41
Revises: 4bd921ef70a1
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6c7d93e82f41"
down_revision: str | None = "4bd921ef70a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "project_videos",
        "duration_seconds",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
    )

    op.add_column(
        "project_videos",
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
    )

    op.alter_column(
        "project_videos",
        "status",
        existing_type=sa.String(length=40),
        server_default="uploading",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "project_videos",
        "status",
        existing_type=sa.String(length=40),
        server_default="waiting",
        existing_nullable=False,
    )

    op.drop_column(
        "project_videos",
        "error_message",
    )

    op.alter_column(
        "project_videos",
        "duration_seconds",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
