"""Add duration_ms to classifier_log, gold, and synthesis for benchmark timing.

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-17
"""

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE classifier_log ADD COLUMN IF NOT EXISTS duration_ms INTEGER")
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS duration_ms INTEGER")
    op.execute("ALTER TABLE synthesis ADD COLUMN IF NOT EXISTS duration_ms INTEGER")


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE classifier_log DROP COLUMN IF EXISTS duration_ms")
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS duration_ms")
    op.execute("ALTER TABLE synthesis DROP COLUMN IF EXISTS duration_ms")
