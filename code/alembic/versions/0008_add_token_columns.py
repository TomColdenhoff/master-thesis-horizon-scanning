"""Add input_tokens and output_tokens columns to gold and synthesis tables.

Allows per-record cost tracking. Values are populated from the API response
usage object on every LLM call.

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-07
"""

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS input_tokens INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE gold ADD COLUMN IF NOT EXISTS output_tokens INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE synthesis ADD COLUMN IF NOT EXISTS input_tokens INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE synthesis ADD COLUMN IF NOT EXISTS output_tokens INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS input_tokens")
    op.execute("ALTER TABLE gold DROP COLUMN IF EXISTS output_tokens")
    op.execute("ALTER TABLE synthesis DROP COLUMN IF EXISTS input_tokens")
    op.execute("ALTER TABLE synthesis DROP COLUMN IF EXISTS output_tokens")
