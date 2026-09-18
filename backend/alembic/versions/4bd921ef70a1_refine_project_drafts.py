"""refine project drafts

Revision ID: 4bd921ef70a1
Revises: 194a41abfc33
Create Date: 2026-09-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4bd921ef70a1"
down_revision: str | Sequence[str] | None = "194a41abfc33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "projects",
        "project_type",
        existing_type=sa.String(length=120),
        nullable=True,
    )
    op.alter_column(
        "projects",
        "short_description",
        existing_type=sa.String(length=500),
        nullable=True,
    )
    op.alter_column(
        "projects",
        "long_description",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.alter_column(
        "projects",
        "project_date",
        existing_type=sa.Date(),
        nullable=True,
    )
    op.alter_column(
        "projects",
        "show_github_link",
        existing_type=sa.Boolean(),
        server_default=sa.text("false"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE projects
        SET
            project_type = COALESCE(project_type, 'Project'),
            short_description = COALESCE(short_description, ''),
            long_description = COALESCE(long_description, ''),
            project_date = COALESCE(project_date, CURRENT_DATE)
        WHERE
            project_type IS NULL
            OR short_description IS NULL
            OR long_description IS NULL
            OR project_date IS NULL
        """
    )

    op.alter_column(
        "projects",
        "show_github_link",
        existing_type=sa.Boolean(),
        server_default=sa.text("true"),
        existing_nullable=False,
    )
    op.alter_column(
        "projects",
        "project_date",
        existing_type=sa.Date(),
        nullable=False,
    )
    op.alter_column(
        "projects",
        "long_description",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.alter_column(
        "projects",
        "short_description",
        existing_type=sa.String(length=500),
        nullable=False,
    )
    op.alter_column(
        "projects",
        "project_type",
        existing_type=sa.String(length=120),
        nullable=False,
    )
