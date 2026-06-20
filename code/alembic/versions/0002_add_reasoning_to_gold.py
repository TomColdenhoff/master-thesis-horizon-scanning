"""Add reasoning column to gold table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26
"""

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS reasoning TEXT")


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS reasoning")
