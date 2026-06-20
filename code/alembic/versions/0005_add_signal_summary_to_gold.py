"""Add signal_summary column to gold for human-readable signal description.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-27
"""

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS signal_summary TEXT")


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS signal_summary")
