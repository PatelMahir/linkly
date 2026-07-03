"""initial schema: links + click_events

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("long_url", sa.String(length=2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_links_code", "links", ["code"], unique=True)

    op.create_table(
        "click_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.Column("referrer", sa.String(length=2048), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["link_id"], ["links.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_click_events_link_id", "click_events", ["link_id"])
    op.create_index("ix_click_events_created_at", "click_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_click_events_created_at", table_name="click_events")
    op.drop_index("ix_click_events_link_id", table_name="click_events")
    op.drop_table("click_events")
    op.drop_index("ix_links_code", table_name="links")
    op.drop_table("links")
