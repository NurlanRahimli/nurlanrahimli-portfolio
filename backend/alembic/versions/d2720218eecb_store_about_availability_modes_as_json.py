"""store about availability modes as json

Revision ID: d2720218eecb
Revises: bc595f19f066
Create Date: 2026-09-18 16:54:41.837102
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d2720218eecb"
down_revision: Union[str, Sequence[str], None] = "bc595f19f066"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE about_content
        ALTER COLUMN availability_modes DROP DEFAULT
        """
    )

    op.alter_column(
        "about_content",
        "availability_modes",
        existing_type=postgresql.ARRAY(sa.String(length=20)),
        type_=sa.JSON(),
        existing_nullable=False,
        postgresql_using="to_json(availability_modes)",
    )

    op.alter_column(
        "about_content",
        "availability_modes",
        existing_type=sa.JSON(),
        server_default=sa.text("'[]'::json"),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_about_content_singleton_id",
        "about_content",
        "id = 1",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_about_content_singleton_id",
        "about_content",
        type_="check",
    )

    op.execute(
        """
        ALTER TABLE about_content
        ALTER COLUMN availability_modes DROP DEFAULT
        """
    )

    op.alter_column(
        "about_content",
        "availability_modes",
        existing_type=sa.JSON(),
        type_=postgresql.ARRAY(sa.String(length=20)),
        existing_nullable=False,
        postgresql_using=(
            "ARRAY("
            "SELECT json_array_elements_text(availability_modes)"
            ")"
        ),
    )

    op.alter_column(
        "about_content",
        "availability_modes",
        existing_type=postgresql.ARRAY(sa.String(length=20)),
        server_default=sa.text("'{}'::character varying[]"),
        existing_nullable=False,
    )
