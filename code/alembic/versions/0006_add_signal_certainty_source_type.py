"""Add signal_certainty and source_type columns to gold.

signal_certainty: committed | proposed | advisory | existing
source_type:      statutory | sector_code | case_law | policy_intent

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-28
"""

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS signal_certainty TEXT")
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS source_type TEXT")


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS signal_certainty")
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS source_type")
