"""add education date range

Revision ID: 897c279aac63
Revises: c1f7f01af8e5
Create Date: 2026-09-18 21:27:39.964356
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "897c279aac63"
down_revision: Union[str, Sequence[str], None] = "c1f7f01af8e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "educations",
        "date",
        new_column_name="start_date",
        existing_type=sa.Date(),
        existing_nullable=False,
    )

    op.add_column(
        "educations",
        sa.Column(
            "end_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "educations",
        sa.Column(
            "is_current",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )

    op.alter_column(
        "educations",
        "is_current",
        server_default=sa.false(),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.drop_column(
        "educations",
        "is_current",
    )

    op.drop_column(
        "educations",
        "end_date",
    )

    op.alter_column(
        "educations",
        "start_date",
        new_column_name="date",
        existing_type=sa.Date(),
        existing_nullable=False,
    )
